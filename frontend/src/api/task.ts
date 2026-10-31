import { deleteJson, getJson, postJson, putJson } from './http'
import type { Page } from './types'

export interface ScheduledJobItem {
  id: number
  name: string
  job_key: string
  trigger_type: 'interval' | 'cron'
  trigger_config: string
  params: string
  enabled: boolean
  builtin: boolean
  remark: string
  trigger_label: string
  last_run_at: string
  last_status: string
}

export interface ScheduledJobHandler {
  key: string
  label: string
}

export interface ScheduledJobLogItem {
  id: number
  job_id: number
  job_name: string
  status: string
  message: string
  trigger_mode: string
  started_at: string
  finished_at: string
}

export function listScheduledJobs(params: { page: number; page_size: number }) {
  return getJson<Page<ScheduledJobItem>>('/scheduled-jobs', params)
}

export function listJobHandlers() {
  return getJson<ScheduledJobHandler[]>('/scheduled-jobs/handlers')
}

export function createScheduledJob(body: {
  name: string
  job_key: string
  trigger_type: 'interval' | 'cron'
  trigger_config: string
  params: string
  enabled: boolean
  remark: string
}) {
  return postJson<ScheduledJobItem>('/scheduled-jobs', body)
}

export function updateScheduledJob(
  id: number,
  body: {
    name: string
    trigger_type: 'interval' | 'cron'
    trigger_config: string
    params: string
    enabled: boolean
    remark: string
  },
) {
  return putJson<ScheduledJobItem>(`/scheduled-jobs/${id}`, body)
}

export function deleteScheduledJob(id: number) {
  return deleteJson<null>(`/scheduled-jobs/${id}`)
}

export function runScheduledJob(id: number) {
  return postJson<ScheduledJobLogItem>(`/scheduled-jobs/${id}/run`)
}

export function listScheduledJobLogs(id: number, params: { page: number; page_size: number }) {
  return getJson<Page<ScheduledJobLogItem>>(`/scheduled-jobs/${id}/logs`, params)
}
