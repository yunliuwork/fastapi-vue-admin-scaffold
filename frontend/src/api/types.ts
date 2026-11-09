export interface RoleBrief {
  id: number
  name: string
  code: string
}

export interface UserItem {
  id: number
  username: string
  nickname: string
  status: 'active' | 'disabled'
  is_superuser: boolean
  roles: RoleBrief[]
  created_at: number
  totp_required?: boolean
  totp_enabled?: boolean
}

export interface TokenPayload {
  login_step: 'complete'
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginTotpVerifyStep {
  login_step: 'totp_verify'
  pre_auth_token: string
}

export interface LoginTotpBindStep {
  login_step: 'totp_bind'
  pre_auth_token: string
  secret: string
  otpauth_url: string
}

export type LoginStepPayload = TokenPayload | LoginTotpVerifyStep | LoginTotpBindStep

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface MenuNode {
  id: number
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
  children: MenuNode[]
}

export interface RoleItem {
  id: number
  name: string
  code: string
  remark: string
  status: 'active' | 'disabled'
  menu_ids: number[]
}

export interface AccessPayload {
  menus: MenuNode[]
  permissions: string[]
}
