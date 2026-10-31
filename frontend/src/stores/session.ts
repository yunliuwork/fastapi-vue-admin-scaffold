import { defineStore } from 'pinia'
import {
  bindLoginTotp,
  changePassword as requestPasswordChange,
  getAccess,
  getMe,
  login,
  logout,
  verifyLoginTotp,
} from '@/api/auth'
import type { LoginStepPayload, MenuNode, UserItem } from '@/api/types'

export const useSessionStore = defineStore('session', {
  state: () => ({
    accessToken: localStorage.getItem('access_token') ?? '',
    profile: null as UserItem | null,
    menus: [] as MenuNode[],
    permissions: [] as string[],
    loaded: false,
  }),
  actions: {
    persist(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    },
    clear() {
      this.accessToken = ''
      this.profile = null
      this.menus = []
      this.permissions = []
      this.loaded = false
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
    async signInWithPassword(username: string, password: string): Promise<LoginStepPayload> {
      return login(username, password)
    },
    async completeLogin(accessToken: string, refreshToken: string) {
      this.persist(accessToken, refreshToken)
      await this.fetchProfile()
    },
    async verifyTotpAndLogin(preAuthToken: string, totpCode: string) {
      const tokens = await verifyLoginTotp(preAuthToken, totpCode)
      await this.completeLogin(tokens.access_token, tokens.refresh_token)
    },
    async bindTotpAndLogin(preAuthToken: string, totpCode: string) {
      const tokens = await bindLoginTotp(preAuthToken, totpCode)
      await this.completeLogin(tokens.access_token, tokens.refresh_token)
    },
    async changePassword(oldPassword: string, newPassword: string) {
      const tokens = await requestPasswordChange(oldPassword, newPassword)
      this.persist(tokens.access_token, tokens.refresh_token)
    },
    async signOut() {
      try {
        if (this.accessToken) {
          await logout()
        }
      } catch {
        // 令牌已经失效时也要清掉本地登录态
      }
      this.clear()
    },
    async fetchProfile() {
      const [profile, access] = await Promise.all([getMe(), getAccess()])
      this.profile = profile
      this.menus = access.menus
      this.permissions = access.permissions
      this.loaded = true
    },
  },
})
