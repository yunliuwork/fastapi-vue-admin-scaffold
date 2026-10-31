<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { createMenu, deleteMenu, listMenus, updateMenu, type MenuInput } from '@/api/menu'
import type { MenuNode } from '@/api/types'
import { reloadAccess } from '@/router/access'
import { useRouter } from 'vue-router'

type MenuRow = Omit<MenuNode, 'children'> & { children?: MenuRow[] }

const loading = ref(false)
const menus = ref<MenuNode[]>([])
const router = useRouter()
const editorOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const tableKey = ref(0)
const expandedRowKeys = ref<number[]>([])
const form = reactive<MenuInput>({
  parent_id: null,
  name: '',
  menu_type: 'menu',
  path: '',
  component: '',
  permission: '',
  icon: '',
  sort: 0,
  visible: true,
  status: 'active',
})

const typeOptions = [
  { value: 'directory', label: '目录' },
  { value: 'menu', label: '页面' },
  { value: 'button', label: '按钮' },
]
const statusOptions = [
  { value: 'active', label: '正常' },
  { value: 'disabled', label: '停用' },
]
const columns = [
  { title: '名称', dataIndex: 'name' },
  { title: '类型', dataIndex: 'menu_type', width: 90 },
  { title: '路径', dataIndex: 'path' },
  { title: '权限标识', dataIndex: 'permission' },
  { title: '排序', dataIndex: 'sort', width: 80 },
  { title: '操作', dataIndex: 'actions', width: 140 },
]
const typeLabel: Record<MenuNode['menu_type'], string> = {
  directory: '目录',
  menu: '页面',
  button: '按钮',
}

function toRows(nodes: MenuNode[]): MenuRow[] {
  return nodes.map((node) => ({
    ...node,
    children: node.children?.length ? toRows(node.children) : undefined,
  }))
}

const rows = computed(() => toRows(menus.value))

const allExpandableIds = computed(() => expandableIds(rows.value))

const hasExpandable = computed(() => allExpandableIds.value.length > 0)

const isFullyExpanded = computed(() => {
  const ids = allExpandableIds.value
  if (!ids.length) {
    return false
  }
  const open = new Set(expandedRowKeys.value)
  return ids.every((id) => open.has(id))
})

function expandAll() {
  expandedRowKeys.value = [...allExpandableIds.value]
}

function collapseAll() {
  expandedRowKeys.value = []
}

function expandableIds(nodes: MenuRow[]): number[] {
  const ids: number[] = []
  const walk = (list: MenuRow[]) => {
    list.forEach((node) => {
      if (node.children?.length) {
        ids.push(node.id)
        walk(node.children)
      }
    })
  }
  walk(nodes)
  return ids
}

function toggleExpand(record: MenuRow) {
  if (!record.children?.length) {
    return
  }
  if (expandedRowKeys.value.includes(record.id)) {
    expandedRowKeys.value = expandedRowKeys.value.filter((id) => id !== record.id)
  } else {
    expandedRowKeys.value = [...expandedRowKeys.value, record.id]
  }
}

function customRow(record: MenuRow) {
  return {
    class: record.children?.length ? 'menu-row-expandable' : '',
    onClick: (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (target.closest('.ant-table-row-expand-icon, button, a, .ant-popconfirm')) {
        return
      }
      toggleExpand(record)
    },
  }
}

function flatten(nodes: MenuNode[], acc: MenuNode[] = []) {
  nodes.forEach((node) => {
    acc.push(node)
    if (node.children?.length) {
      flatten(node.children, acc)
    }
  })
  return acc
}

const parentOptions = computed(() => {
  const allowed = form.menu_type === 'button' ? 'menu' : 'directory'
  return flatten(menus.value)
    .filter((node) => node.menu_type === allowed && node.id !== editingId.value)
    .map((node) => ({ value: node.id, label: node.name }))
})

