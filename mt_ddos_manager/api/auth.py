"""
Authentication and authorization for mt-ddos-manager
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.orm import Session
from .db import get_db
from .models import User


def role_required(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401

            db: Session = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 401

            # Role hierarchy: admin > operator > viewer
            role_hierarchy = {'viewer': 1, 'operator': 2, 'admin': 3}
            user_level = role_hierarchy.get(user.role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            if user_level < required_level:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator