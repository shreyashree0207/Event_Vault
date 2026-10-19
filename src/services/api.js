/**
 * Central API Client Abstraction
 * 
 * Supports switching between Mock Local Execution (Frontend Only phase)
 * and FastAPI Backend integration (http://localhost:8000 via VITE_API_BASE_URL).
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Toggle this parameter or override to use FastAPI when available
export const USE_REAL_BACKEND = true;

export const apiClient = {
  async get(endpoint) {
    if (USE_REAL_BACKEND) {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
      }
      return response.json();
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  },

  async post(endpoint, data) {
    if (USE_REAL_BACKEND) {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
      }
      return response.json();
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  },

  async delete(endpoint, options = {}) {
    if (USE_REAL_BACKEND) {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(options.data),
      });
      if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
      }
      return response.json();
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  }
};
