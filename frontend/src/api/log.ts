import { getJson } from './http'
import type { Page } from './types'

export interface OperationLogItem {
  id: number
  username: string
  action: string
  target: string
  ip: string
  params: string
  response: string
  status_code: number | null
  created_at: number
}

export function listOperationLogs(params: {
  username?: string
  action?: string
  outcome?: string
  page: number
  page_size: number
}) {
  return getJson<Page<OperationLogItem>>('/operation-logs', params)
}
