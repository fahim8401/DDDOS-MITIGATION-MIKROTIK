#!/usr/bin/env python3
"""
Tests for multi-router functionality
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_database, Router, Event, BlockedIP, RouterStats, DatabaseManager
from mt_ddos_manager import RouterClient, MonitorWorker, ConfigManager
import models


class TestRouterModel:
    """Test Router model"""
    
    def test_create_router(self):
        """Test creating a router"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = get_database(f'sqlite:///{db_path}')
            db.create_tables()  # Create tables before using
            session = db.get_session()
            
            router = Router(
                name='Test Router',
                host='192.168.1.1',
                port=8728,
                username='admin',
                password='test',
                use_ssl=False,
                enabled=True
            )
            
            session.add(router)
            session.commit()
            
            # Verify router was created
            saved_router = session.query(Router).filter_by(name='Test Router').first()
            assert saved_router is not None
            assert saved_router.host == '192.168.1.1'
            assert saved_router.port == 8728
            assert saved_router.enabled is True
            
            session.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_router_to_dict(self):
        """Test router to_dict method"""
        router = Router(
            id=1,
            name='Test Router',
            host='192.168.1.1',
            port=8728,
            username='admin',
            password='secret',
            use_ssl=False,
            enabled=True,
            status='connected'
        )
        
        router_dict = router.to_dict()
        
        assert router_dict['id'] == 1
        assert router_dict['name'] == 'Test Router'
        assert router_dict['host'] == '192.168.1.1'
        assert router_dict['status'] == 'connected'
        assert 'password' not in str(router_dict) or router_dict.get('password') == 'secret'


class TestEventModel:
    """Test Event model"""
    
    def test_create_event(self):
        """Test creating an event"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Reset global instance for fresh database
            models._db_instance = None
            db = get_database(f'sqlite:///{db_path}')
            db.create_tables()  # Create tables before using
            session = db.get_session()
            
            # Create router first
            router = Router(
                name='Test Router',
                host='192.168.1.1',
                username='admin',
                password='test',
                enabled=True
            )
            session.add(router)
            session.commit()
            
            # Create event
            event = Event(
                router_id=router.id,
                timestamp=datetime.now(),
                attack_type='SYN Flood',
                source_ip='1.2.3.4',
                target_ip='192.168.1.1',
                packet_rate=15000,
                severity='HIGH',
                action_taken='Blocked'
            )
            
            session.add(event)
            session.commit()
            
            # Verify event was created
            saved_event = session.query(Event).filter_by(source_ip='1.2.3.4').first()
            assert saved_event is not None
            assert saved_event.router_id == router.id
            assert saved_event.attack_type == 'SYN Flood'
            assert saved_event.severity == 'HIGH'
            
            session.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestBlockedIPModel:
    """Test BlockedIP model"""
    
    def test_create_blocked_ip(self):
        """Test creating a blocked IP"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Reset global instance for fresh database
            models._db_instance = None
            db = get_database(f'sqlite:///{db_path}')
            db.create_tables()  # Create tables before using
            session = db.get_session()
            
            # Create router first
            router = Router(
                name='Test Router',
                host='192.168.1.1',
                username='admin',
                password='test',
                enabled=True
            )
            session.add(router)
            session.commit()
            
            # Create blocked IP
            blocked = BlockedIP(
                router_id=router.id,
                ip_address='1.2.3.4',
                reason='DDoS Attack',
                blocked_at=datetime.now(),
                status='active'
            )
            
            session.add(blocked)
            session.commit()
            
            # Verify blocked IP was created
            saved_blocked = session.query(BlockedIP).filter_by(ip_address='1.2.3.4').first()
            assert saved_blocked is not None
            assert saved_blocked.router_id == router.id
            assert saved_blocked.reason == 'DDoS Attack'
            assert saved_blocked.status == 'active'
            
            session.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestRouterClient:
    """Test RouterClient class"""
    
    def test_router_client_creation(self):
        """Test creating a RouterClient"""
        router = Router(
            id=1,
            name='Test Router',
            host='192.168.1.1',
            port=8728,
            username='admin',
            password='test',
            enabled=True
        )
        
        client = RouterClient(router)
        
        assert client.router == router
        assert client.api is None
        assert client.connected is False
        assert client.last_error is None


class TestConfigManager:
    """Test ConfigManager with multi-router support"""
    
    def test_load_config(self, tmp_path):
        """Test loading configuration"""
        config_file = tmp_path / "test_config.yml"
        config_file.write_text("""
detection:
  check_interval: 30
  packet_threshold: 10000
  auto_block_enabled: true
  
database:
  path: test.db
""")
        
        config = ConfigManager(str(config_file))
        
        assert config.get('detection.check_interval') == 30
        assert config.get('detection.packet_threshold') == 10000
        assert config.get('detection.auto_block_enabled') is True
        assert config.get('database.path') == 'test.db'


def test_database_relationships():
    """Test database relationships between models"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Reset global instance for fresh database
        models._db_instance = None
        db = get_database(f'sqlite:///{db_path}')
        db.create_tables()  # Create tables before using
        session = db.get_session()
        
        # Create router
        router = Router(
            name='Test Router',
            host='192.168.1.1',
            username='admin',
            password='test',
            enabled=True
        )
        session.add(router)
        session.commit()
        
        # Create event
        event = Event(
            router_id=router.id,
            timestamp=datetime.now(),
            attack_type='Test Attack',
            source_ip='1.2.3.4',
            target_ip='192.168.1.1',
            packet_rate=1000,
            severity='LOW',
            action_taken='None'
        )
        session.add(event)
        
        # Create blocked IP
        blocked = BlockedIP(
            router_id=router.id,
            ip_address='1.2.3.4',
            reason='Test',
            status='active'
        )
        session.add(blocked)
        session.commit()
        
        # Test relationships
        router_check = session.query(Router).filter_by(id=router.id).first()
        assert len(router_check.events) == 1
        assert len(router_check.blocked_ips) == 1
        assert router_check.events[0].source_ip == '1.2.3.4'
        assert router_check.blocked_ips[0].ip_address == '1.2.3.4'
        
        session.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
