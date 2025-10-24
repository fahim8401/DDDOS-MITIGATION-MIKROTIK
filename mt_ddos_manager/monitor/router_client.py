"""
Router client abstraction over librouteros
"""

import librouteros
from librouteros import connect
from librouteros.exceptions import TrapError, FatalError, ConnectionClosed
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class RouterClient:
    """Client for MikroTik RouterOS API"""

    def __init__(self, host: str, username: str, password: str, port: int = 8728, use_ssl: bool = False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self._connection = None

    def connect(self):
        """Establish connection to router"""
        try:
            self._connection = connect(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                ssl=self.use_ssl
            )
            logger.info(f"Connected to router {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to router {self.host}:{self.port}: {e}")
            raise

    def disconnect(self):
        """Close connection"""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            self._connection = None

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connection is not None

    def get_total_connections_count(self) -> int:
        """Get total connections count"""
        try:
            if not self._connection:
                self.connect()

            # Try print count-only first
            result = tuple(self._connection('/ip/firewall/connection/print', count_only=True))
            if result:
                return result[0]['count']
            else:
                # Fallback to counting
                connections = tuple(self._connection('/ip/firewall/connection/print'))
                return len(connections)
        except Exception as e:
            logger.error(f"Error getting connections count: {e}")
            return 0

    def monitor_interface_traffic(self, iface: str, duration: int = 1) -> Dict[str, Any]:
        """Monitor interface traffic"""
        try:
            if not self._connection:
                self.connect()

            result = tuple(self._connection('/interface/monitor-traffic', interface=iface, duration=duration))
            return dict(result[0]) if result else {}
        except Exception as e:
            logger.error(f"Error monitoring interface {iface}: {e}")
            return {}

    def run_script(self, name: str) -> Dict[str, Any]:
        """Run a script by name"""
        try:
            if not self._connection:
                self.connect()

            result = tuple(self._connection('/system/script/run', numbers=name))
            return {'success': True, 'result': dict(result[0]) if result else {}}
        except Exception as e:
            logger.error(f"Error running script {name}: {e}")
            return {'success': False, 'error': str(e)}

    def set_filter_limit(self, comment_substr: str, **props) -> Dict[str, Any]:
        """Set filter rule limits"""
        try:
            if not self._connection:
                self.connect()

            # Find rule by comment
            rules = tuple(self._connection('/ip/firewall/filter/print'))
            rule_id = None
            for rule in rules:
                if comment_substr in rule.get('comment', ''):
                    rule_id = rule['.id']
                    break

            if rule_id:
                self._connection('/ip/firewall/filter/set', numbers=rule_id, **props)
                return {'success': True}
            else:
                return {'success': False, 'error': f'Rule with comment containing "{comment_substr}" not found'}
        except Exception as e:
            logger.error(f"Error setting filter limit: {e}")
            return {'success': False, 'error': str(e)}

    def add_address_list(self, list_name: str, ip: str, timeout: Optional[str] = None) -> Dict[str, Any]:
        """Add IP to address list"""
        try:
            if not self._connection:
                self.connect()

            params = {'list': list_name, 'address': ip}
            if timeout:
                params['timeout'] = timeout

            result = tuple(self._connection('/ip/firewall/address-list/add', **params))
            return {'success': True, 'result': dict(result[0]) if result else {}}
        except Exception as e:
            logger.error(f"Error adding address to list: {e}")
            return {'success': False, 'error': str(e)}

    def remove_address_list(self, list_name: str, ip: str) -> Dict[str, Any]:
        """Remove IP from address list"""
        try:
            if not self._connection:
                self.connect()

            # Find entry
            entries = tuple(self._connection('/ip/firewall/address-list/print'))
            entry_id = None
            for entry in entries:
                if entry.get('list') == list_name and entry.get('address') == ip:
                    entry_id = entry['.id']
                    break

            if entry_id:
                self._connection('/ip/firewall/address-list/remove', numbers=entry_id)
                return {'success': True}
            else:
                return {'success': False, 'error': f'Address {ip} not found in list {list_name}'}
        except Exception as e:
            logger.error(f"Error removing address from list: {e}")
            return {'success': False, 'error': str(e)}

    def list_address_list(self, list_name: str) -> Dict[str, Any]:
        """List addresses in address list"""
        try:
            if not self._connection:
                self.connect()

            entries = tuple(self._connection('/ip/firewall/address-list/print'))
            addresses = [entry for entry in entries if entry.get('list') == list_name]
            return {'success': True, 'addresses': addresses}
        except Exception as e:
            logger.error(f"Error listing address list: {e}")
            return {'success': False, 'error': str(e)}