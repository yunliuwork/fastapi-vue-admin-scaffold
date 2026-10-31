import { deleteJson, getJson, patchJson, postJson, putJson } from './http'
import type { Page, RoleItem } from './types'

export type { RoleItem }

export type RoleProfileInput = { name: string; code: string; remark: string }

export function listRoles(params: { page: number; page_size: number }) {
  return getJson<Page<RoleItem>>('/roles', params)
}

export function createRole(body: RoleProfileInput) {
  return postJson<RoleItem>('/roles', body)
}

export function updateRole(id: number, body: RoleProfileInput) {
  return putJson<RoleItem>(`/roles/${id}`, body)
}

export function updateRoleStatus(id: number, status: 'active' | 'disabled') {
  return patchJson<RoleItem>(`/roles/${id}/status`, { status })
}

export function updateRoleMenus(id: number, menuIds: number[]) {
  return putJson<RoleItem>(`/roles/${id}/menus`, { menu_ids: menuIds })
}

export function deleteRole(id: number) {
  return deleteJson<null>(`/roles/${id}`)
}
