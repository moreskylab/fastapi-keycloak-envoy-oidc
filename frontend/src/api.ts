/**
 * API client with automatic Bearer token injection.
 *
 * Security: Token is fetched from the in-memory Keycloak instance
 * on every request — never read from storage.
 */

import axios, { type AxiosInstance, type AxiosResponse } from "axios";
import { getToken } from "./auth";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || window.location.origin;

/**
 * Create an Axios instance with Bearer token interceptor.
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE,
    timeout: 15000,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Request interceptor: inject Bearer token from memory
  client.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor: handle auth errors
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        console.warn("API returned 401 — token may be expired");
      }
      return Promise.reject(error);
    }
  );

  return client;
}

const apiClient = createApiClient();

/**
 * Call a GET endpoint and return the response data.
 */
export async function apiGet<T = Record<string, unknown>>(
  path: string
): Promise<T> {
  const response = await apiClient.get<T>(path);
  return response.data;
}
