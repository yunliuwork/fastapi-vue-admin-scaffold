<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import type { TableColumnsType } from 'ant-design-vue'
import {
  createUser,
  listUsers,
  resetUserPassword,
  resetUserTotp,
  updateUser,
  updateUserStatus,
  type UserItem,
} from '@/api/user'
import { listRoles } from '@/api/role'
import type { RoleItem } from '@/api/types'
import { useTableHeight } from '@/utils/useTableHeight'

const loading = ref(false)
const items = ref<UserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const query = reactive({ username: '', status: undefined as string | undefined })
const roles = ref<RoleItem[]>([])
const editorOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const editingIsSuperuser = ref(false)
const rowBusy = ref<number | null>(null)
const form = reactive({
  username: '',
  password: '',
  nickname: '',
  statusActive: true,
  role_ids: [] as number[],
  totp_required: false,
})
const editorForm = ref()
const passwordOpen = ref(false)
const passwordUserId = ref<number | null>(null)
const nextPassword = ref('')

const statusOptions = [
  { value: 'active', label: '正常' },
  { value: 'disabled', label: '停用' },
]
const tableWrap = ref<HTMLElement | null>(null)
const tableY = useTableHeight(tableWrap)
const columns: TableColumnsType = [
  { title: '用户名', dataIndex: 'username', width: 140, ellipsis: true },
  { title: '昵称', dataIndex: 'nickname', width: 130, ellipsis: true },
  { title: '角色', dataIndex: 'roles', width: 160, ellipsis: true },
  { title: '账号状态', dataIndex: 'status', width: 110 },
  { title: '谷歌验证', dataIndex: 'totp', width: 130 },
  { title: '操作', dataIndex: 'actions', width: 230, fixed: 'right' },
]

const rules = computed(() => ({
  username: [{ required: true, message: '请填写用户名' }],
  password: editingId.value === null ? [{ required: true, min: 6, message: '密码至少 6 位' }] : [],
}))

function totpBindHint(record: UserItem) {
  if (!record.totp_required) {
    return ''
  }
  return record.totp_enabled ? '已绑定' : '待绑定'
}

