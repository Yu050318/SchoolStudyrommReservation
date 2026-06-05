const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    const error = new Error(payload.message || '请求服务器失败')
    error.status = response.status
    throw error
  }

  return payload
}

export function normalizeStatus(status) {
  const map = {
    pending: '待签到',
    checked_in: '已签到',
    completed: '已签退',
    canceled: '已取消',
  }
  return map[status] || status
}

export function toApiBookingStatus(status) {
  const map = {
    待签到: 'pending',
    已签到: 'checked_in',
    已签退: 'completed',
    已取消: 'canceled',
  }
  return map[status] || status
}
