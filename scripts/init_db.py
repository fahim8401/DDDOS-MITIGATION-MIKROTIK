#!/usr/bin/env python3
"""
Initialize database and create admin user
"""

import os
import sys
import bcrypt
from sqlalchemy.orm import Session

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mt_ddos_manager.db import init_db, get_db
from mt_ddos_manager.models import User


def create_admin_user(password: str):
    """Create admin user"""
    db: Session = next(get_db())

    # Check if admin exists
    admin = db.query(User).filter(User.username == 'admin').first()
    if admin:
        print("Admin user already exists")
        return

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    admin = User(
        username='admin',
        password_hash=password_hash.decode('utf-8'),
        role='admin',
        enabled=True
    )

    db.add(admin)
    db.commit()
    print("Admin user created")


def main():
    """Main function"""
    # Initialize database
    init_db()
    print("Database initialized")

    # Create admin user
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    create_admin_user(password)
    print(f"Admin user created with password: {password}")


if __name__ == '__main__':
    main()