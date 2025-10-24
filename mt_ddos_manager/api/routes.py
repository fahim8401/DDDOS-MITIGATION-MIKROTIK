"""
API routes for mt-ddos-manager
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Router, RouterConfig, User, Event, Metric, AddressList, ActionHistory
import json
import bcrypt
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'mt-ddos-manager-api'
    })


# Authentication
@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    db: Session = next(get_db())
    user = db.query(User).filter(User.username == data['username']).first()
    
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    # Create JWT token
    access_token = create_access_token(identity=user.username, additional_claims={'role': user.role})
    
    return jsonify({
        'token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    })


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """User registration"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    db: Session = next(get_db())
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409
    
    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        username=data['username'],
        password_hash=password_hash.decode('utf-8'),
        role=data.get('role', 'admin')  # Default to admin
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return jsonify({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    }), 201


# Dashboard
@api_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    db: Session = next(get_db())
    
    # Get router counts
    total_routers = db.query(Router).count()
    active_routers = db.query(Router).filter(Router.enabled == True).count()
    
    # Get event counts
    total_events = db.query(Event).count()
    
    # Get active mitigations (events with high severity in last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    active_mitigations = db.query(Event).filter(
        Event.created_at >= yesterday,
        Event.severity.in_(['high', 'critical'])
    ).count()
    
    return jsonify({
        'totalRouters': total_routers,
        'activeRouters': active_routers,
        'totalEvents': total_events,
        'activeMitigations': active_mitigations
    })


# Routers CRUD
@api_bp.route('/routers', methods=['GET'])
@jwt_required()
def get_routers():
    """Get all routers"""
    db: Session = next(get_db())
    routers = db.query(Router).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'host': r.host,
        'port': r.port,
        'use_ssl': r.use_ssl,
        'enabled': r.enabled,
        'tags': r.tags,
        'last_seen': r.last_seen.isoformat() if r.last_seen else None
    } for r in routers])


@api_bp.route('/routers', methods=['POST'])
@jwt_required()
def create_router():
    """Create new router"""
    data = request.get_json()
    db: Session = next(get_db())

    router = Router(
        name=data['name'],
        host=data['host'],
        port=data['port'],
        username=data['username'],
        password=data['password'],
        use_ssl=data.get('use_ssl', False),
        enabled=data.get('enabled', True),
        tags=data.get('tags')
    )

    db.add(router)
    db.commit()
    db.refresh(router)

    return jsonify({'id': router.id}), 201


@api_bp.route('/routers/<int:router_id>', methods=['PUT'])
@jwt_required()
def update_router(router_id):
    """Update router"""
    data = request.get_json()
    db: Session = next(get_db())

    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        return jsonify({'error': 'Router not found'}), 404

    for key, value in data.items():
        if hasattr(router, key):
            setattr(router, key, value)

    db.commit()
    return jsonify({'message': 'Router updated'})


@api_bp.route('/routers/<int:router_id>', methods=['DELETE'])
@jwt_required()
def delete_router(router_id):
    """Delete router"""
    db: Session = next(get_db())

    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        return jsonify({'error': 'Router not found'}), 404

    db.delete(router)
    db.commit()
    return jsonify({'message': 'Router deleted'})


# Router actions
@api_bp.route('/routers/<int:router_id>/actions/tighten', methods=['POST'])
@jwt_required()
def tighten_router(router_id):
    """Tighten router security"""
    # Implementation would call monitor worker
    return jsonify({'message': 'Tighten action initiated'})


@api_bp.route('/routers/<int:router_id>/actions/restore', methods=['POST'])
@jwt_required()
def restore_router(router_id):
    """Restore router to normal"""
    # Implementation would call monitor worker
    return jsonify({'message': 'Restore action initiated'})


