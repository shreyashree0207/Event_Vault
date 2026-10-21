import { readSession } from './sessionStorage';

/**
 * Central API Client Abstraction
 * 
 * Supports switching between Mock Local Execution (Frontend Only phase)
 * and FastAPI Backend integration (http://localhost:8000 via VITE_API_BASE_URL).
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Toggle this parameter or override to use FastAPI when available
export const USE_REAL_BACKEND = true;

async function request(endpoint, options = {}) {
  let response;
  const headers = new Headers(options.headers);
  const accessToken = readSession()?.accessToken;
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Unable to connect to Event Vault API at ${API_BASE_URL}. ` +
        'Verify that FastAPI is running and VITE_API_BASE_URL is correct.'
      );
    }
    throw error;
  }

  const responseText = await response.text();
  let responseData = null;
  if (responseText) {
    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = responseText;
    }
  }

  if (!response.ok) {
    const detail = typeof responseData === 'object'
      ? responseData?.detail || responseData?.message
      : responseData;
    const message = typeof detail === 'string'
      ? detail
      : detail
        ? JSON.stringify(detail)
        : response.statusText;
    throw new Error(`API request failed (${response.status}): ${message}`);
  }

  return responseData;
}

async function download(endpoint) {
  const headers = new Headers();
  const accessToken = readSession()?.accessToken;
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Unable to connect to Event Vault API at ${API_BASE_URL}. ` +
        'Verify that FastAPI is running and VITE_API_BASE_URL is correct.'
      );
    }
    throw error;
  }

  if (!response.ok) {
    const responseData = await response.json().catch(() => null);
    throw new Error(
      responseData?.detail || `Ticket download failed (${response.status}).`
    );
  }
  return response.blob();
}

export const apiClient = {
  async get(endpoint) {
    if (USE_REAL_BACKEND) {
      return request(endpoint);
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  },

  async post(endpoint, data) {
    if (USE_REAL_BACKEND) {
      return request(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  },

  async delete(endpoint, options = {}) {
    if (USE_REAL_BACKEND) {
      return request(endpoint, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(options.data),
      });
    }
    throw new Error("Backend not configured. Service should fall back to mock data.");
  }
},
async download(endpoint) {
  if (USE_REAL_BACKEND) {
    return download(endpoint);
  }
  throw new Error("Ticket downloads require the FastAPI backend.");
};
