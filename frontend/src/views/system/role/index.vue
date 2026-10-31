<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import type { TableColumnsType } from 'ant-design-vue'
import {
  createRole,
  deleteRole,
  listRoles,
  updateRole,
  updateRoleMenus,
  updateRoleStatus,
} from '@/api/role'
import { listMenus } from '@/api/menu'
import type { MenuNode, RoleItem } from '@/api/types'
import { reloadAccess } from '@/router/access'
import { useSessionStore } from '@/stores/session'
import { useRouter } from 'vue-router'
import { useTableHeight } from '@/utils/useTableHeight'

interface PermButton {
  id: number
  name: string
}

interface PermPage {
  id: number
  name: string
  path: string
  buttons: PermButton[]
}

interface PermSection {
  key: string
  title: string
  dirId: number | null
  pages: PermPage[]
}

const loading = ref(false)
const items = ref<RoleItem[]>([])
const router = useRouter()
const session = useSessionStore()
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const menus = ref<MenuNode[]>([])
const editorOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const rowBusy = ref<number | null>(null)
const form = reactive({
  name: '',
  code: '',
  remark: '',
})

const menuOpen = ref(false)
const menuSaving = ref(false)
const menuRoleId = ref<number | null>(null)
const menuRoleName = ref('')
const selectedIds = ref<number[]>([])

const tableWrap = ref<HTMLElement | null>(null)
const tableY = useTableHeight(tableWrap)
const columns: TableColumnsType = [
  { title: '名称', dataIndex: 'name', width: 150, ellipsis: true },
  { title: '编码', dataIndex: 'code', width: 150, ellipsis: true },
  { title: '状态', dataIndex: 'status', width: 110 },
  { title: '备注', dataIndex: 'remark', width: 200, ellipsis: true },
  { title: '操作', dataIndex: 'actions', width: 240, fixed: 'right' },
]

function toPage(node: MenuNode): PermPage {
  return {
    id: node.id,
    name: node.name,
    path: node.path,
    buttons: (node.children ?? [])
      .filter((child) => child.menu_type === 'button')
      .map((child) => ({ id: child.id, name: child.name })),
  }
}

const permSections = computed<PermSection[]>(() => {
  const sections: PermSection[] = []
  const visit = (nodes: MenuNode[]) => {
    for (const node of nodes) {
      if (node.menu_type === 'directory') {
        const children = node.children ?? []
        sections.push({
          key: `dir-${node.id}`,
          title: node.name,
          dirId: node.id,
          pages: children.filter((child) => child.menu_type === 'menu').map(toPage),
        })
        visit(children.filter((child) => child.menu_type === 'directory'))
      } else if (node.menu_type === 'menu') {
        sections.push({ key: `page-${node.id}`, title: '', dirId: null, pages: [toPage(node)] })
      }
    }
  }
  visit(menus.value)
  return sections
})

const canUpdateRole = computed(() => session.permissions.includes('system:role:update'))
const allMenuIds = computed(() => permSections.value.flatMap((section) => sectionIds(section)))
const allChecked = computed(() => allMenuIds.value.length > 0 && allMenuIds.value.every(has))

function has(id: number) {
  return selectedIds.value.includes(id)
}

function setChecked(ids: number[], checked: boolean) {
  const next = new Set(selectedIds.value)
  for (const id of ids) {
    if (checked) {
      next.add(id)
    } else {
      next.delete(id)
    }
  }
  selectedIds.value = [...next]
}

function sectionIds(section: PermSection) {
  return [
    ...(section.dirId === null ? [] : [section.dirId]),
    ...section.pages.flatMap((item) => [item.id, ...item.buttons.map((button) => button.id)]),
  ]
}

function sectionState(section: PermSection) {
  const ids = sectionIds(section)
  const count = ids.filter(has).length
  return { checked: ids.length > 0 && count === ids.length, indeterminate: count > 0 && count < ids.length }
}

function onPageToggle(item: PermPage, event: { target?: { checked?: boolean } }) {
  const checked = Boolean(event?.target?.checked)
  if (checked) {
    setChecked([item.id], true)
    return
  }
  // 取消页面时，页面下的按钮一起取消，避免出现「没有页面却有按钮权限」
  setChecked([item.id, ...item.buttons.map((button) => button.id)], false)
}

