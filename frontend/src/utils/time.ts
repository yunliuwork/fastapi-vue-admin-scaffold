function pad(value: number): string {
  return String(value).padStart(2, '0')
}

/**
 * 后端时间统一是 13 位毫秒时间戳；按浏览器本地时区显示。
 */
export function formatDateTime(ms?: number | null): string {
  if (ms === null || ms === undefined || !Number.isFinite(ms)) {
    return '—'
  }
  const date = new Date(ms)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
