import axios from 'axios';

// ✅ STEP 1: Sahi Server Address (Python Backend Port 5000)
const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// ✅ STEP 2: Admin API (Dashboard ke liye stats lana)
export const adminAPI = {
  getStats: async () => {
    try {
      // Ye Backend ke naye route '/admin/stats' se data layega
      const response = await api.get('/admin/stats');
      return response.data;
    } catch (error) {
      console.error("API Error (Stats):", error);
      // Agar error aaye to fake data bhejo taake site band na ho
      return { total_sales: 0, total_orders: 0, active_orders: 0 };
    }
  },
  
  // Agar future mein saare orders ki list chahiye ho
  getAllOrders: async () => {
    try {
      const response = await api.get('/orders');
      return response.data;
    } catch (error) {
      console.error("API Error (Orders):", error);
      return [];
    }
  }
};

// Agar purane components 'authAPI' dhund rahe hain to empty functions rakhe hain taake error na aaye
export const authAPI = {
  login: async () => console.log("Login not implemented for Simple Admin"),
  logout: async () => console.log("Logout"),
};

export default api;