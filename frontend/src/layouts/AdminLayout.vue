<script setup lang="ts">
import { computed, h, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BgColorsOutlined,
  CheckOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
} from '@ant-design/icons-vue'
import type { ItemType } from 'ant-design-vue'
import { useSessionStore } from '@/stores/session'
import { useThemeStore } from '@/stores/theme'
import { palettes } from '@/theme/presets'
import { isLightColor } from '@/theme/runtime'
import { resetAccessRoutes } from '@/router/access'
import { resolveIcon } from '@/utils/icons'
import type { MenuNode } from '@/api/types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const themeStore = useThemeStore()
const menuTheme = computed<'dark' | 'light'>(() => (isLightColor(themeStore.palette.ink) ? 'light' : 'dark'))
const themeOpen = ref(false)
const collapsed = ref(false)
const passwordOpen = ref(false)
const savingPassword = ref(false)
const passwordForm = reactive({ old_password: '', new_password: '' })
const openKeys = ref<string[]>([])
const selectedKeys = computed(() => [route.path])

function pickTheme(id: string) {
  themeStore.setPalette(id)
  themeOpen.value = false
}

function toItems(nodes: MenuNode[]): ItemType[] {
  return nodes.map((node) => {
    const key = node.path || `dir-${node.id}`
    const item: ItemType = {
      key,
      label: node.name,
      icon: node.icon ? () => h(resolveIcon(node.icon)) : undefined,
    }
    if (node.children?.length) {
      return { ...item, children: toItems(node.children) }
    }
    return item
  })
}

const menuItems = computed(() => toItems(session.menus))

function isPage(nodes: MenuNode[], key: string): boolean {
  return nodes.some((node) => {
    if (node.menu_type === 'menu' && node.path === key) {
      return true
    }
    return node.children?.length ? isPage(node.children, key) : false
  })
}

function onMenuClick(info: { key: string | number }) {
  const key = String(info.key)
  if (isPage(session.menus, key)) {
    router.push(key)
  }
}

function onOpenChange(keys: (string | number)[]) {
  const values = keys.map(String)
  const dirs = topLevelDirs()
  // 手风琴：只保留最后打开的那个一级目录（以及它下面的子目录）
  const owner = values
    .map((key) => dirs.find((dir) => key === dir || key.startsWith(`${dir}/`)))
    .filter((dir): dir is string => Boolean(dir))
    .pop()
  openKeys.value = owner ? values.filter((key) => key === owner || key.startsWith(`${owner}/`)) : []
}

function topLevelDirs(): string[] {
  return session.menus
    .filter((node) => node.menu_type === 'directory' && node.path)
    .map((node) => node.path)
}

function dirKeyForPath(path: string): string | null {
  return topLevelDirs().find((dir) => path === dir || path.startsWith(`${dir}/`)) ?? null
}

watch(
  () => [route.path, session.menus.length] as const,
  ([path]) => {
    // 进入页面时只展开它所属的一级目录，其它目录收起
    const dir = dirKeyForPath(path)
    openKeys.value = dir ? [dir] : []
  },
  { immediate: true },
)

function onAccountMenu(info: { key: string | number }) {
  if (info.key === 'password') {
    passwordOpen.value = true
  }
  if (info.key === 'logout') {
    void logout()
  }
}

async function logout() {
  resetAccessRoutes(router)
  await session.signOut()
  router.push('/login')
}

