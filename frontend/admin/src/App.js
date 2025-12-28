import React, { useState, useEffect } from 'react';
import './App.css';

// ✅ SERVER ADDRESS (Localhost kyunki ye Laptop par hi chal raha hai)
const API_URL = "http://localhost:5000";

function App() {
  const [stats, setStats] = useState({
    total_sales: 0,
    total_orders: 0,
    active_orders: 0
  });

  const fetchStats = async () => {
    try {
      // console.log("Fetching Admin Stats...");
      const response = await fetch(`${API_URL}/admin/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  useEffect(() => {
    fetchStats();
    // Har 5 second mein refresh karo
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🍕 Restaurant Admin Panel</h1>
        <p>Live Control Room</p>
      </header>

      <div className="dashboard">
        <div className="card blue">
          <h3>Total Orders</h3>
          <h1>{stats.total_orders}</h1>
        </div>
        <div className="card green">
          <h3>Total Sales</h3>
          <h1>Rs {stats.total_sales}</h1>
        </div>
        <div className="card orange">
          <h3>Active Orders</h3>
          <h1>{stats.active_orders}</h1>
        </div>
      </div>

      <div className="recent-orders">
        <h2>Live Database Status 🟢</h2>
        <div className="status-bar">
          System Online • Database Connected • Tracking Sales
        </div>
      </div>
    </div>
  );
}

export default App;