-- MikroTik DDoS Monitor Multi-Router Database Schema
-- SQLite migration file: 001_initial.sql

-- Routers table
CREATE TABLE routers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    use_ssl BOOLEAN DEFAULT 0,
    enabled BOOLEAN DEFAULT 1,
    tags TEXT,  -- comma-separated
    last_seen DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Router configurations table
CREATE TABLE router_configs (
    id INTEGER PRIMARY KEY,
    router_id INTEGER REFERENCES routers(id) ON DELETE CASCADE,
    poll_interval INTEGER,
    conn_attack_threshold INTEGER,
    new_conn_rate_threshold INTEGER,
    per_src_new_conn_limit INTEGER,
    per_src_window INTEGER,
    tighten_cooldown INTEGER,
    tighten_limits TEXT,  -- JSON
    restore_limits TEXT,  -- JSON
    notification_prefs TEXT,  -- JSON
    updated_at DATETIME
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    role TEXT CHECK(role IN ('admin','operator','viewer')) DEFAULT 'viewer',
    created_at DATETIME,
    last_login DATETIME
);

-- Events table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NULL,
    type TEXT,
    detail TEXT,
    meta TEXT,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    severity TEXT
);

-- Metrics table
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_connections INTEGER,
    new_connections INTEGER,
    packets_in INTEGER,
    packets_out INTEGER,
    bytes_in INTEGER,
    bytes_out INTEGER
);

-- Address lists table
CREATE TABLE address_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NULL,
    list_name TEXT,
    address TEXT,
    timeout TEXT,
    added_by INTEGER REFERENCES users(id),
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Actions history table
CREATE TABLE actions_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    router_id INTEGER NULL,
    action TEXT,
    initiated_by INTEGER REFERENCES users(id) NULL,
    detail TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_routers_enabled ON routers(enabled);
CREATE INDEX idx_router_configs_router_id ON router_configs(router_id);
CREATE INDEX idx_events_router_id ON events(router_id);
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_metrics_router_id ON metrics(router_id);
CREATE INDEX idx_metrics_ts ON metrics(ts);
CREATE INDEX idx_address_lists_router_id ON address_lists(router_id);
CREATE INDEX idx_actions_history_router_id ON actions_history(router_id);
CREATE INDEX idx_actions_history_created_at ON actions_history(created_at);
