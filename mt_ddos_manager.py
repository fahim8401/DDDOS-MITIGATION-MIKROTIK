#!/usr/bin/env python3
"""
MikroTik Multi-Router DDoS Manager
A modular application for monitoring and mitigating DDoS attacks across multiple MikroTik routers.
"""

import os
import sys
import time
import logging
import yaml
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import librouteros
    from librouteros import connect
    from librouteros.exceptions import TrapError, FatalError, ConnectionClosed
except ImportError:
    print("Error: librouteros is required. Install with: pip install librouteros")
    sys.exit(1)

from models import get_database, Router, Event, BlockedIP, RouterStats, Setting


@dataclass
class DDoSEvent:
    """Represents a DDoS attack event"""
    router_id: int
    timestamp: datetime
    attack_type: str
    source_ip: str
    target_ip: str
    packet_rate: int
    severity: str
    action_taken: str
    details: Optional[str] = None


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logging.info(f"Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            logging.error(f"Configuration file {self.config_path} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing configuration: {e}")
            sys.exit(1)
    
    def get(self, key: str, default=None):
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


class RouterClient:
    """Client for managing a single MikroTik router connection"""
    
    def __init__(self, router: Router):
        self.router = router
        self.api = None
        self.connected = False
        self.last_error = None
    
    def connect(self) -> bool:
        """Establish connection to MikroTik router"""
        try:
            logging.info(f"Connecting to router '{self.router.name}' at {self.router.host}:{self.router.port}")
            self.api = connect(
                host=self.router.host,
                username=self.router.username,
                password=self.router.password,
                port=self.router.port,
                timeout=10
            )
            self.connected = True
            self.last_error = None
            logging.info(f"Successfully connected to router '{self.router.name}'")
            return True
        except (TrapError, FatalError, ConnectionClosed) as e:
            self.connected = False
            self.last_error = str(e)
            logging.error(f"Failed to connect to router '{self.router.name}': {e}")
            return False
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            logging.error(f"Unexpected error connecting to router '{self.router.name}': {e}")
            return False
    
    def disconnect(self):
        """Disconnect from router"""
        if self.api:
            try:
                self.api.close()
            except:
                pass
        self.connected = False
        self.api = None
    
    def get_firewall_filter_stats(self) -> List[Dict]:
        """Get firewall filter rules statistics"""
        try:
            if not self.connected or not self.api:
                return []
            
            firewall = self.api.path('/ip/firewall/filter')
            return list(firewall)
        except Exception as e:
            logging.error(f"Error getting firewall stats from '{self.router.name}': {e}")
            return []
    
    def get_connection_tracking(self) -> List[Dict]:
        """Get connection tracking data"""
        try:
            if not self.connected or not self.api:
                return []
            
            tracking = self.api.path('/ip/firewall/connection/tracking')
            return list(tracking)
        except Exception as e:
            logging.error(f"Error getting connection tracking from '{self.router.name}': {e}")
            return []
    
    def get_system_resources(self) -> Dict:
        """Get system resource information"""
        try:
            if not self.connected or not self.api:
                return {}
            
            system = self.api.path('/system/resource')
            resources = list(system)
            return resources[0] if resources else {}
        except Exception as e:
            logging.error(f"Error getting system resources from '{self.router.name}': {e}")
            return {}
    
    def block_ip(self, ip_address: str, reason: str, duration: str = '1h') -> bool:
        """Add IP address to block list"""
        try:
            if not self.connected or not self.api:
                logging.error(f"Cannot block IP on '{self.router.name}': not connected")
                return False
            
            address_list = self.api.path('/ip/firewall/address-list')
            list_name = 'ddos_blocklist'
            
            address_list.add(
                list=list_name,
                address=ip_address,
                comment=f"{reason} - {datetime.now().isoformat()}",
                timeout=duration
            )
            
            logging.info(f"Blocked IP {ip_address} on router '{self.router.name}': {reason}")
            return True
            
        except Exception as e:
            logging.error(f"Error blocking IP {ip_address} on '{self.router.name}': {e}")
            return False
    
    def unblock_ip(self, ip_address: str, list_name: str = 'ddos_blocklist') -> bool:
        """Remove IP address from block list"""
        try:
            if not self.connected or not self.api:
                logging.error(f"Cannot unblock IP on '{self.router.name}': not connected")
                return False
            
            address_list = self.api.path('/ip/firewall/address-list')
            
            for entry in address_list:
                if entry.get('address') == ip_address and entry.get('list') == list_name:
                    address_list.remove(id=entry.get('.id'))
                    logging.info(f"Unblocked IP {ip_address} on router '{self.router.name}'")
                    return True
            
            logging.warning(f"IP {ip_address} not found in block list on '{self.router.name}'")
            return False
            
        except Exception as e:
            logging.error(f"Error unblocking IP {ip_address} on '{self.router.name}': {e}")
            return False
    
    def get_blocked_ips(self, list_name: str = 'ddos_blocklist') -> List[Dict]:
        """Get list of currently blocked IPs"""
        try:
            if not self.connected or not self.api:
                return []
            
            address_list = self.api.path('/ip/firewall/address-list')
            
            blocked = []
            for entry in address_list:
                if entry.get('list') == list_name:
                    blocked.append({
                        'address': entry.get('address'),
                        'comment': entry.get('comment', ''),
                        'timeout': entry.get('timeout', 'permanent')
                    })
            
            return blocked
            
        except Exception as e:
            logging.error(f"Error getting blocked IPs from '{self.router.name}': {e}")
            return []


class MonitorWorker:
    """Worker for monitoring a single router"""
    
    def __init__(self, router: Router, config: ConfigManager, db_manager):
        self.router = router
        self.config = config
        self.db_manager = db_manager
        self.client = RouterClient(router)
        self.running = False
    
    def analyze_traffic(self) -> List[DDoSEvent]:
        """Analyze traffic patterns for potential DDoS attacks"""
        events = []
        
        try:
            # Get firewall filter rules statistics
            rules = self.client.get_firewall_filter_stats()
            
            threshold = self.config.get('detection.packet_threshold', 10000)
            
            # Analyze connection rates
            connections = {}
            for rule in rules:
                src_addr = rule.get('src-address', '')
                if src_addr:
                    connections[src_addr] = connections.get(src_addr, 0) + 1
            
            # Detect anomalies
            for src_ip, count in connections.items():
                if count > threshold:
                    severity = self.calculate_severity(count, threshold)
                    event = DDoSEvent(
                        router_id=self.router.id,
                        timestamp=datetime.now(),
                        attack_type="High Connection Rate",
                        source_ip=src_ip,
                        target_ip=self.router.host,
                        packet_rate=count,
                        severity=severity,
                        action_taken="Pending",
                        details=f"Connection count: {count}"
                    )
                    events.append(event)
                    logging.warning(f"[{self.router.name}] Potential DDoS from {src_ip}: {count} connections")
            
        except Exception as e:
            logging.error(f"[{self.router.name}] Error analyzing traffic: {e}")
        
        return events
    
    def calculate_severity(self, count: int, threshold: int) -> str:
        """Calculate attack severity based on packet rate"""
        ratio = count / threshold
        if ratio >= 10:
            return "CRITICAL"
        elif ratio >= 5:
            return "HIGH"
        elif ratio >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def collect_stats(self):
        """Collect router statistics"""
        try:
            resources = self.client.get_system_resources()
            
            if resources:
                session = self.db_manager.get_session()
                try:
                    stats = RouterStats(
                        router_id=self.router.id,
                        timestamp=datetime.now(),
                        cpu_load=float(resources.get('cpu-load', 0)),
                        memory_used=int(resources.get('total-memory', 0)) - int(resources.get('free-memory', 0)),
                        memory_total=int(resources.get('total-memory', 0)),
                        uptime=resources.get('uptime', ''),
                        connection_count=None  # TODO: implement connection count
                    )
                    session.add(stats)
                    session.commit()
                    logging.debug(f"[{self.router.name}] Stats collected: CPU={stats.cpu_load}%")
                finally:
                    session.close()
        except Exception as e:
            logging.error(f"[{self.router.name}] Error collecting stats: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop for this router"""
        self.running = True
        check_interval = self.config.get('detection.check_interval', 30)
        auto_block = self.config.get('detection.auto_block_enabled', True)
        block_duration = self.config.get('detection.block_duration', '1h')
        
        logging.info(f"[{self.router.name}] Starting monitoring loop")
        
        # Connect to router
        if not self.client.connect():
            logging.error(f"[{self.router.name}] Failed to connect, stopping monitor")
            self.running = False
            return
        
        # Update router status
        session = self.db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=self.router.id).first()
            if router:
                router.status = 'connected'
                router.last_seen = datetime.now()
                session.commit()
        finally:
            session.close()
        
        while self.running:
            try:
                # Update last seen timestamp
                session = self.db_manager.get_session()
                try:
                    router = session.query(Router).filter_by(id=self.router.id).first()
                    if router:
                        router.last_seen = datetime.now()
                        session.commit()
                finally:
                    session.close()
                
                # Analyze traffic for DDoS attacks
                events = self.analyze_traffic()
                
                # Process detected events
                for event_data in events:
                    session = self.db_manager.get_session()
                    try:
                        # Create event record
                        event = Event(
                            router_id=event_data.router_id,
                            timestamp=event_data.timestamp,
                            attack_type=event_data.attack_type,
                            source_ip=event_data.source_ip,
                            target_ip=event_data.target_ip,
                            packet_rate=event_data.packet_rate,
                            severity=event_data.severity,
                            action_taken=event_data.action_taken,
                            details=event_data.details
                        )
                        session.add(event)
                        session.commit()
                        
                        # Auto-block if enabled and severity is high
                        if auto_block and event_data.severity in ['HIGH', 'CRITICAL']:
                            if self.client.block_ip(event_data.source_ip, event_data.attack_type, block_duration):
                                # Update event action
                                event.action_taken = "Blocked"
                                
                                # Create blocked IP record
                                blocked_ip = BlockedIP(
                                    router_id=self.router.id,
                                    ip_address=event_data.source_ip,
                                    reason=event_data.attack_type,
                                    blocked_at=datetime.now(),
                                    status='active'
                                )
                                session.add(blocked_ip)
                                session.commit()
                    finally:
                        session.close()
                
                # Collect router statistics
                self.collect_stats()
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info(f"[{self.router.name}] Monitoring interrupted")
                self.running = False
                break
            except Exception as e:
                logging.error(f"[{self.router.name}] Error in monitoring loop: {e}")
                time.sleep(check_interval)
        
        # Cleanup
        self.client.disconnect()
        
        # Update router status
        session = self.db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=self.router.id).first()
            if router:
                router.status = 'disconnected'
                session.commit()
        finally:
            session.close()
        
        logging.info(f"[{self.router.name}] Monitoring loop stopped")
    
    def start(self):
        """Start the monitor in a thread"""
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        self.client.disconnect()


