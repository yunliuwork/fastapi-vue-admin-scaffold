import { getJson, patchJson, postJson, putJson } from './http'
import type { Page, UserItem } from './types'

export type { UserItem }

export function listUsers(params: { username?: string; status?: string; page: number; page_size: number }) {
  return getJson<Page<UserItem>>('/users', params)
}

export function createUser(body: {
  username: string
  password: string
  nickname: string
  role_ids: number[]
  totp_required?: boolean
}) {
  return postJson<UserItem>('/users', body)
}

export function updateUser(
  id: number,
  body: { nickname: string; status: string; role_ids: number[]; totp_required: boolean },
) {
  return putJson<UserItem>(`/users/${id}`, body)
}

export function updateUserStatus(id: number, status: string) {
  return patchJson<UserItem>(`/users/${id}/status`, { status })
}

export function resetUserPassword(id: number, password: string) {
  return postJson<null>(`/users/${id}/reset-password`, { password })
}

export function resetUserTotp(id: number) {
  return postJson<UserItem>(`/users/${id}/reset-totp`)
}
