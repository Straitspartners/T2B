import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://127.0.0.1:8000",  // ✅ Changed from 5000
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ ADD THIS — attaches token to every request
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// your existing response interceptor (keep as is)
axiosInstance.interceptors.response.use(
  (response) => response,

  async (error) => {
    const config = error.config;

    if (
      config &&
      !config._retry &&
      (error.code === "ECONNABORTED" || !error.response)
    ) {
      config._retry = true;

      await new Promise((resolve) =>
        setTimeout(resolve, 3000)
      );

      return axiosInstance(config);
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;