class MultiRouterManager:
    """Manager for monitoring multiple routers"""
    
    def __init__(self, config: ConfigManager, db_manager):
        self.config = config
        self.db_manager = db_manager
        self.monitors = {}
        self.running = False
    
    def load_routers(self) -> List[Router]:
        """Load enabled routers from database"""
        session = self.db_manager.get_session()
        try:
            routers = session.query(Router).filter_by(enabled=True).all()
            logging.info(f"Loaded {len(routers)} enabled routers from database")
            return routers
        finally:
            session.close()
    
    def start_monitoring(self):
        """Start monitoring all enabled routers"""
        self.running = True
        routers = self.load_routers()
        
        if not routers:
            logging.warning("No enabled routers found in database")
            return
        
        logging.info(f"Starting monitoring for {len(routers)} routers")
        
        for router in routers:
            monitor = MonitorWorker(router, self.config, self.db_manager)
            thread = monitor.start()
            self.monitors[router.id] = {
                'monitor': monitor,
                'thread': thread
            }
            logging.info(f"Started monitor for router '{router.name}'")
    
    def stop_monitoring(self):
        """Stop monitoring all routers"""
        self.running = False
        
        logging.info("Stopping all monitors...")
        
        for router_id, monitor_info in self.monitors.items():
            monitor = monitor_info['monitor']
            monitor.stop()
            logging.info(f"Stopped monitor for router ID {router_id}")
        
        # Wait for threads to finish (with timeout)
        for router_id, monitor_info in self.monitors.items():
            thread = monitor_info['thread']
            thread.join(timeout=5)
        
        self.monitors.clear()
        logging.info("All monitors stopped")


class DDoSManagerApp:
    """Main application class for multi-router DDoS management"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.setup_logging()
        self.config = ConfigManager(config_path)
        
        # Initialize database
        db_path = self.config.get('database.path', 'ddos_events.db')
        self.db_manager = get_database(f'sqlite:///{db_path}')
        
        # Initialize multi-router manager
        self.manager = MultiRouterManager(self.config, self.db_manager)
        
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mt_ddos_manager.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        self.manager.stop_monitoring()
        self.db_manager.close()
        logging.info("Application shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        logging.info("=" * 70)
        logging.info("MikroTik Multi-Router DDoS Manager & Auto-Actuator")
        logging.info("=" * 70)
        
        try:
            self.manager.start_monitoring()
            
            # Keep main thread alive
            while True:
                time.sleep(60)
                
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
            self.shutdown()
        except Exception as e:
            logging.error(f"Fatal error: {e}")
            self.shutdown()


def main():
    """Main entry point"""
    config_file = os.getenv('CONFIG_FILE', 'config.yml')
    app = DDoSManagerApp(config_file)
    app.run()


if __name__ == "__main__":
    main()
