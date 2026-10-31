import { deleteJson, getJson, postJson, putJson } from './http'
import type { Page, RoleItem } from './types'

export type { RoleItem }

export function listRoles(params: { page: number; page_size: number }) {
  return getJson<Page<RoleItem>>('/roles', params)
}

export function createRole(body: {
  name: string
  code: string
  remark: string
  status: string
  menu_ids: number[]
}) {
  return postJson<RoleItem>('/roles', body)
}

export function updateRole(
  id: number,
  body: { name: string; code: string; remark: string; status: string; menu_ids: number[] },
) {
  return putJson<RoleItem>(`/roles/${id}`, body)
}

export function deleteRole(id: number) {
  return deleteJson<null>(`/roles/${id}`)
}
