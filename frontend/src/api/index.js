import axios from 'axios'

/**
 * API base URL:
 * - Railway / simulate.nodera.app: one service runs Vite (3000) + Flask (5001). Only 3000 is public.
 *   Browser must call same-origin `/api/...` so Vite proxies to Flask. `import.meta.env.PROD` is false
 *   when using `npm run dev`, so we must NOT use localhost:5001 in the browser.
 * - Local dev: call Flask directly at http://localhost:5001 (paths still include /api/...).
 * - Optional: set VITE_API_BASE_URL to override (e.g. separate API service).
 */
const getApiBaseUrl = () => {
  const override = import.meta.env.VITE_API_BASE_URL
  if (override !== undefined && override !== null && String(override).trim() !== '') {
    return String(override).replace(/\/$/, '')
  }

  if (typeof window !== 'undefined') {
    const h = window.location.hostname
    if (h !== 'localhost' && h !== '127.0.0.1') {
      return ''
    }
  }

  return 'http://localhost:5001'
}

// axios instance
const service = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 300000, // 5分钟超时（Ontology Generation可能需要较长时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// request interceptor
service.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// response interceptor (retry)
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // reject if not success
    if (!res.success && res.success !== undefined) {
      console.error('API Error:', res.error || res.message || 'Unknown error')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }
    
    return res
  },
  error => {
    console.error('Response error:', error)
    
    // handle timeout
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }
    
    // handle network error
    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection')
    }
    
    return Promise.reject(error)
  }
)

// request with retry
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