async function load() {
  loading.value = true
  try {
    const data = await listUsers({
      username: query.username || undefined,
      status: query.status,
      page: page.value,
      page_size: pageSize.value,
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  void load()
}

function openCreate() {
  editingId.value = null
  editingIsSuperuser.value = false
  form.username = ''
  form.password = ''
  form.nickname = ''
  form.statusActive = true
  form.role_ids = []
  form.totp_required = false
  editorOpen.value = true
}

function openEdit(record: UserItem) {
  editingId.value = record.id
  editingIsSuperuser.value = record.is_superuser
  form.username = record.username
  form.password = ''
  form.nickname = record.nickname
  form.statusActive = record.status === 'active'
  form.role_ids = record.roles.map((role) => role.id)
  form.totp_required = Boolean(record.totp_required)
  editorOpen.value = true
}

async function save() {
  await editorForm.value?.validate()
  saving.value = true
  try {
    const status = form.statusActive ? 'active' : 'disabled'
    if (editingId.value === null) {
      await createUser({
        username: form.username,
        password: form.password,
        nickname: form.nickname,
        role_ids: form.role_ids,
        totp_required: form.totp_required,
      })
    } else {
      await updateUser(editingId.value, {
        nickname: form.nickname,
        status,
        role_ids: form.role_ids,
        totp_required: form.totp_required,
      })
    }
    message.success('已保存')
    editorOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function applyStatus(record: UserItem, active: boolean) {
  const status = active ? 'active' : 'disabled'
  rowBusy.value = record.id
  try {
    await updateUserStatus(record.id, status)
    record.status = status
    message.success(active ? '已启用' : '已停用')
  } finally {
    rowBusy.value = null
  }
}

function onStatusSwitch(record: UserItem, active: boolean) {
  if (record.is_superuser) {
    return
  }
  if (!active) {
    Modal.confirm({
      title: '停用后该账号不能登录',
      okText: '停用',
      cancelText: '取消',
      onOk: () => applyStatus(record, false),
    })
    return
  }
  void applyStatus(record, true)
}

async function applyTotpRequired(record: UserItem, required: boolean) {
  rowBusy.value = record.id
  try {
    await updateUser(record.id, {
      nickname: record.nickname,
      status: record.status,
      role_ids: record.roles.map((role) => role.id),
      totp_required: required,
    })
    record.totp_required = required
    if (!required) {
      record.totp_enabled = false
    }
    message.success(required ? '已启用谷歌验证' : '已关闭谷歌验证')
  } finally {
    rowBusy.value = null
  }
}

function onTotpSwitch(record: UserItem, required: boolean) {
  if (!required && record.totp_required) {
    Modal.confirm({
      title: '关闭后将清除该用户的验证器绑定',
      okText: '关闭',
      cancelText: '取消',
      onOk: () => applyTotpRequired(record, false),
    })
    return
  }
  void applyTotpRequired(record, true)
}

function openReset(record: UserItem) {
  passwordUserId.value = record.id
  nextPassword.value = ''
  passwordOpen.value = true
}

async function savePassword() {
  if (!passwordUserId.value || nextPassword.value.length < 6) {
    message.error('密码至少 6 位')
    return Promise.reject(new Error('密码至少 6 位'))
  }
  await resetUserPassword(passwordUserId.value, nextPassword.value)
  message.success('密码已重置')
  passwordOpen.value = false
  await load()
}

async function resetTotp(record: UserItem) {
  await resetUserTotp(record.id)
  message.success('已重置验证器，用户需重新绑定')
  await load()
}

function onTableChange(pagination: { current?: number; pageSize?: number }) {
  page.value = pagination.current ?? 1
  pageSize.value = pagination.pageSize ?? 10
  void load()
}

onMounted(async () => {
  const data = await listRoles({ page: 1, page_size: 100 })
  roles.value = data.items
  await load()
})
</script>

<template>
  <section class="page page-fill">
    <h1>用户管理</h1>
    <div class="toolbar">
      <a-form layout="inline" :model="query" @finish="search">
        <a-form-item label="用户名">
          <a-input v-model:value="query.username" allow-clear />
        </a-form-item>
        <a-form-item label="状态">
          <a-select
            v-model:value="query.status"
            allow-clear
            placeholder="全部"
            style="width: 120px"
            :options="statusOptions"
          />
        </a-form-item>
        <a-form-item>
          <a-button html-type="submit">查询</a-button>
        </a-form-item>
      </a-form>
      <a-button v-permission="'system:user:create'" type="primary" @click="openCreate">新增用户</a-button>
    </div>
    <div ref="tableWrap" class="page-fill-body table-fill">
      <a-table
        row-key="id"
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :scroll="{ x: 900, y: tableY }"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'roles'">
            {{ record.roles.map((role: { name: string }) => role.name).join('、') || '未分配' }}
          </template>
          <template v-else-if="column.dataIndex === 'status'">
            <div v-permission="'system:user:disable'" class="cell-switch">
              <a-switch
                :checked="record.status === 'active'"
                :disabled="record.is_superuser || rowBusy === record.id"
                checked-children="正常"
                un-checked-children="停用"
                @change="(checked: boolean) => onStatusSwitch(record as UserItem, checked)"
              />
            </div>
            <span v-if="record.is_superuser" class="sub">超级管理员</span>
          </template>
          <template v-else-if="column.dataIndex === 'totp'">
            <div v-permission="'system:user:update'" class="cell-switch">
              <a-switch
                :checked="Boolean(record.totp_required)"
                :disabled="rowBusy === record.id"
                checked-children="启用"
                un-checked-children="关闭"
                @change="(checked: boolean) => onTotpSwitch(record as UserItem, checked)"
              />
              <span v-if="totpBindHint(record as UserItem)" class="sub">{{ totpBindHint(record as UserItem) }}</span>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'actions'">
            <a-button v-permission="'system:user:update'" type="link" size="small" @click="openEdit(record)">编辑</a-button>
            <a-button
              v-permission="'system:user:reset-password'"
              type="link"
              size="small"
              @click="openReset(record)"
            >
              重置密码
            </a-button>
            <a-popconfirm
              v-if="record.totp_required && record.totp_enabled"
              title="清除绑定后，用户下次登录需重新绑定验证器"
              ok-text="重置"
              cancel-text="取消"
              @confirm="resetTotp(record)"
            >
              <a-button v-permission="'system:user:update'" type="link" size="small">重置验证器</a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="editorOpen"
      :title="editingId === null ? '新增用户' : '编辑用户'"
      :width="720"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      @ok="save"
    >
      <a-form ref="editorForm" class="form-grid" :model="form" :rules="rules" layout="vertical">
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="form.username" :disabled="editingId !== null" />
        </a-form-item>
        <a-form-item v-if="editingId === null" label="密码" name="password">
          <a-input-password v-model:value="form.password" />
        </a-form-item>
        <a-form-item label="昵称" name="nickname">
          <a-input v-model:value="form.nickname" />
        </a-form-item>
        <a-form-item v-if="editingId !== null" label="账号状态">
          <a-switch
            v-model:checked="form.statusActive"
            checked-children="正常"
            un-checked-children="停用"
            :disabled="editingIsSuperuser"
          />
        </a-form-item>
        <a-form-item class="span-2" label="角色" name="role_ids">
          <a-select
            v-model:value="form.role_ids"
            mode="multiple"
            :options="roles.map((role) => ({ value: role.id, label: role.name }))"
            placeholder="选择角色"
          />
        </a-form-item>
        <a-form-item class="span-2" label="谷歌验证">
          <a-switch v-model:checked="form.totp_required" checked-children="启用" un-checked-children="关闭" />
          <p class="field-hint">启用后须在该用户登录时绑定或输入验证码；关闭会清除已有绑定。</p>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="passwordOpen" title="重置密码" ok-text="保存" cancel-text="取消" @ok="savePassword">
      <a-form layout="vertical">
        <a-form-item label="新密码">
          <a-input-password v-model:value="nextPassword" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.cell-switch {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.sub {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}

.field-hint {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}
</style>
