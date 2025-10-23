#!/usr/bin/env python3
"""
Flask API for MikroTik DDoS Monitor
Provides RESTful endpoints for monitoring and management
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from functools import wraps
import sqlite3
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mt_ddos_monitor import ConfigManager, DatabaseManager, MikroTikMonitor

app = Flask(__name__)
CORS(app)

# Initialize components
config = ConfigManager(os.getenv('CONFIG_FILE', 'config.yml'))
db = DatabaseManager(config.get('database.path', 'ddos_events.db'))
monitor = MikroTikMonitor(config, db)

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
        # Check database connection
        db_status = db.conn is not None
        
        # Check router connection
        router_connected = monitor.api is not None
        
        return jsonify({
            'status': 'healthy' if db_status and router_connected else 'degraded',
            'database': 'connected' if db_status else 'disconnected',
            'router': 'connected' if router_connected else 'disconnected',
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
        # Connect to router if not already connected
        if not monitor.api:
            monitor.connect_to_router()
        
        # Get recent events
        recent_events = db.get_recent_events(hours=1)
        
        # Get blocked IPs
        blocked_ips = monitor.get_blocked_ips()
        
        return jsonify({
            'status': 'operational',
            'router_connected': monitor.api is not None,
            'recent_events_count': len(recent_events),
            'blocked_ips_count': len(blocked_ips),
            'monitoring_active': monitor.running,
            'timestamp': datetime.now().isoformat()
        }), 200
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
        limit = request.args.get('limit', default=100, type=int)
        
        # Get events from database
        events = db.get_recent_events(hours=hours)
        
        # Filter by severity if specified
        if severity:
            events = [e for e in events if e.severity == severity.upper()]
        
        # Limit results
        events = events[:limit]
        
        # Convert to JSON-serializable format
        events_data = [
            {
                'timestamp': e.timestamp.isoformat(),
                'attack_type': e.attack_type,
                'source_ip': e.source_ip,
                'target_ip': e.target_ip,
                'packet_rate': e.packet_rate,
                'severity': e.severity,
                'action_taken': e.action_taken
            }
            for e in events
        ]
        
        return jsonify({
            'events': events_data,
            'total': len(events_data),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logging.error(f"Error getting events: {e}")
        return jsonify({'error': 'Failed to retrieve events'}), 500


@app.route('/api/events/stats', methods=['GET'])
@require_api_key
def get_event_stats():
    """Get event statistics"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        events = db.get_recent_events(hours=hours)
        
        # Calculate statistics
        stats = {
            'total_events': len(events),
            'by_severity': {},
            'by_type': {},
            'unique_sources': len(set(e.source_ip for e in events)),
            'timestamp': datetime.now().isoformat()
        }
        
        # Count by severity
        for event in events:
            stats['by_severity'][event.severity] = stats['by_severity'].get(event.severity, 0) + 1
            stats['by_type'][event.attack_type] = stats['by_type'].get(event.attack_type, 0) + 1
        
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error getting event stats: {e}")
        return jsonify({'error': 'Failed to retrieve event statistics'}), 500


@app.route('/api/blocked-ips', methods=['GET'])
@require_api_key
def get_blocked_ips():
    """Get list of currently blocked IP addresses"""
    try:
        # Connect to router if not already connected
        if not monitor.api:
            monitor.connect_to_router()
        
        blocked = monitor.get_blocked_ips()
        
        return jsonify({
            'blocked_ips': blocked,
            'total': len(blocked),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logging.error(f"Error getting blocked IPs: {e}")
        return jsonify({'error': 'Failed to retrieve blocked IPs'}), 500


@app.route('/api/blocked-ips', methods=['POST'])
@require_api_key
def block_ip():
    """Manually block an IP address"""
    try:
        data = request.get_json()
        
        if not data or 'ip_address' not in data:
            return jsonify({'error': 'IP address is required'}), 400
        
        ip_address = data['ip_address']
        reason = data.get('reason', 'Manual block')
        
        # Connect to router if not already connected
        if not monitor.api:
            if not monitor.connect_to_router():
                return jsonify({'error': 'Failed to connect to router'}), 500
        
        # Block the IP
        if monitor.block_ip(ip_address, reason):
            return jsonify({
                'success': True,
                'message': f'IP {ip_address} blocked successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Failed to block IP'}), 500
            
    except Exception as e:
        logging.error(f"Error blocking IP: {e}")
        return jsonify({'error': 'Failed to block IP address'}), 500


@app.route('/api/blocked-ips/<ip_address>', methods=['DELETE'])
@require_api_key
def unblock_ip(ip_address):
    """Unblock an IP address"""
    try:
        # Connect to router if not already connected
        if not monitor.api:
            if not monitor.connect_to_router():
                return jsonify({'error': 'Failed to connect to router'}), 500
        
        # Unblock the IP
        if monitor.unblock_ip(ip_address):
            return jsonify({
                'success': True,
                'message': f'IP {ip_address} unblocked successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Failed to unblock IP or IP not found'}), 404
            
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


@app.route('/api/router/info', methods=['GET'])
@require_api_key
def get_router_info():
    """Get MikroTik router information"""
    try:
        # Connect to router if not already connected
        if not monitor.api:
            if not monitor.connect_to_router():
                return jsonify({'error': 'Failed to connect to router'}), 500
        
        # Get system resource info
        system = monitor.api.path('/system/resource')
        resource_info = list(system)[0] if system else {}
        
        return jsonify({
            'platform': resource_info.get('platform', 'unknown'),
            'board_name': resource_info.get('board-name', 'unknown'),
            'version': resource_info.get('version', 'unknown'),
            'uptime': resource_info.get('uptime', 'unknown'),
            'cpu_load': resource_info.get('cpu-load', 0),
            'free_memory': resource_info.get('free-memory', 0),
            'total_memory': resource_info.get('total-memory', 0),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logging.error(f"Error getting router info: {e}")
        return jsonify({'error': 'Failed to retrieve router information'}), 500


@app.route('/api/dashboard/summary', methods=['GET'])
@require_api_key
def get_dashboard_summary():
    """Get dashboard summary data"""
    try:
        # Connect to router if not already connected
        if not monitor.api:
            monitor.connect_to_router()
        
        # Get recent events
        recent_events = db.get_recent_events(hours=24)
        
        # Get blocked IPs
        blocked_ips = monitor.get_blocked_ips()
        
        # Calculate statistics
        critical_events = len([e for e in recent_events if e.severity == 'CRITICAL'])
        high_events = len([e for e in recent_events if e.severity == 'HIGH'])
        
        return jsonify({
            'total_events_24h': len(recent_events),
            'critical_events': critical_events,
            'high_events': high_events,
            'blocked_ips_count': len(blocked_ips),
            'router_connected': monitor.api is not None,
            'monitoring_active': monitor.running,
            'recent_events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'attack_type': e.attack_type,
                    'source_ip': e.source_ip,
                    'severity': e.severity
                }
                for e in recent_events[:10]
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
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
    # Connect to router on startup
    monitor.connect_to_router()
    logging.info("API initialized successfully")


if __name__ == '__main__':
    init_api()
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '5000'))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
