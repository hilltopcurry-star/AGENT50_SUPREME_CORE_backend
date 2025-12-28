import React, { useEffect, useState } from 'react';
import { adminAPI } from '../services/api';
import './Dashboard.css'; // Design wali file import ki

const Dashboard = () => {
  // Stats ke liye state banayi
  const [stats, setStats] = useState({ total_sales: 0, total_orders: 0, active_orders: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Backend se Stats mangwaye
      const data = await adminAPI.getStats();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data", error);
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <h1>🚀 Agent 50 Admin Panel</h1>
      
      {loading ? (
        <div style={{textAlign: 'center', marginTop: '50px'}}>Loading Stats...</div>
      ) : (
        /* Stats Cards Section */
        <div className="stats-grid">
          
          {/* Card 1: TOTAL SALES (Green) */}
          <div className="card green">
            <h3>💰 Total Sales</h3>
            <p>Rs {stats.total_sales}</p>
          </div>
          
          {/* Card 2: TOTAL ORDERS (Blue) */}
          <div className="card blue">
            <h3>📦 Total Orders</h3>
            <p>{stats.total_orders}</p>
          </div>

          {/* Card 3: ACTIVE ORDERS (Orange) */}
          <div className="card orange">
            <h3>🔥 Active Orders</h3>
            <p>{stats.active_orders}</p>
          </div>
          
        </div>
      )}
    </div>
  );
};

export default Dashboard;