@api_bp.route('/routers/<int:router_id>/address-lists/add', methods=['POST'])
@jwt_required()
def add_address_list(router_id):
    """Add IP to address list"""
    data = request.get_json()
    db: Session = next(get_db())

    addr_list = AddressList(
        router_id=router_id,
        list_name=data['list_name'],
        address=data['address'],
        timeout=data.get('timeout'),
        added_by=get_jwt_identity()
    )

    db.add(addr_list)
    db.commit()

    # Log action
    action = ActionHistory(
        router_id=router_id,
        action='add_address_list',
        initiated_by=get_jwt_identity(),
        detail=json.dumps(data)
    )
    db.add(action)
    db.commit()

    return jsonify({'message': 'Address added to list'})


@api_bp.route('/routers/<int:router_id>/address-lists/remove', methods=['POST'])
@jwt_required()
def remove_address_list(router_id):
    """Remove IP from address list"""
    data = request.get_json()
    db: Session = next(get_db())

    addr_list = db.query(AddressList).filter(
        AddressList.router_id == router_id,
        AddressList.address == data['address']
    ).first()

    if addr_list:
        db.delete(addr_list)
        db.commit()

        # Log action
        action = ActionHistory(
            router_id=router_id,
            action='remove_address_list',
            initiated_by=get_jwt_identity(),
            detail=json.dumps(data)
        )
        db.add(action)
        db.commit()

    return jsonify({'message': 'Address removed from list'})


# Global actions
@api_bp.route('/actions/tighten', methods=['POST'])
@jwt_required()
def global_tighten():
    """Tighten multiple routers"""
    data = request.get_json()
    router_ids = data.get('router_ids', [])
    # Implementation would iterate over routers
    return jsonify({'message': f'Tighten initiated for routers: {router_ids}'})


# Metrics
@api_bp.route('/routers/<int:router_id>/metrics', methods=['GET'])
@jwt_required()
def get_router_metrics(router_id):
    """Get metrics for router"""
    db: Session = next(get_db())
    metrics = db.query(Metric).filter(Metric.router_id == router_id).order_by(Metric.ts.desc()).limit(100).all()
    return jsonify([{
        'ts': m.ts.isoformat(),
        'total_connections': m.total_connections,
        'new_connections': m.new_connections,
        'packets_in': m.packets_in,
        'packets_out': m.packets_out,
        'bytes_in': m.bytes_in,
        'bytes_out': m.bytes_out
    } for m in metrics])


@api_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_global_metrics():
    """Get global metrics"""
    db: Session = next(get_db())
    # Aggregate metrics across all routers
    metrics = db.query(Metric).order_by(Metric.ts.desc()).limit(100).all()
    return jsonify([{
        'router_id': m.router_id,
        'ts': m.ts.isoformat(),
        'total_connections': m.total_connections,
        'new_connections': m.new_connections
    } for m in metrics])


# Events
@api_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    """Get events"""
    db: Session = next(get_db())
    events = db.query(Event).order_by(Event.created_at.desc()).limit(100).all()
    return jsonify([{
        'id': e.id,
        'router_id': e.router_id,
        'type': e.type,
        'detail': e.detail,
        'meta': json.loads(e.meta) if e.meta else None,
        'created_at': e.created_at.isoformat(),
        'severity': e.severity
    } for e in events])


# Users
@api_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users"""
    db: Session = next(get_db())
    users = db.query(User).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else None,
        'last_login': u.last_login.isoformat() if u.last_login else None
    } for u in users])


# Health
@api_bp.route('/routers/<int:router_id>/health', methods=['GET'])
@jwt_required()
def get_router_health(router_id):
    """Get router health status"""
    db: Session = next(get_db())
    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        return jsonify({'error': 'Router not found'}), 404

    # Simple health check - in real implementation, would test connection
    health = {
        'router_id': router_id,
        'status': 'healthy' if router.enabled else 'disabled',
        'last_seen': router.last_seen.isoformat() if router.last_seen else None
    }
    return jsonify(health)