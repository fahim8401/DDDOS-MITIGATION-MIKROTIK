import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Routers = () => {
  const [routers, setRouters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRouters();
  }, []);

  const fetchRouters = async () => {
    try {
      const response = await fetch('/api/routers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setRouters(data.routers);
      }
    } catch (err) {
      console.error('Failed to fetch routers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (routerId) => {
    if (!confirm('Are you sure you want to delete this router?')) return;

    try {
      const response = await fetch(`/api/routers/${routerId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        setRouters(routers.filter(router => router.id !== routerId));
      }
    } catch (err) {
      console.error('Failed to delete router:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-gray-600">Loading routers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Routers</h1>
          <Link
            to="/routers/new"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Add Router
          </Link>
        </div>

        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {routers.map((router) => (
              <li key={router.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-3 ${
                        router.status === 'online' ? 'bg-green-400' :
                        router.status === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          {router.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {router.host}:{router.port}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        router.status === 'online' ? 'bg-green-100 text-green-800' :
                        router.status === 'offline' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {router.status}
                      </span>
                      <Link
                        to={`/routers/${router.id}`}
                        className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(router.id)}
                        className="text-red-600 hover:text-red-900 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        Last seen: {router.last_seen ? new Date(router.last_seen).toLocaleString() : 'Never'}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <p>Version: {router.version || 'Unknown'}</p>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          {routers.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No routers configured yet.</p>
              <Link
                to="/routers/new"
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200"
              >
                Add your first router
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Routers;