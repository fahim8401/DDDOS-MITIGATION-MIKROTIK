import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const RouterDetail = () => {
  const { id } = useParams();
  const [router, setRouter] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRouter();
    fetchMetrics();
    fetchEvents();
  }, [id]);

  const fetchRouter = async () => {
    try {
      const response = await fetch(`/api/routers/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setRouter(data.router);
      }
    } catch (err) {
      console.error('Failed to fetch router:', err);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`/api/routers/${id}/metrics?hours=24`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await fetch(`/api/routers/${id}/events?limit=20`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events);
      }
    } catch (err) {
      console.error('Failed to fetch events:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-gray-600">Loading router details...</p>
        </div>
      </div>
    );
  }

  if (!router) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Router not found</p>
          <Link
            to="/routers"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200"
          >
            Back to routers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${
                router.status === 'online' ? 'bg-green-400' :
                router.status === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
              }`}></div>
              <h1 className="text-3xl font-bold text-gray-900">{router.name}</h1>
            </div>
            <Link
              to="/routers"
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Back to Routers
            </Link>
          </div>
          <p className="mt-2 text-gray-600">{router.host}:{router.port}</p>
        </div>

        {/* Router Info */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Router Information
            </h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    router.status === 'online' ? 'bg-green-100 text-green-800' :
                    router.status === 'offline' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {router.status}
                  </span>
                </dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Version</dt>
                <dd className="mt-1 text-sm text-gray-900">{router.version || 'Unknown'}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Last Seen</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {router.last_seen ? new Date(router.last_seen).toLocaleString() : 'Never'}
                </dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Identity</dt>
                <dd className="mt-1 text-sm text-gray-900">{router.identity || 'Unknown'}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Metrics Chart */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Traffic Metrics (Last 24 Hours)
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(timestamp) => new Date(timestamp).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                  />
                  <Line
                    type="monotone"
                    dataKey="cpu_usage"
                    stroke="#8884d8"
                    name="CPU Usage (%)"
                  />
                  <Line
                    type="monotone"
                    dataKey="memory_usage"
                    stroke="#82ca9d"
                    name="Memory Usage (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Recent Events */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Events
            </h3>
            <ul className="divide-y divide-gray-200">
              {events.map((event) => (
                <li key={event.id} className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-indigo-600 truncate">
                        {event.event_type}
                      </p>
                      <p className="ml-2 flex items-center text-sm text-gray-500">
                        {event.description}
                      </p>
                    </div>
                    <div className="ml-2 flex-shrink-0 flex">
                      <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        event.severity === 'high' ? 'bg-red-100 text-red-800' :
                        event.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {event.severity}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
            {events.length === 0 && (
              <p className="text-gray-500 text-center py-4">No events found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RouterDetail;