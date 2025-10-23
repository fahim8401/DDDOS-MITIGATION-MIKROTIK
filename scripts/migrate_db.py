#!/usr/bin/env python3
"""
Database migration script for multi-router DDoS monitoring system
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_database

def run_migration(db_path: str = 'ddos_events.db', migration_file: str = 'migrations/001_initial.sql'):
    """Run database migration from SQL file"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Check if migration file exists
        if not os.path.exists(migration_file):
            logging.error(f"Migration file not found: {migration_file}")
            return False
        
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logging.info(f"Running migration from {migration_file}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute migration SQL
        try:
            cursor.executescript(migration_sql)
            conn.commit()
            logging.info("Migration completed successfully")
            
            # Verify tables were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logging.info(f"Tables in database: {', '.join(tables)}")
            
            return True
            
        except sqlite3.Error as e:
            logging.error(f"Error executing migration: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        return False


def init_database_with_orm(db_path: str = 'ddos_events.db'):
    """Initialize database using SQLAlchemy ORM models"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        logging.info(f"Initializing database with SQLAlchemy ORM: {db_path}")
        
        # Get database manager and create tables
        db_manager = get_database(f'sqlite:///{db_path}')
        
        logging.info("Database tables created successfully")
        
        # Insert default settings
        session = db_manager.get_session()
        try:
            from models import Setting
            
            default_settings = [
                Setting(key='check_interval', value='30', description='Monitoring check interval in seconds'),
                Setting(key='packet_threshold', value='10000', description='Packet rate threshold for detection'),
                Setting(key='auto_block_enabled', value='true', description='Enable automatic IP blocking'),
                Setting(key='block_duration', value='1h', description='Default block duration'),
                Setting(key='retention_days', value='30', description='Event retention period in days'),
                Setting(key='database_version', value='1', description='Database schema version'),
            ]
            
            for setting in default_settings:
                existing = session.query(Setting).filter_by(key=setting.key).first()
                if not existing:
                    session.add(setting)
            
            session.commit()
            logging.info("Default settings inserted")
            
        finally:
            session.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False


def add_sample_router(db_path: str = 'ddos_events.db'):
    """Add a sample router configuration for testing"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        from models import get_database, Router
        
        db_manager = get_database(f'sqlite:///{db_path}')
        session = db_manager.get_session()
        
        try:
            # Check if sample router already exists
            existing = session.query(Router).filter_by(name='Sample Router').first()
            
            if not existing:
                sample_router = Router(
                    name='Sample Router',
                    host='192.168.88.1',
                    port=8728,
                    username='admin',
                    password='changeme',
                    use_ssl=False,
                    enabled=False,  # Disabled by default for safety
                    status='unknown'
                )
                session.add(sample_router)
                session.commit()
                logging.info("Sample router added (disabled)")
            else:
                logging.info("Sample router already exists")
            
        finally:
            session.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to add sample router: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration tool')
    parser.add_argument('--db', default='ddos_events.db', help='Database file path')
    parser.add_argument('--migration', default='migrations/001_initial.sql', help='Migration file path')
    parser.add_argument('--orm', action='store_true', help='Use SQLAlchemy ORM to create tables')
    parser.add_argument('--add-sample', action='store_true', help='Add sample router configuration')
    
    args = parser.parse_args()
    
    if args.orm:
        success = init_database_with_orm(args.db)
    else:
        success = run_migration(args.db, args.migration)
    
    if success and args.add_sample:
        add_sample_router(args.db)
    
    sys.exit(0 if success else 1)
