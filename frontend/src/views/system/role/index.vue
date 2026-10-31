<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { createRole, deleteRole, listRoles, updateRole } from '@/api/role'
import { listMenus } from '@/api/menu'
import type { MenuNode, RoleItem } from '@/api/types'
import { reloadAccess } from '@/router/access'
import { useRouter } from 'vue-router'

const loading = ref(false)
const items = ref<RoleItem[]>([])
const router = useRouter()
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const menus = ref<MenuNode[]>([])
const editorOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const checkedKeys = ref<number[]>([])
const form = reactive({
  name: '',
  code: '',
  remark: '',
  status: 'active',
  menu_ids: [] as number[],
})

const columns = [
  { title: '名称', dataIndex: 'name' },
  { title: '编码', dataIndex: 'code' },
  { title: '状态', dataIndex: 'status', width: 100 },
  { title: '备注', dataIndex: 'remark' },
  { title: '操作', dataIndex: 'actions', width: 160 },
]
const statusOptions = [
  { value: 'active', label: '正常' },
  { value: 'disabled', label: '停用' },
]

function toTree(nodes: MenuNode[]): { title: string; key: number; children?: { title: string; key: number }[] }[] {
  return nodes.map((node) => ({
    title: node.name,
    key: node.id,
    children: node.children?.length ? toTree(node.children) : undefined,
  }))
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
  form.status = 'active'
  form.menu_ids = []
  checkedKeys.value = []
  editorOpen.value = true
}

function openEdit(record: RoleItem) {
  editingId.value = record.id
  form.name = record.name
  form.code = record.code
  form.remark = record.remark
  form.status = record.status
  form.menu_ids = [...record.menu_ids]
  checkedKeys.value = [...record.menu_ids]
  editorOpen.value = true
}

function onCheck(keys: number[] | { checked: number[] }) {
  const checked = (Array.isArray(keys) ? keys : keys.checked).map(Number)
  checkedKeys.value = checked
  form.menu_ids = checked
}

async function save() {
  if (!form.name || !form.code) {
    message.error('请填写名称和编码')
    return Promise.reject(new Error('请填写名称和编码'))
  }
  saving.value = true
  try {
    const payload = {
      name: form.name,
      code: form.code,
      remark: form.remark,
      status: form.status,
      menu_ids: form.menu_ids,
    }
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
  <section class="page">
    <h1>角色管理</h1>
    <div class="toolbar">
      <p class="lead">勾选页面和按钮才会授权。只勾选页面时，按钮不会出现。</p>
      <a-button v-permission="'system:role:create'" type="primary" @click="openCreate">新增角色</a-button>
    </div>
    <a-table
      row-key="id"
      :columns="columns"
      :data-source="items"
      :loading="loading"
      :pagination="{ current: page, pageSize, total }"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'status'">
          {{ record.status === 'active' ? '正常' : '停用' }}
        </template>
        <template v-else-if="column.dataIndex === 'actions'">
          <a-button v-permission="'system:role:update'" type="link" size="small" @click="openEdit(record)">编辑</a-button>
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
        <a-form-item label="备注">
          <a-input v-model:value="form.remark" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="form.status" :options="statusOptions" />
        </a-form-item>
        <a-form-item class="span-2" label="菜单">
          <a-tree
            v-if="editorOpen"
            checkable
            check-strictly
            default-expand-all
            :tree-data="toTree(menus)"
            :checked-keys="{ checked: checkedKeys, halfChecked: [] }"
            @check="onCheck"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>
