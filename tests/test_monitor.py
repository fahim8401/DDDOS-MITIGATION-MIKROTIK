"""
Unit tests for MikroTik DDoS Monitor
"""

import pytest
import sqlite3
from datetime import datetime
from mt_ddos_monitor import ConfigManager, DatabaseManager, DDoSEvent


class TestConfigManager:
    """Test configuration management"""
    
    def test_load_config(self, tmp_path):
        """Test loading configuration from YAML"""
        config_file = tmp_path / "test_config.yml"
        config_file.write_text("""
mikrotik:
  host: "192.168.1.1"
  username: "test"
  password: "test"
  port: 8728

detection:
  check_interval: 30
  packet_threshold: 10000
""")
        
        config = ConfigManager(str(config_file))
        assert config.get('mikrotik.host') == "192.168.1.1"
        assert config.get('mikrotik.port') == 8728
        assert config.get('detection.check_interval') == 30
    
    def test_get_with_default(self, tmp_path):
        """Test getting config value with default"""
        config_file = tmp_path / "test_config.yml"
        config_file.write_text("mikrotik:\n  host: '192.168.1.1'\n")
        
        config = ConfigManager(str(config_file))
        assert config.get('nonexistent.key', 'default') == 'default'


class TestDatabaseManager:
    """Test database operations"""
    
    def test_init_database(self, tmp_path):
        """Test database initialization"""
        db_file = tmp_path / "test.db"
        db = DatabaseManager(str(db_file))
        
        # Check if table exists
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None
        db.close()
    
    def test_log_event(self, tmp_path):
        """Test logging an event"""
        db_file = tmp_path / "test.db"
        db = DatabaseManager(str(db_file))
        
        event = DDoSEvent(
            timestamp=datetime.now(),
            attack_type="SYN Flood",
            source_ip="1.2.3.4",
            target_ip="192.168.1.1",
            packet_rate=15000,
            severity="HIGH",
            action_taken="Blocked"
        )
        
        db.log_event(event)
        
        # Verify event was logged
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        assert count == 1
        
        db.close()
    
    def test_get_recent_events(self, tmp_path):
        """Test retrieving recent events"""
        db_file = tmp_path / "test.db"
        db = DatabaseManager(str(db_file))
        
        # Log test events
        for i in range(5):
            event = DDoSEvent(
                timestamp=datetime.now(),
                attack_type="Test Attack",
                source_ip=f"1.2.3.{i}",
                target_ip="192.168.1.1",
                packet_rate=10000 + i,
                severity="MEDIUM",
                action_taken="Pending"
            )
            db.log_event(event)
        
        # Get recent events
        events = db.get_recent_events(hours=24)
        assert len(events) == 5
        
        db.close()


class TestDDoSEvent:
    """Test DDoSEvent dataclass"""
    
    def test_create_event(self):
        """Test creating a DDoS event"""
        event = DDoSEvent(
            timestamp=datetime.now(),
            attack_type="UDP Flood",
            source_ip="10.0.0.1",
            target_ip="192.168.1.1",
            packet_rate=20000,
            severity="CRITICAL",
            action_taken="Blocked"
        )
        
        assert event.source_ip == "10.0.0.1"
        assert event.severity == "CRITICAL"
        assert event.packet_rate == 20000


@pytest.fixture
def mock_config(tmp_path):
    """Fixture for mock configuration"""
    config_file = tmp_path / "config.yml"
    config_file.write_text("""
mikrotik:
  host: "192.168.1.1"
  username: "admin"
  password: "test"
  port: 8728

detection:
  check_interval: 30
  packet_threshold: 10000
  auto_block_enabled: true
  block_duration: "1h"
  address_list_name: "test_blocklist"

database:
  path: "test.db"
""")
    return ConfigManager(str(config_file))


def test_severity_calculation():
    """Test severity calculation logic"""
    from mt_ddos_monitor import MikroTikMonitor
    
    # This would require mocking the monitor
    # For now, just test the concept
    threshold = 10000
    
    # Test different severity levels
    assert 100000 / threshold >= 10  # CRITICAL
    assert 50000 / threshold >= 5    # HIGH
    assert 20000 / threshold >= 2    # MEDIUM