async function savePassword() {
  if (!passwordForm.old_password) {
    message.error('请填写原密码')
    return Promise.reject(new Error('请填写原密码'))
  }
  if (passwordForm.new_password.length < 6) {
    message.error('新密码至少 6 位')
    return Promise.reject(new Error('新密码至少 6 位'))
  }
  savingPassword.value = true
  try {
    await session.changePassword(passwordForm.old_password, passwordForm.new_password)
    message.success('已保存')
    passwordOpen.value = false
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (error) {
    return Promise.reject(error)
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <a-layout class="shell">
    <a-layout-sider
      v-model:collapsed="collapsed"
      class="sider"
      :style="{ background: 'var(--ink)' }"
      :width="216"
      :collapsed-width="72"
      breakpoint="xl"
      theme="dark"
      :trigger="null"
      collapsible
    >
      <div class="brand" :title="'fastapi-vue-admin-scaffold'">
        {{ collapsed ? 'AS' : 'Admin Scaffold' }}
      </div>
      <a-menu
        :theme="menuTheme"
        mode="inline"
        :selected-keys="selectedKeys"
        :open-keys="openKeys"
        :items="menuItems"
        @openChange="onOpenChange"
        @click="onMenuClick"
      />
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="header">
        <a-button type="text" aria-label="折叠菜单" @click="collapsed = !collapsed">
          <MenuUnfoldOutlined v-if="collapsed" />
          <MenuFoldOutlined v-else />
        </a-button>
        <div class="header-actions">
          <a-popover v-model:open="themeOpen" trigger="click" placement="bottomRight">
            <a-button type="text" aria-label="切换配色">
              <BgColorsOutlined />
            </a-button>
            <template #content>
              <div class="theme-list">
                <button
                  v-for="palette in palettes"
                  :key="palette.id"
                  type="button"
                  class="theme-row"
                  :class="{ active: palette.id === themeStore.paletteId }"
                  @click="pickTheme(palette.id)"
                >
                  <span class="theme-dots">
                    <i :style="{ background: palette.ink }" />
                    <i :style="{ background: palette.paper }" />
                    <i :style="{ background: palette.accent }" />
                  </span>
                  <span class="theme-name">{{ palette.label }}</span>
                  <CheckOutlined v-if="palette.id === themeStore.paletteId" class="theme-check" />
                </button>
              </div>
            </template>
          </a-popover>
          <a-dropdown :trigger="['click']" placement="bottomRight">
            <button type="button" class="account">
              <span>{{ session.profile?.nickname || session.profile?.username }}</span>
              <DownOutlined />
            </button>
            <template #overlay>
              <a-menu @click="onAccountMenu">
                <a-menu-item key="password">修改密码</a-menu-item>
                <a-menu-item key="logout">退出</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
  <a-modal
    v-model:open="passwordOpen"
    title="修改密码"
    ok-text="保存"
    cancel-text="取消"
    :confirm-loading="savingPassword"
    @ok="savePassword"
  >
    <a-form layout="vertical" :model="passwordForm">
      <a-form-item label="原密码">
        <a-input-password v-model:value="passwordForm.old_password" autocomplete="current-password" />
      </a-form-item>
      <a-form-item label="新密码">
        <a-input-password v-model:value="passwordForm.new_password" autocomplete="new-password" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style scoped>
.shell {
  height: 100vh;
  overflow: hidden;
  background: var(--paper);
}

.shell > .ant-layout {
  min-width: 0;
}

.sider {
  background: var(--ink);
}

.brand {
  height: 56px;
  padding: 0 20px;
  color: var(--menu-text);
  font-weight: 600;
  line-height: 56px;
  letter-spacing: 0.01em;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--line);
}

.account {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  height: 36px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text);
  font: inherit;
  cursor: pointer;
}

.account:hover {
  background: var(--account-hover);
}

.header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.theme-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 184px;
}

.theme-row {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  font: inherit;
  cursor: pointer;
}

.theme-row:hover {
  background: var(--account-hover);
}

.theme-row.active {
  font-weight: 600;
}

.theme-dots {
  display: inline-flex;
  gap: 4px;
}

.theme-dots i {
  width: 10px;
  height: 10px;
  border: 1px solid rgba(22, 35, 38, 0.24);
  border-radius: 50%;
}

.theme-name {
  flex: 1;
  text-align: left;
}

.theme-check {
  color: var(--accent);
}

.content {
  flex: 1;
  min-height: 0;
  padding: 24px;
  overflow: auto;
}

@media (max-width: 720px) {
  .content {
    padding: 16px;
  }
}
</style>
