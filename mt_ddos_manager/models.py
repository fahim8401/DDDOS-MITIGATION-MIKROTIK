"""
SQLAlchemy models for mt-ddos-manager
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


class Router(Base):
    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    use_ssl = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    tags = Column(Text)  # comma-separated
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime)

    # Relationships
    configs = relationship("RouterConfig", back_populates="router", uselist=False)
    events = relationship("Event", back_populates="router")
    metrics = relationship("Metric", back_populates="router")
    address_lists = relationship("AddressList", back_populates="router")
    actions_history = relationship("ActionHistory", back_populates="router")


class RouterConfig(Base):
    __tablename__ = "router_configs"

    id = Column(Integer, primary_key=True)
    router_id = Column(Integer, ForeignKey("routers.id"), nullable=False)
    poll_interval = Column(Integer)
    conn_attack_threshold = Column(Integer)
    new_conn_rate_threshold = Column(Integer)
    per_src_new_conn_limit = Column(Integer)
    per_src_window = Column(Integer)
    tighten_cooldown = Column(Integer)
    tighten_limits = Column(Text)  # JSON
    restore_limits = Column(Text)  # JSON
    notification_prefs = Column(Text)  # JSON
    updated_at = Column(DateTime)

    # Relationships
    router = relationship("Router", back_populates="configs")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, CheckConstraint("role IN ('admin','operator','viewer')"), default='viewer')
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    address_lists = relationship("AddressList", back_populates="added_by_user")
    actions_history = relationship("ActionHistory", back_populates="initiated_by_user")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id"), nullable=True)
    type = Column(String)
    detail = Column(Text)
    meta = Column(Text)  # JSON
    created_at = Column(DateTime, default=func.now())
    severity = Column(String)

    # Relationships
    router = relationship("Router", back_populates="events")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id"))
    ts = Column(DateTime, default=func.now())
    total_connections = Column(Integer)
    new_connections = Column(Integer)
    packets_in = Column(Integer)
    packets_out = Column(Integer)
    bytes_in = Column(Integer)
    bytes_out = Column(Integer)

    # Relationships
    router = relationship("Router", back_populates="metrics")


class AddressList(Base):
    __tablename__ = "address_lists"

    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id"), nullable=True)
    list_name = Column(String)
    address = Column(String)
    timeout = Column(String)
    added_by = Column(Integer, ForeignKey("users.id"))
    added_at = Column(DateTime, default=func.now())

    # Relationships
    router = relationship("Router", back_populates="address_lists")
    added_by_user = relationship("User", back_populates="address_lists")


class ActionHistory(Base):
    __tablename__ = "actions_history"

    id = Column(Integer, primary_key=True, index=True)
    router_id = Column(Integer, ForeignKey("routers.id"), nullable=True)
    action = Column(String)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    detail = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    router = relationship("Router", back_populates="actions_history")
    initiated_by_user = relationship("User", back_populates="actions_history")