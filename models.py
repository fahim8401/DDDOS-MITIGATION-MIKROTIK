#!/usr/bin/env python3
"""
SQLAlchemy ORM models for multi-router DDoS monitoring system
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, Text, DateTime, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class Router(Base):
    """Router configuration model"""
    __tablename__ = 'routers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=8728)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    use_ssl = Column(Boolean, nullable=False, default=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)
    status = Column(String(50), default='unknown', index=True)
    
    # Relationships
    events = relationship('Event', back_populates='router', cascade='all, delete-orphan')
    blocked_ips = relationship('BlockedIP', back_populates='router', cascade='all, delete-orphan')
    stats = relationship('RouterStats', back_populates='router', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Router(id={self.id}, name='{self.name}', host='{self.host}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'use_ssl': self.use_ssl,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status
        }


class Event(Base):
    """DDoS event model"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    router_id = Column(Integer, ForeignKey('routers.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    attack_type = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=False, index=True)  # IPv6 max length
    target_ip = Column(String(45), nullable=False)
    packet_rate = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    action_taken = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    
    # Relationships
    router = relationship('Router', back_populates='events')
    notifications = relationship('NotificationLog', back_populates='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Event(id={self.id}, router_id={self.router_id}, source_ip='{self.source_ip}', severity='{self.severity}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'router_id': self.router_id,
            'router_name': self.router.name if self.router else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'attack_type': self.attack_type,
            'source_ip': self.source_ip,
            'target_ip': self.target_ip,
            'packet_rate': self.packet_rate,
            'severity': self.severity,
            'action_taken': self.action_taken,
            'details': self.details
        }


class BlockedIP(Base):
    """Blocked IP address model"""
    __tablename__ = 'blocked_ips'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    router_id = Column(Integer, ForeignKey('routers.id', ondelete='CASCADE'), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    blocked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    blocked_until = Column(DateTime, nullable=True)
    unblocked_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    
    # Relationships
    router = relationship('Router', back_populates='blocked_ips')
    
    def __repr__(self):
        return f"<BlockedIP(id={self.id}, router_id={self.router_id}, ip='{self.ip_address}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'router_id': self.router_id,
            'router_name': self.router.name if self.router else None,
            'ip_address': self.ip_address,
            'reason': self.reason,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'blocked_until': self.blocked_until.isoformat() if self.blocked_until else None,
            'unblocked_at': self.unblocked_at.isoformat() if self.unblocked_at else None,
            'status': self.status
        }


class User(Base):
    """User authentication model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default='viewer')
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses (without sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Setting(Base):
    """System settings model"""
    __tablename__ = 'settings'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RouterStats(Base):
    """Router statistics model"""
    __tablename__ = 'router_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    router_id = Column(Integer, ForeignKey('routers.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    cpu_load = Column(Float, nullable=True)
    memory_used = Column(Integer, nullable=True)
    memory_total = Column(Integer, nullable=True)
    uptime = Column(String(100), nullable=True)
    connection_count = Column(Integer, nullable=True)
    
    # Relationships
    router = relationship('Router', back_populates='stats')
    
    def __repr__(self):
        return f"<RouterStats(id={self.id}, router_id={self.router_id}, cpu_load={self.cpu_load})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'router_id': self.router_id,
            'router_name': self.router.name if self.router else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_load': self.cpu_load,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'uptime': self.uptime,
            'connection_count': self.connection_count
        }


class NotificationLog(Base):
    """Notification log model"""
    __tablename__ = 'notification_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete='SET NULL'), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    event = relationship('Event', back_populates='notifications')
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type='{self.notification_type}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'notification_type': self.notification_type,
            'recipient': self.recipient,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message
        }


class DatabaseManager:
    """Database manager for SQLAlchemy operations"""
    
    def __init__(self, database_url: str = 'sqlite:///ddos_events.db'):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database engine"""
        self.engine.dispose()


# Global database instance
_db_instance: Optional[DatabaseManager] = None


def get_database(database_url: str = 'sqlite:///ddos_events.db') -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(database_url)
        _db_instance.create_tables()
    return _db_instance
