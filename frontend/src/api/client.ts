import axios from 'axios'

// Runtime config is injected by /config.js at container startup.
// Local dev uses frontend/public/config.js defaults.
const runtimeConfig = window.__APP_CONFIG__
const baseURL = runtimeConfig?.API_URL ?? ''
const apiKey = runtimeConfig?.API_KEY ?? ''

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  },
})
