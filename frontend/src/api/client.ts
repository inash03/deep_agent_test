import axios from 'axios'

// In Docker, VITE_API_URL is injected at build time as an absolute URL.
// In local dev, we use a relative base ('') so the Vite proxy handles /api/* routing.
const baseURL = import.meta.env.VITE_API_URL ?? ''
const apiKey = import.meta.env.VITE_API_KEY ?? ''

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  },
})
