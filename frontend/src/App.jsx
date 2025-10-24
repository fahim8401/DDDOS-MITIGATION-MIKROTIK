import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Routers from './pages/Routers'
import RouterDetail from './pages/RouterDetail'
import Users from './pages/Users'
import Layout from './components/Layout'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="routers" element={<Routers />} />
          <Route path="routers/:id" element={<RouterDetail />} />
          <Route path="users" element={<Users />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App