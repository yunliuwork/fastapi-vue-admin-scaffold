import { deleteJson, getJson, postJson, putJson } from './http'
import type { MenuNode } from './types'

export type { MenuNode }

export interface MenuInput {
  parent_id: number | null
  name: string
  menu_type: 'directory' | 'menu' | 'button'
  path: string
  component: string
  permission: string
  icon: string
  sort: number
  visible: boolean
  status: 'active' | 'disabled'
}

export function listMenus() {
  return getJson<MenuNode[]>('/menus')
}

export function createMenu(body: MenuInput) {
  return postJson<MenuNode>('/menus', body)
}

export function updateMenu(id: number, body: MenuInput) {
  return putJson<MenuNode>(`/menus/${id}`, body)
}

export function deleteMenu(id: number) {
  return deleteJson<null>(`/menus/${id}`)
}