function onButtonToggle(item: PermPage, button: PermButton, event: { target?: { checked?: boolean } }) {
  const checked = Boolean(event?.target?.checked)
  // 勾按钮时自动带上所属页面，否则权限有了但导航里看不到页面
  setChecked(checked ? [item.id, button.id] : [button.id], checked)
}

function onSectionToggle(section: PermSection, event: { target?: { checked?: boolean } }) {
  setChecked(sectionIds(section), Boolean(event?.target?.checked))
}

function selectAll() {
  selectedIds.value = [...new Set(allMenuIds.value)]
}

function clearAll() {
  selectedIds.value = []
}

async function load() {
  loading.value = true
  try {
    const data = await listRoles({ page: page.value, page_size: pageSize.value })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.code = ''
  form.remark = ''
  editorOpen.value = true
}

function openEdit(record: RoleItem) {
  editingId.value = record.id
  form.name = record.name
  form.code = record.code
  form.remark = record.remark
  editorOpen.value = true
}

function openMenus(record: RoleItem) {
  menuRoleId.value = record.id
  menuRoleName.value = record.name
  selectedIds.value = [...record.menu_ids]
  menuOpen.value = true
}

async function save() {
  if (!form.name || !form.code) {
    message.error('请填写名称和编码')
    return Promise.reject(new Error('请填写名称和编码'))
  }
  saving.value = true
  try {
    const payload = { name: form.name, code: form.code, remark: form.remark }
    if (editingId.value === null) {
      await createRole(payload)
    } else {
      await updateRole(editingId.value, payload)
    }
    message.success('已保存')
    editorOpen.value = false
    await load()
    await reloadAccess(router)
  } finally {
    saving.value = false
  }
}

async function saveMenus() {
  if (menuRoleId.value === null) {
    return
  }
  menuSaving.value = true
  try {
    const updated = await updateRoleMenus(menuRoleId.value, selectedIds.value)
    const target = items.value.find((item) => item.id === updated.id)
    if (target) {
      target.menu_ids = updated.menu_ids
    }
    message.success('已保存')
    menuOpen.value = false
    await reloadAccess(router)
  } finally {
    menuSaving.value = false
  }
}

async function applyStatus(record: RoleItem, active: boolean) {
  rowBusy.value = record.id
  try {
    const updated = await updateRoleStatus(record.id, active ? 'active' : 'disabled')
    record.status = updated.status
    message.success(active ? '已启用' : '已停用')
  } finally {
    rowBusy.value = null
  }
}

function onStatusSwitch(record: RoleItem, active: boolean) {
  if (record.code === 'super_admin') {
    return
  }
  if (!active) {
    Modal.confirm({
      title: '停用后，拥有该角色的用户会失去这些菜单权限',
      okText: '停用',
      cancelText: '取消',
      onOk: () => applyStatus(record, false),
    })
    return
  }
  void applyStatus(record, true)
}

async function remove(record: RoleItem) {
  await deleteRole(record.id)
  message.success('已删除')
  await load()
  await reloadAccess(router)
}

function onTableChange(pagination: { current?: number; pageSize?: number }) {
  page.value = pagination.current ?? 1
  pageSize.value = pagination.pageSize ?? 10
  void load()
}

onMounted(async () => {
  menus.value = await listMenus()
  await load()
})
</script>

<template>
  <section class="page page-fill">
    <h1>角色管理</h1>
    <div class="toolbar">
      <p class="lead">状态控制角色是否生效，菜单在「分配菜单」里单独维护。</p>
      <a-button v-permission="'system:role:create'" type="primary" @click="openCreate">新增角色</a-button>
    </div>
    <div ref="tableWrap" class="page-fill-body table-fill">
      <a-table
        row-key="id"
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :scroll="{ x: 850, y: tableY }"
        :pagination="{ current: page, pageSize, total }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <div v-permission="'system:role:update'" class="cell-switch">
              <a-switch
                :checked="record.status === 'active'"
                :disabled="record.code === 'super_admin' || rowBusy === record.id"
                checked-children="正常"
                un-checked-children="停用"
                @change="(checked: boolean) => onStatusSwitch(record as RoleItem, checked)"
              />
            </div>
            <span v-if="!canUpdateRole">{{ record.status === 'active' ? '正常' : '停用' }}</span>
            <span v-if="record.code === 'super_admin'" class="sub">超级管理员</span>
          </template>
          <template v-else-if="column.dataIndex === 'actions'">
            <a-button v-permission="'system:role:update'" type="link" size="small" @click="openEdit(record)">编辑</a-button>
            <a-button v-permission="'system:role:update'" type="link" size="small" @click="openMenus(record)">分配菜单</a-button>
            <a-popconfirm
              v-if="record.code !== 'super_admin'"
              title="删除后，已分配该角色的用户会失去这些权限"
              ok-text="删除"
              cancel-text="取消"
              @confirm="remove(record)"
            >
              <a-button v-permission="'system:role:delete'" type="link" size="small">删除</a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="editorOpen"
      :title="editingId === null ? '新增角色' : '编辑角色'"
      :width="720"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      @ok="save"
    >
      <a-form class="form-grid" :model="form" layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item label="编码">
          <a-input v-model:value="form.code" :disabled="editingId !== null" />
        </a-form-item>
        <a-form-item class="span-2" label="备注">
          <a-input v-model:value="form.remark" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="menuOpen"
      :title="`分配菜单 · ${menuRoleName}`"
      :width="760"
      :confirm-loading="menuSaving"
      ok-text="保存"
      cancel-text="取消"
      :body-style="{ maxHeight: '60vh', overflowY: 'auto' }"
      @ok="saveMenus"
    >
      <div class="perm-toolbar">
        <span class="perm-hint">勾选页面才会出现在导航；按钮决定页面里的操作权限。</span>
        <a-space>
          <a-checkbox :checked="allChecked" :indeterminate="!allChecked && selectedIds.length > 0" @change="(e: { target?: { checked?: boolean } }) => (e.target?.checked ? selectAll() : clearAll())">
            全选
          </a-checkbox>
        </a-space>
      </div>
      <p v-if="!permSections.length" class="perm-empty">还没有菜单，先到「菜单管理」里添加。</p>
      <div v-for="section in permSections" :key="section.key" class="perm-section">
        <div v-if="section.title" class="perm-section-head">
          <a-checkbox
            :checked="sectionState(section).checked"
            :indeterminate="sectionState(section).indeterminate"
            @change="(e: { target?: { checked?: boolean } }) => onSectionToggle(section, e)"
          >
            {{ section.title }}
          </a-checkbox>
          <a-tag class="type-tag type-directory">目录</a-tag>
        </div>
        <div class="perm-pages">
          <div v-for="item in section.pages" :key="item.id" class="perm-page">
            <div class="perm-page-head">
              <a-checkbox :checked="has(item.id)" @change="(e: { target?: { checked?: boolean } }) => onPageToggle(item, e)">
                {{ item.name }}
              </a-checkbox>
              <a-tag class="type-tag type-menu">页面</a-tag>
              <span class="perm-path">{{ item.path }}</span>
            </div>
            <div v-if="item.buttons.length" class="perm-buttons">
              <a-tag class="type-tag type-button">按钮</a-tag>
              <a-checkbox
                v-for="button in item.buttons"
                :key="button.id"
                :checked="has(button.id)"
                @change="(e: { target?: { checked?: boolean } }) => onButtonToggle(item, button, e)"
              >
                <span class="perm-button-name">{{ button.name }}</span>
              </a-checkbox>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </section>
</template>

<style scoped>
.cell-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}

.perm-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.perm-hint {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.perm-empty {
  margin: 0;
  color: var(--muted);
}

.perm-section + .perm-section {
  margin-top: 18px;
}

.perm-section-head {
  display: flex;
  gap: 8px;
  align-items: center;
  padding-bottom: 6px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.perm-pages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.perm-page {
  padding-left: 4px;
}

.perm-page-head {
  display: flex;
  gap: 10px;
  align-items: center;
}

.perm-page-head :deep(.ant-checkbox-wrapper) {
  color: var(--text);
}

.perm-path {
  color: var(--muted);
  font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

/* 按钮权限横向排列，页面多了也不会堆成一长列 */
.perm-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  align-items: center;
  margin: 6px 0 0 24px;
}

.perm-button-name {
  color: #a85a00;
}
</style>
