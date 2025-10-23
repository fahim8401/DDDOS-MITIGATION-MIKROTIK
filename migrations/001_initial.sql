-- Initial database schema for multi-router DDoS monitoring system
-- Migration: 001_initial.sql
-- Created: 2025-10-23

-- Router configuration table
CREATE TABLE IF NOT EXISTS routers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    host TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 8728,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    use_ssl BOOLEAN NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen TEXT,
    status TEXT DEFAULT 'unknown'
);

-- Create index on router name and status
CREATE INDEX IF NOT EXISTS idx_routers_name ON routers(name);
CREATE INDEX IF NOT EXISTS idx_routers_status ON routers(status);

-- DDoS events table (enhanced with router_id)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    attack_type TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    target_ip TEXT NOT NULL,
    packet_rate INTEGER NOT NULL,
    severity TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (router_id) REFERENCES routers(id) ON DELETE CASCADE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source_ip ON events(source_ip);
CREATE INDEX IF NOT EXISTS idx_events_router_id ON events(router_id);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);

-- Blocked IPs table
CREATE TABLE IF NOT EXISTS blocked_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    reason TEXT NOT NULL,
    blocked_at TEXT NOT NULL DEFAULT (datetime('now')),
    blocked_until TEXT,
    unblocked_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (router_id) REFERENCES routers(id) ON DELETE CASCADE,
    UNIQUE(router_id, ip_address)
);

-- Create indexes for blocked IPs
CREATE INDEX IF NOT EXISTS idx_blocked_ips_router ON blocked_ips(router_id);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_address ON blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_status ON blocked_ips(status);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'viewer',
    api_key TEXT UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login TEXT
);

-- Create index on username and api_key
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);

-- System settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Router statistics table
CREATE TABLE IF NOT EXISTS router_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    cpu_load REAL,
    memory_used INTEGER,
    memory_total INTEGER,
    uptime TEXT,
    connection_count INTEGER,
    FOREIGN KEY (router_id) REFERENCES routers(id) ON DELETE CASCADE
);

-- Create indexes for router stats
CREATE INDEX IF NOT EXISTS idx_router_stats_router ON router_stats(router_id);
CREATE INDEX IF NOT EXISTS idx_router_stats_timestamp ON router_stats(timestamp);

-- Notification log table
CREATE TABLE IF NOT EXISTS notification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    notification_type TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    error_message TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL
);

-- Create index on notification log
CREATE INDEX IF NOT EXISTS idx_notification_log_event ON notification_log(event_id);
CREATE INDEX IF NOT EXISTS idx_notification_log_status ON notification_log(status);

-- Insert default system settings
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('check_interval', '30', 'Monitoring check interval in seconds'),
    ('packet_threshold', '10000', 'Packet rate threshold for detection'),
    ('auto_block_enabled', 'true', 'Enable automatic IP blocking'),
    ('block_duration', '1h', 'Default block duration'),
    ('retention_days', '30', 'Event retention period in days'),
    ('database_version', '1', 'Database schema version');

-- Create a view for active events summary
CREATE VIEW IF NOT EXISTS active_events_summary AS
SELECT 
    r.name as router_name,
    e.severity,
    COUNT(*) as event_count,
    MIN(e.timestamp) as first_seen,
    MAX(e.timestamp) as last_seen
FROM events e
JOIN routers r ON e.router_id = r.id
WHERE e.timestamp >= datetime('now', '-24 hours')
GROUP BY r.id, e.severity;

-- Create a view for blocked IPs summary
CREATE VIEW IF NOT EXISTS blocked_ips_summary AS
SELECT 
    r.name as router_name,
    COUNT(*) as blocked_count,
    MIN(bi.blocked_at) as oldest_block,
    MAX(bi.blocked_at) as newest_block
FROM blocked_ips bi
JOIN routers r ON bi.router_id = r.id
WHERE bi.status = 'active'
GROUP BY r.id;
