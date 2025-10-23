"""
API tests for MikroTik DDoS Monitor
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def api_key():
    """API key for testing"""
    return 'changeme'


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'timestamp' in data


def test_status_without_api_key(client):
    """Test status endpoint without API key"""
    response = client.get('/api/status')
    assert response.status_code == 401


def test_status_with_api_key(client, api_key):
    """Test status endpoint with API key"""
    response = client.get(
        '/api/status',
        headers={'X-API-Key': api_key}
    )
    # May fail if not connected to router, but should not return 401
    assert response.status_code in [200, 500]


def test_get_events_without_api_key(client):
    """Test events endpoint without API key"""
    response = client.get('/api/events')
    assert response.status_code == 401


def test_get_events_with_api_key(client, api_key):
    """Test events endpoint with API key"""
    response = client.get(
        '/api/events',
        headers={'X-API-Key': api_key}
    )
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.get_json()
        assert 'events' in data
        assert isinstance(data['events'], list)


def test_block_ip_without_api_key(client):
    """Test block IP endpoint without API key"""
    response = client.post(
        '/api/blocked-ips',
        json={'ip_address': '1.2.3.4'}
    )
    assert response.status_code == 401


def test_block_ip_missing_data(client, api_key):
    """Test block IP endpoint with missing data"""
    response = client.post(
        '/api/blocked-ips',
        headers={'X-API-Key': api_key},
        json={}
    )
    assert response.status_code == 400


def test_404_handler(client):
    """Test 404 error handler"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
