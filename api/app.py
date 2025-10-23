#!/usr/bin/env python3
"""
Flask API for Multi-Router MikroTik DDoS Monitor
Provides RESTful endpoints for monitoring and management
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from functools import wraps
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mt_ddos_manager import ConfigManager, RouterClient
from models import get_database, Router, Event, BlockedIP, RouterStats, Setting

app = Flask(__name__)
CORS(app)

# Initialize components
config = ConfigManager(os.getenv('CONFIG_FILE', 'config.yml'))
db_path = config.get('database.path', 'ddos_events.db')
db_manager = get_database(f'sqlite:///{db_path}')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# API Key authentication
API_KEY = os.getenv('API_KEY', config.get('api.key', 'changeme'))


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        from sqlalchemy import text
        
        # Check database connection
        session = db_manager.get_session()
        db_status = False
        try:
            session.execute(text('SELECT 1'))
            db_status = True
        finally:
            session.close()
        
        # Check router connections
        session = db_manager.get_session()
        try:
            router_count = session.query(Router).count()
            connected_count = session.query(Router).filter_by(status='connected').count()
        finally:
            session.close()
        
        return jsonify({
            'status': 'healthy' if db_status else 'degraded',
            'database': 'connected' if db_status else 'disconnected',
            'total_routers': router_count,
            'connected_routers': connected_count,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Service unavailable',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/status', methods=['GET'])
@require_api_key
def get_status():
    """Get current system status"""
    try:
        session = db_manager.get_session()
        try:
            # Get router counts
            total_routers = session.query(Router).count()
            enabled_routers = session.query(Router).filter_by(enabled=True).count()
            connected_routers = session.query(Router).filter_by(status='connected').count()
            
            # Get recent events (last hour)
            since = datetime.now() - timedelta(hours=1)
            recent_events_count = session.query(Event).filter(Event.timestamp >= since).count()
            
            # Get blocked IPs count
            blocked_ips_count = session.query(BlockedIP).filter_by(status='active').count()
            
            return jsonify({
                'status': 'operational',
                'total_routers': total_routers,
                'enabled_routers': enabled_routers,
                'connected_routers': connected_routers,
                'recent_events_count': recent_events_count,
                'blocked_ips_count': blocked_ips_count,
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return jsonify({'error': 'Failed to retrieve status'}), 500


@app.route('/api/events', methods=['GET'])
@require_api_key
def get_events():
    """Get DDoS events with optional filtering"""
    try:
        # Get query parameters
        hours = request.args.get('hours', default=24, type=int)
        severity = request.args.get('severity', default=None, type=str)
        router_id = request.args.get('router_id', default=None, type=int)
        limit = request.args.get('limit', default=100, type=int)
        
        session = db_manager.get_session()
        try:
            # Build query
            since = datetime.now() - timedelta(hours=hours)
            query = session.query(Event).filter(Event.timestamp >= since)
            
            # Filter by severity if specified
            if severity:
                query = query.filter(Event.severity == severity.upper())
            
            # Filter by router if specified
            if router_id:
                query = query.filter(Event.router_id == router_id)
            
            # Order by timestamp descending and limit
            events = query.order_by(Event.timestamp.desc()).limit(limit).all()
            
            # Convert to JSON-serializable format
            events_data = [event.to_dict() for event in events]
            
            return jsonify({
                'events': events_data,
                'total': len(events_data),
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting events: {e}")
        return jsonify({'error': 'Failed to retrieve events'}), 500


@app.route('/api/events/stats', methods=['GET'])
@require_api_key
def get_event_stats():
    """Get event statistics"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        router_id = request.args.get('router_id', default=None, type=int)
        
        session = db_manager.get_session()
        try:
            # Build query
            since = datetime.now() - timedelta(hours=hours)
            query = session.query(Event).filter(Event.timestamp >= since)
            
            # Filter by router if specified
            if router_id:
                query = query.filter(Event.router_id == router_id)
            
            events = query.all()
            
            # Calculate statistics
            stats = {
                'total_events': len(events),
                'by_severity': {},
                'by_type': {},
                'by_router': {},
                'unique_sources': len(set(e.source_ip for e in events)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Count by severity, type, and router
            for event in events:
                stats['by_severity'][event.severity] = stats['by_severity'].get(event.severity, 0) + 1
                stats['by_type'][event.attack_type] = stats['by_type'].get(event.attack_type, 0) + 1
                router_name = event.router.name if event.router else f"Router {event.router_id}"
                stats['by_router'][router_name] = stats['by_router'].get(router_name, 0) + 1
            
            return jsonify(stats), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting event stats: {e}")
        return jsonify({'error': 'Failed to retrieve event statistics'}), 500


@app.route('/api/blocked-ips', methods=['GET'])
@require_api_key
def get_blocked_ips():
    """Get list of currently blocked IP addresses"""
    try:
        router_id = request.args.get('router_id', default=None, type=int)
        
        session = db_manager.get_session()
        try:
            # Build query
            query = session.query(BlockedIP).filter_by(status='active')
            
            # Filter by router if specified
            if router_id:
                query = query.filter_by(router_id=router_id)
            
            blocked = query.all()
            blocked_data = [b.to_dict() for b in blocked]
            
            return jsonify({
                'blocked_ips': blocked_data,
                'total': len(blocked_data),
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting blocked IPs: {e}")
        return jsonify({'error': 'Failed to retrieve blocked IPs'}), 500


@app.route('/api/blocked-ips', methods=['POST'])
@require_api_key
def block_ip():
    """Manually block an IP address"""
    try:
        data = request.get_json()
        
        if not data or 'ip_address' not in data or 'router_id' not in data:
            return jsonify({'error': 'IP address and router_id are required'}), 400
        
        ip_address = data['ip_address']
        router_id = data['router_id']
        reason = data.get('reason', 'Manual block')
        duration = data.get('duration', '1h')
        
        session = db_manager.get_session()
        try:
            # Get router
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            # Connect to router and block IP
            client = RouterClient(router)
            if not client.connect():
                return jsonify({'error': f'Failed to connect to router {router.name}'}), 500
            
            try:
                if client.block_ip(ip_address, reason, duration):
                    # Create blocked IP record
                    blocked_ip = BlockedIP(
                        router_id=router_id,
                        ip_address=ip_address,
                        reason=reason,
                        blocked_at=datetime.now(),
                        status='active'
                    )
                    session.add(blocked_ip)
                    session.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': f'IP {ip_address} blocked on router {router.name}',
                        'timestamp': datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({'error': 'Failed to block IP on router'}), 500
            finally:
                client.disconnect()
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error blocking IP: {e}")
        return jsonify({'error': 'Failed to block IP address'}), 500


@app.route('/api/blocked-ips/<int:blocked_id>', methods=['DELETE'])
@require_api_key
def unblock_ip(blocked_id):
    """Unblock an IP address"""
    try:
        session = db_manager.get_session()
        try:
            # Get blocked IP record
            blocked = session.query(BlockedIP).filter_by(id=blocked_id).first()
            if not blocked:
                return jsonify({'error': 'Blocked IP not found'}), 404
            
            # Get router
            router = session.query(Router).filter_by(id=blocked.router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            # Connect to router and unblock IP
            client = RouterClient(router)
            if not client.connect():
                return jsonify({'error': f'Failed to connect to router {router.name}'}), 500
            
            try:
                if client.unblock_ip(blocked.ip_address):
                    # Update blocked IP record
                    blocked.status = 'unblocked'
                    blocked.unblocked_at = datetime.now()
                    session.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': f'IP {blocked.ip_address} unblocked from router {router.name}',
                        'timestamp': datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({'error': 'Failed to unblock IP on router'}), 500
            finally:
                client.disconnect()
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error unblocking IP: {e}")
        return jsonify({'error': 'Failed to unblock IP address'}), 500


@app.route('/api/config', methods=['GET'])
@require_api_key
def get_config():
    """Get current configuration (sensitive data redacted)"""
    try:
        safe_config = {
            'detection': config.get('detection', {}),
            'monitoring': {
                'check_interval': config.get('detection.check_interval'),
                'auto_block_enabled': config.get('detection.auto_block_enabled')
            },
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(safe_config), 200
    except Exception as e:
        logging.error(f"Error getting config: {e}")
        return jsonify({'error': 'Failed to retrieve configuration'}), 500


@app.route('/api/routers', methods=['GET'])
@require_api_key
def get_routers():
    """Get list of all routers"""
    try:
        session = db_manager.get_session()
        try:
            routers = session.query(Router).all()
            routers_data = [r.to_dict() for r in routers]
            
            return jsonify({
                'routers': routers_data,
                'total': len(routers_data),
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting routers: {e}")
        return jsonify({'error': 'Failed to retrieve routers'}), 500


@app.route('/api/routers/<int:router_id>', methods=['GET'])
@require_api_key
def get_router(router_id):
    """Get specific router information"""
    try:
        session = db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            return jsonify(router.to_dict()), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting router: {e}")
        return jsonify({'error': 'Failed to retrieve router'}), 500


@app.route('/api/routers', methods=['POST'])
@require_api_key
def create_router():
    """Create a new router configuration"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'host', 'username', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
        
        session = db_manager.get_session()
        try:
            # Check if router name already exists
            existing = session.query(Router).filter_by(name=data['name']).first()
            if existing:
                return jsonify({'error': 'Router name already exists'}), 409
            
            # Create new router
            router = Router(
                name=data['name'],
                host=data['host'],
                port=data.get('port', 8728),
                username=data['username'],
                password=data['password'],
                use_ssl=data.get('use_ssl', False),
                enabled=data.get('enabled', True),
                status='unknown'
            )
            session.add(router)
            session.commit()
            
            return jsonify({
                'success': True,
                'router': router.to_dict(),
                'message': 'Router created successfully'
            }), 201
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error creating router: {e}")
        return jsonify({'error': 'Failed to create router'}), 500


@app.route('/api/routers/<int:router_id>', methods=['PUT'])
@require_api_key
def update_router(router_id):
    """Update router configuration"""
    try:
        data = request.get_json()
        
        session = db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            # Update fields
            if 'name' in data:
                router.name = data['name']
            if 'host' in data:
                router.host = data['host']
            if 'port' in data:
                router.port = data['port']
            if 'username' in data:
                router.username = data['username']
            if 'password' in data:
                router.password = data['password']
            if 'use_ssl' in data:
                router.use_ssl = data['use_ssl']
            if 'enabled' in data:
                router.enabled = data['enabled']
            
            router.updated_at = datetime.now()
            session.commit()
            
            return jsonify({
                'success': True,
                'router': router.to_dict(),
                'message': 'Router updated successfully'
            }), 200
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error updating router: {e}")
        return jsonify({'error': 'Failed to update router'}), 500


@app.route('/api/routers/<int:router_id>', methods=['DELETE'])
@require_api_key
def delete_router(router_id):
    """Delete a router configuration"""
    try:
        session = db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            session.delete(router)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Router {router.name} deleted successfully'
            }), 200
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error deleting router: {e}")
        return jsonify({'error': 'Failed to delete router'}), 500


@app.route('/api/routers/<int:router_id>/test', methods=['POST'])
@require_api_key
def test_router_connection(router_id):
    """Test connection to a router"""
    try:
        session = db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            # Test connection
            client = RouterClient(router)
            if client.connect():
                # Get system info
                resources = client.get_system_resources()
                client.disconnect()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully connected to router {router.name}',
                    'system_info': {
                        'platform': resources.get('platform', 'unknown'),
                        'board_name': resources.get('board-name', 'unknown'),
                        'version': resources.get('version', 'unknown'),
                        'uptime': resources.get('uptime', 'unknown')
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': f'Failed to connect to router {router.name}',
                    'error': client.last_error
                }), 500
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error testing router connection: {e}")
        return jsonify({'error': 'Failed to test router connection'}), 500


@app.route('/api/routers/<int:router_id>/stats', methods=['GET'])
@require_api_key
def get_router_stats(router_id):
    """Get router statistics"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        
        session = db_manager.get_session()
        try:
            router = session.query(Router).filter_by(id=router_id).first()
            if not router:
                return jsonify({'error': 'Router not found'}), 404
            
            # Get recent stats
            since = datetime.now() - timedelta(hours=hours)
            stats = session.query(RouterStats).filter(
                RouterStats.router_id == router_id,
                RouterStats.timestamp >= since
            ).order_by(RouterStats.timestamp.asc()).all()
            
            stats_data = [s.to_dict() for s in stats]
            
            return jsonify({
                'router_name': router.name,
                'stats': stats_data,
                'total': len(stats_data),
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error getting router stats: {e}")
        return jsonify({'error': 'Failed to retrieve router statistics'}), 500


@app.route('/api/dashboard/summary', methods=['GET'])
@require_api_key
def get_dashboard_summary():
    """Get dashboard summary data"""
    try:
        session = db_manager.get_session()
        try:
            # Get router counts
            total_routers = session.query(Router).count()
            enabled_routers = session.query(Router).filter_by(enabled=True).count()
            connected_routers = session.query(Router).filter_by(status='connected').count()
            
            # Get recent events (last 24 hours)
            since = datetime.now() - timedelta(hours=24)
            recent_events = session.query(Event).filter(Event.timestamp >= since).all()
            
            # Get blocked IPs
            blocked_ips_count = session.query(BlockedIP).filter_by(status='active').count()
            
            # Calculate statistics
            critical_events = len([e for e in recent_events if e.severity == 'CRITICAL'])
            high_events = len([e for e in recent_events if e.severity == 'HIGH'])
            
            # Get recent 10 events
            recent_10 = session.query(Event).order_by(Event.timestamp.desc()).limit(10).all()
            
            return jsonify({
                'total_routers': total_routers,
                'enabled_routers': enabled_routers,
                'connected_routers': connected_routers,
                'total_events_24h': len(recent_events),
                'critical_events': critical_events,
                'high_events': high_events,
                'blocked_ips_count': blocked_ips_count,
                'recent_events': [e.to_dict() for e in recent_10],
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error getting dashboard summary: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard summary'}), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


def init_api():
    """Initialize the API"""
    logging.info("Initializing multi-router DDoS Monitor API")
    
    # Ensure database is initialized
    db_manager.create_tables()
    
    logging.info("API initialized successfully")


if __name__ == '__main__':
    init_api()
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '5000'))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
