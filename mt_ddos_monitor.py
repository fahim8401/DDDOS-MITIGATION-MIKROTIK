#!/usr/bin/env python3
"""
MikroTik DDoS Monitor & Auto-Actuator
A robust Python 3.11+ application for monitoring and mitigating DDoS attacks on MikroTik routers.
"""

import os
import sys
import time
import logging
import sqlite3
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import signal
import threading

try:
    import librouteros
    from librouteros import connect
    from librouteros.exceptions import TrapError, FatalError, ConnectionClosed
except ImportError:
    print("Error: librouteros is required. Install with: pip install librouteros")
    sys.exit(1)


@dataclass
class DDoSEvent:
    """Represents a DDoS attack event"""
    timestamp: datetime
    attack_type: str
    source_ip: str
    target_ip: str
    packet_rate: int
    severity: str
    action_taken: str


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


class DatabaseManager:
    """Manages SQLite database for event logging"""
    
    def __init__(self, db_path: str = "ddos_events.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    source_ip TEXT NOT NULL,
                    target_ip TEXT NOT NULL,
                    packet_rate INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    action_taken TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source_ip ON events(source_ip)
            ''')
            self.conn.commit()
            logging.info("Database initialized successfully")
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            sys.exit(1)
    
    def log_event(self, event: DDoSEvent):
        """Log a DDoS event to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO events (timestamp, attack_type, source_ip, target_ip, 
                                  packet_rate, severity, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.timestamp.isoformat(),
                event.attack_type,
                event.source_ip,
                event.target_ip,
                event.packet_rate,
                event.severity,
                event.action_taken
            ))
            self.conn.commit()
            logging.debug(f"Event logged: {event.source_ip} -> {event.target_ip}")
        except sqlite3.Error as e:
            logging.error(f"Error logging event: {e}")
    
    def get_recent_events(self, hours: int = 24) -> List[DDoSEvent]:
        """Get recent events from the database"""
        try:
            cursor = self.conn.cursor()
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute('''
                SELECT timestamp, attack_type, source_ip, target_ip, 
                       packet_rate, severity, action_taken
                FROM events
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since,))
            
            events = []
            for row in cursor.fetchall():
                events.append(DDoSEvent(
                    timestamp=datetime.fromisoformat(row[0]),
                    attack_type=row[1],
                    source_ip=row[2],
                    target_ip=row[3],
                    packet_rate=row[4],
                    severity=row[5],
                    action_taken=row[6]
                ))
            return events
        except sqlite3.Error as e:
            logging.error(f"Error retrieving events: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class MikroTikMonitor:
    """Monitors MikroTik router for DDoS attacks"""
    
    def __init__(self, config: ConfigManager, db: DatabaseManager):
        self.config = config
        self.db = db
        self.api = None
        self.running = False
        self.blocked_ips = set()
        
    def connect_to_router(self) -> bool:
        """Establish connection to MikroTik router"""
        try:
            host = self.config.get('mikrotik.host')
            username = self.config.get('mikrotik.username')
            password = self.config.get('mikrotik.password')
            port = self.config.get('mikrotik.port', 8728)
            
            logging.info(f"Connecting to MikroTik router at {host}:{port}")
            self.api = connect(
                host=host,
                username=username,
                password=password,
                port=port,
                timeout=10
            )
            logging.info("Successfully connected to MikroTik router")
            return True
        except (TrapError, FatalError, ConnectionClosed) as e:
            logging.error(f"Failed to connect to MikroTik router: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error connecting to router: {e}")
            return False
    
    def get_connection_tracking(self) -> List[Dict]:
        """Get connection tracking data from router"""
        try:
            if not self.api:
                return []
            
            tracking = self.api.path('/ip/firewall/connection/tracking')
            return list(tracking)
        except Exception as e:
            logging.error(f"Error getting connection tracking: {e}")
            return []
    
    def analyze_traffic(self) -> List[DDoSEvent]:
        """Analyze traffic patterns for potential DDoS attacks"""
        events = []
        
        try:
            # Get firewall filter rules statistics
            firewall = self.api.path('/ip/firewall/filter')
            rules = list(firewall)
            
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
                        timestamp=datetime.now(),
                        attack_type="High Connection Rate",
                        source_ip=src_ip,
                        target_ip=self.config.get('mikrotik.host', 'unknown'),
                        packet_rate=count,
                        severity=severity,
                        action_taken="Pending"
                    )
                    events.append(event)
                    logging.warning(f"Potential DDoS detected from {src_ip}: {count} connections")
            
        except Exception as e:
            logging.error(f"Error analyzing traffic: {e}")
        
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
    
    def block_ip(self, ip_address: str, reason: str = "DDoS Attack") -> bool:
        """Add IP address to block list"""
        try:
            if ip_address in self.blocked_ips:
                logging.debug(f"IP {ip_address} already blocked")
                return True
            
            address_list = self.api.path('/ip/firewall/address-list')
            list_name = self.config.get('detection.address_list_name', 'ddos_blocklist')
            
            address_list.add(
                list=list_name,
                address=ip_address,
                comment=f"{reason} - {datetime.now().isoformat()}",
                timeout=self.config.get('detection.block_duration', '1h')
            )
            
            self.blocked_ips.add(ip_address)
            logging.info(f"Blocked IP {ip_address}: {reason}")
            return True
            
        except Exception as e:
            logging.error(f"Error blocking IP {ip_address}: {e}")
            return False
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Remove IP address from block list"""
        try:
            address_list = self.api.path('/ip/firewall/address-list')
            list_name = self.config.get('detection.address_list_name', 'ddos_blocklist')
            
            for entry in address_list:
                if entry.get('address') == ip_address and entry.get('list') == list_name:
                    address_list.remove(id=entry.get('.id'))
                    self.blocked_ips.discard(ip_address)
                    logging.info(f"Unblocked IP {ip_address}")
                    return True
            
            logging.warning(f"IP {ip_address} not found in block list")
            return False
            
        except Exception as e:
            logging.error(f"Error unblocking IP {ip_address}: {e}")
            return False
    
    def get_blocked_ips(self) -> List[Dict]:
        """Get list of currently blocked IPs"""
        try:
            address_list = self.api.path('/ip/firewall/address-list')
            list_name = self.config.get('detection.address_list_name', 'ddos_blocklist')
            
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
            logging.error(f"Error getting blocked IPs: {e}")
            return []
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.running = True
        check_interval = self.config.get('detection.check_interval', 30)
        auto_block = self.config.get('detection.auto_block_enabled', True)
        
        logging.info("Starting monitoring loop")
        
        while self.running:
            try:
                # Analyze traffic for DDoS attacks
                events = self.analyze_traffic()
                
                for event in events:
                    # Log event to database
                    self.db.log_event(event)
                    
                    # Auto-block if enabled
                    if auto_block and event.severity in ['HIGH', 'CRITICAL']:
                        if self.block_ip(event.source_ip, event.attack_type):
                            event.action_taken = "Blocked"
                            self.db.log_event(event)
                    
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info("Monitoring interrupted by user")
                self.running = False
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
        
        logging.info("Monitoring loop stopped")
    
    def start(self):
        """Start the monitor"""
        if self.connect_to_router():
            self.monitor_loop()
        else:
            logging.error("Failed to start monitor - connection failed")
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        if self.api:
            self.api.close()


class DDoSMonitorApp:
    """Main application class"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.setup_logging()
        self.config = ConfigManager(config_path)
        self.db = DatabaseManager(self.config.get('database.path', 'ddos_events.db'))
        self.monitor = MikroTikMonitor(self.config, self.db)
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mt_ddos_monitor.log'),
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
        self.monitor.stop()
        self.db.close()
        logging.info("Application shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        logging.info("=" * 60)
        logging.info("MikroTik DDoS Monitor & Auto-Actuator")
        logging.info("=" * 60)
        
        try:
            self.monitor.start()
        except Exception as e:
            logging.error(f"Fatal error: {e}")
            self.shutdown()


def main():
    """Main entry point"""
    config_file = os.getenv('CONFIG_FILE', 'config.yml')
    app = DDoSMonitorApp(config_file)
    app.run()


if __name__ == "__main__":
    main()