async function load() {
  loading.value = true
  try {
    menus.value = await listMenus()
    expandedRowKeys.value = [...allExpandableIds.value]
    tableKey.value += 1
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.parent_id = null
  form.name = ''
  form.menu_type = 'menu'
  form.path = ''
  form.component = ''
  form.permission = ''
  form.icon = ''
  form.sort = 0
  form.visible = true
  form.status = 'active'
}

function openCreate() {
  editingId.value = null
  resetForm()
  editorOpen.value = true
}

function openEdit(record: MenuRow) {
  editingId.value = record.id
  form.parent_id = record.parent_id
  form.name = record.name
  form.menu_type = record.menu_type
  form.path = record.path
  form.component = record.component
  form.permission = record.permission
  form.icon = record.icon
  form.sort = record.sort
  form.visible = record.visible
  form.status = record.status
  editorOpen.value = true
}

async function save() {
  if (!form.name) {
    message.error('请填写名称')
    return Promise.reject(new Error('请填写名称'))
  }
  saving.value = true
  try {
    const payload: MenuInput = { ...form, parent_id: form.parent_id ?? null }
    if (editingId.value === null) {
      await createMenu(payload)
    } else {
      await updateMenu(editingId.value, payload)
    }
    message.success('已保存')
    editorOpen.value = false
    await load()
    await reloadAccess(router)
  } finally {
    saving.value = false
  }
}

async function remove(record: MenuRow) {
  await deleteMenu(record.id)
  message.success('已删除')
  await load()
  await reloadAccess(router)
}

onMounted(load)
</script>

<template>
  <section class="page">
    <h1>菜单管理</h1>
    <div class="toolbar">
      <div class="toolbar-left">
        <p class="lead">目录负责分组，页面对应一个路由，按钮对应页面上的操作。</p>
        <a-space>
          <a-button :disabled="!hasExpandable || isFullyExpanded" @click="expandAll">全部展开</a-button>
          <a-button :disabled="!hasExpandable || !expandedRowKeys.length" @click="collapseAll">全部收起</a-button>
        </a-space>
      </div>
      <a-button v-permission="'system:menu:create'" type="primary" @click="openCreate">新增菜单</a-button>
    </div>
    <a-table
      :key="tableKey"
      v-model:expanded-row-keys="expandedRowKeys"
      row-key="id"
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="false"
      :custom-row="customRow"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'menu_type'">
          {{ typeLabel[record.menu_type as MenuNode['menu_type']] }}
        </template>
        <template v-else-if="column.dataIndex === 'actions'">
          <a-button v-permission="'system:menu:update'" type="link" size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm
            v-if="!record.children?.length"
            title="删除这个菜单？"
            ok-text="删除"
            cancel-text="取消"
            @confirm="remove(record)"
          >
            <a-button v-permission="'system:menu:delete'" type="link" size="small">删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="editorOpen"
      :title="editingId === null ? '新增菜单' : '编辑菜单'"
      :width="760"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      @ok="save"
    >
      <a-form class="form-grid" :model="form" layout="vertical">
        <a-form-item label="类型">
          <a-select v-model:value="form.menu_type" :options="typeOptions" />
        </a-form-item>
        <a-form-item label="名称">
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item label="上级">
          <a-select v-model:value="form.parent_id" allow-clear placeholder="无" :options="parentOptions" />
        </a-form-item>
        <a-form-item v-if="form.menu_type !== 'button'" label="路径">
          <a-input v-model:value="form.path" placeholder="/system/example" />
        </a-form-item>
        <a-form-item v-if="form.menu_type === 'menu'" label="组件">
          <a-input v-model:value="form.component" placeholder="system/example/index" />
        </a-form-item>
        <a-form-item v-if="form.menu_type !== 'directory'" label="权限标识">
          <a-input v-model:value="form.permission" placeholder="system:example:list" />
        </a-form-item>
        <a-form-item v-if="form.menu_type !== 'button'" label="图标">
          <a-input v-model:value="form.icon" placeholder="AppstoreOutlined" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="form.sort" style="width: 100%" />
        </a-form-item>
        <a-form-item label="显示">
          <a-switch v-model:checked="form.visible" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status" :options="statusOptions" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.toolbar-left {
  flex: 1;
  min-width: 0;
}

.toolbar-left .lead {
  margin-bottom: 12px;
}

.page :deep(tr.menu-row-expandable > td) {
  cursor: pointer;
}
</style>
