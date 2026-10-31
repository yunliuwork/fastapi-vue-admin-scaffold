import { getJson, postJson, putJson } from './http'
import type { AccessPayload, LoginStepPayload, TokenPayload, UserItem } from './types'

export function login(username: string, password: string) {
  return postJson<LoginStepPayload>('/auth/login', { username, password })
}

export function verifyLoginTotp(preAuthToken: string, totpCode: string) {
  return postJson<TokenPayload>('/auth/login/totp-verify', {
    pre_auth_token: preAuthToken,
    totp_code: totpCode,
  })
}

export function bindLoginTotp(preAuthToken: string, totpCode: string) {
  return postJson<TokenPayload>('/auth/login/totp-bind', {
    pre_auth_token: preAuthToken,
    totp_code: totpCode,
  })
}

export function getMe() {
  return getJson<UserItem>('/auth/me')
}

export function getAccess() {
  return getJson<AccessPayload>('/auth/menus')
}

export function logout() {
  return postJson<null>('/auth/logout')
}

export function changePassword(oldPassword: string, newPassword: string) {
  return putJson<Omit<TokenPayload, 'login_step'>>('/auth/password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
