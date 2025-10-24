"""
Database management for mt-ddos-manager
SQLAlchemy wrapper with SQLite
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mt_ddos.db')
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {},
    poolclass=StaticPool if DATABASE_URL.startswith('sqlite') else None,
    echo=False  # Set to True for debugging
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata
metadata = MetaData()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    from .models import User
    import bcrypt
    
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if admin_user:
            print("Default admin user already exists")
            return
        
        # Create default admin user
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = User(
            username='admin',
            password_hash=password_hash.decode('utf-8'),
            role='admin'
        )
        db.add(admin)
        db.commit()
        print("Default admin user created (username: admin, password: admin123)")
    except Exception as e:
        print(f"Error creating default admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_db():
    """Initialize database"""
    create_tables()
    create_default_admin()