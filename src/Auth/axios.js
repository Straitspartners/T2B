
// src/api/axios.js
import axios from "axios";
// const baseURL = "http://localhost:5000"

const baseURL = "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net"

const api = axios.create({
  baseURL: baseURL, // Change to your backend URL
  timeout: 10000, // 10 seconds timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to handle errors globally
api.interceptors.response.use(
  response => response,
  error => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

export default api;