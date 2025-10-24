"""
Authentication utilities for mt-ddos-manager
"""

from flask_jwt_extended import get_jwt
from flask import jsonify
from functools import wraps


def role_required(required_role):
    """
    Decorator to check if user has required role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            jwt_data = get_jwt()
            user_role = jwt_data.get('role', 'user')

            if user_role != required_role and user_role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to check if user is admin
    """
    return role_required('admin')(f)