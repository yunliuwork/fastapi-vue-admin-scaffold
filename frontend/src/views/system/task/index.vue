<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import type { TableColumnsType } from 'ant-design-vue'
import {
  cleanupJobLogs,
  createScheduledJob,
  deleteScheduledJob,
  getJobLogStats,
  listJobHandlers,
  listScheduledJobLogs,
  listScheduledJobs,
  runScheduledJob,
  updateScheduledJob,
  updateScheduledJobStatus,
  type JobLogStats,
  type ScheduledJobItem,
  type ScheduledJobLogItem,
} from '@/api/task'
import { useSessionStore } from '@/stores/session'
import { formatDateTime } from '@/utils/time'
import { useTableHeight } from '@/utils/useTableHeight'

const loading = ref(false)
const items = ref<ScheduledJobItem[]>([])
const session = useSessionStore()
const rowBusy = ref<number | null>(null)
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const handlers = ref<{ value: string; label: string }[]>([])
const editorOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const logOpen = ref(false)
const logLoading = ref(false)
const logItems = ref<ScheduledJobLogItem[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logJobId = ref<number | null>(null)
const logJobName = ref('')
const cleanOpen = ref(false)
const cleaning = ref(false)
const cleanRule = ref<'all' | '7' | '30'>('30')
const cleanStats = ref<JobLogStats | null>(null)

const form = reactive({
  name: '',
  job_key: '',
  trigger_type: 'interval' as 'interval' | 'cron',
  interval_hours: 1,
  cron_expr: '0 3 * * *',
  retention_days: 180,
  enabled: true,
  remark: '',
})

const tableWrap = ref<HTMLElement | null>(null)
const tableY = useTableHeight(tableWrap)
const columns: TableColumnsType = [
  { title: '名称', dataIndex: 'name', width: 120, ellipsis: true },
  { title: '任务', dataIndex: 'job_key', width: 120, ellipsis: true },
  { title: '触发规则', dataIndex: 'trigger_label', width: 90, ellipsis: true },
  { title: '状态', dataIndex: 'enabled', width: 110 },
  { title: '上次执行', dataIndex: 'last_run_at', width: 130, ellipsis: true },
  { title: '上次结果', dataIndex: 'last_status', width: 96 },
  { title: '操作', dataIndex: 'actions', width: 224, fixed: 'right' },
]

const logColumns: TableColumnsType = [
  { title: '开始时间', dataIndex: 'started_at', width: 188 },
  { title: '方式', dataIndex: 'trigger_mode', width: 88 },
  { title: '结果', dataIndex: 'status', width: 88 },
  { title: '说明', dataIndex: 'message', ellipsis: true },
]

const triggerOptions = [
  { value: 'interval', label: '固定间隔' },
  { value: 'cron', label: 'Cron 表达式' },
]

const showRetention = computed(
  () => form.job_key === 'purge_old_operation_logs' || editingJobKey.value === 'purge_old_operation_logs',
)
const editingJobKey = ref('')

function statusText(enabled: boolean) {
  return enabled ? '启用' : '停用'
}

const canUpdateJob = computed(() => session.permissions.includes('system:job:update'))

async function applyEnabled(record: ScheduledJobItem, enabled: boolean) {
  rowBusy.value = record.id
  try {
    const updated = await updateScheduledJobStatus(record.id, enabled)
    record.enabled = updated.enabled
    message.success(enabled ? '已启用' : '已停用')
  } finally {
    rowBusy.value = null
  }
}

function onEnabledSwitch(record: ScheduledJobItem, enabled: boolean) {
  if (!enabled) {
    Modal.confirm({
      title: '停用后不再按计划执行，仍可手动执行',
      okText: '停用',
      cancelText: '取消',
      onOk: () => applyEnabled(record, false),
    })
    return
  }
  void applyEnabled(record, true)
}

function resultText(status: string) {
  if (status === 'success') return '成功'
  if (status === 'failure') return '失败'
  return status || '—'
}

function triggerModeText(mode: string) {
  return mode === 'manual' ? '手动' : '定时'
}

function buildTriggerConfig() {
  if (form.trigger_type === 'interval') {
    return JSON.stringify({ hours: form.interval_hours })
  }
  return JSON.stringify({ expr: form.cron_expr.trim() })
}

function buildParams() {
  if (showRetention.value) {
    return JSON.stringify({ retention_days: form.retention_days })
  }
  return '{}'
}

function fillForm(record: ScheduledJobItem) {
  editingJobKey.value = record.job_key
  form.name = record.name
  form.job_key = record.job_key
  form.trigger_type = record.trigger_type
  form.enabled = record.enabled
  form.remark = record.remark
  const trigger = JSON.parse(record.trigger_config || '{}')
  form.interval_hours = Number(trigger.hours ?? 1)
  form.cron_expr = String(trigger.expr ?? '0 3 * * *')
  const params = JSON.parse(record.params || '{}')
  form.retention_days = Number(params.retention_days ?? 180)
}

async function load() {
  loading.value = true
  try {
    const data = await listScheduledJobs({ page: page.value, page_size: pageSize.value })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadHandlers() {
  const data = await listJobHandlers()
  handlers.value = data.map((item) => ({ value: item.key, label: item.label }))
}

function openCreate() {
  editingId.value = null
  editingJobKey.value = ''
  form.name = ''
  form.job_key = handlers.value[0]?.value ?? ''
  form.trigger_type = 'interval'
  form.interval_hours = 1
  form.cron_expr = '0 3 * * *'
  form.retention_days = 180
  form.enabled = true
  form.remark = ''
  editorOpen.value = true
}

function openEdit(record: ScheduledJobItem) {
  editingId.value = record.id
  fillForm(record)
  editorOpen.value = true
}

async function save() {
  if (!form.name) {
    message.error('请填写名称')
    return Promise.reject(new Error('请填写名称'))
  }
  if (editingId.value === null && !form.job_key) {
    message.error('请选择任务')
    return Promise.reject(new Error('请选择任务'))
  }
  saving.value = true
  try {
    const payload = {
      name: form.name,
      trigger_type: form.trigger_type,
      trigger_config: buildTriggerConfig(),
      params: buildParams(),
      enabled: form.enabled,
      remark: form.remark,
    }
    if (editingId.value === null) {
      await createScheduledJob({ ...payload, job_key: form.job_key })
    } else {
      await updateScheduledJob(editingId.value, payload)
    }
    message.success('已保存')
    editorOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(record: ScheduledJobItem) {
  await deleteScheduledJob(record.id)
  message.success('已删除')
  await load()
}

async function runNow(record: ScheduledJobItem) {
  await runScheduledJob(record.id)
  message.success('已执行')
  await load()
}

async function openCleanup() {
  cleanRule.value = '30'
  cleanStats.value = null
  cleanOpen.value = true
  cleanStats.value = await getJobLogStats()
}

async function doCleanup() {
  cleaning.value = true
  try {
    const days = cleanRule.value === 'all' ? null : Number(cleanRule.value)
    const result = await cleanupJobLogs(days)
    message.success(result.deleted > 0 ? `已清理 ${result.deleted} 条日志` : '没有可清理的日志')
    cleanOpen.value = false
  } finally {
    cleaning.value = false
  }
}

async function openLogs(record: ScheduledJobItem) {
  logJobId.value = record.id
  logJobName.value = record.name
  logPage.value = 1
  logOpen.value = true
  await loadLogs()
}

async function loadLogs() {
  if (logJobId.value === null) return
  logLoading.value = true
  try {
    const data = await listScheduledJobLogs(logJobId.value, { page: logPage.value, page_size: 10 })
    logItems.value = data.items
    logTotal.value = data.total
  } finally {
    logLoading.value = false
  }
}

function onTableChange(pagination: { current?: number; pageSize?: number }) {
  page.value = pagination.current ?? 1
  pageSize.value = pagination.pageSize ?? 10
  void load()
}

function onLogTableChange(pagination: { current?: number }) {
  logPage.value = pagination.current ?? 1
  void loadLogs()
}

onMounted(async () => {
  await loadHandlers()
  await load()
})
</script>

<template>
  <section class="page page-fill">
    <h1>定时任务</h1>
    <div class="toolbar">
      <a-space>
        <a-button v-permission="'system:job:create'" type="primary" @click="openCreate">新增任务</a-button>
        <a-button v-permission="'system:job:delete'" @click="openCleanup">清理日志</a-button>
      </a-space>
    </div>
    <div ref="tableWrap" class="page-fill-body table-fill">
      <a-table
        row-key="id"
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :scroll="{ x: 890, y: tableY }"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'last_run_at'">
            {{ formatDateTime(record.last_run_at) }}
          </template>
          <template v-else-if="column.dataIndex === 'enabled'">
            <div v-permission="'system:job:update'" class="cell-switch">
              <a-switch
                :checked="record.enabled"
                :disabled="rowBusy === record.id"
                checked-children="启用"
                un-checked-children="停用"
                @change="(checked: boolean) => onEnabledSwitch(record as ScheduledJobItem, checked)"
              />
            </div>
            <span v-if="!canUpdateJob">{{ statusText(record.enabled) }}</span>
          </template>
          <template v-else-if="column.dataIndex === 'last_status'">
            <span class="result" :data-ok="record.last_status === 'success' ? true : record.last_status ? false : undefined">
              {{ resultText(record.last_status) }}
            </span>
          </template>
          <template v-else-if="column.dataIndex === 'actions'">
            <a-button v-permission="'system:job:update'" type="link" size="small" @click="openEdit(record)">编辑</a-button>
            <a-button v-permission="'system:job:run'" type="link" size="small" @click="runNow(record)">执行</a-button>
            <a-button type="link" size="small" @click="openLogs(record)">日志</a-button>
            <a-popconfirm
              v-if="!record.builtin"
              title="删除后不再调度该任务"
              ok-text="删除"
              cancel-text="取消"
              @confirm="remove(record)"
            >
              <a-button v-permission="'system:job:delete'" type="link" size="small">删除</a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="editorOpen"
      :title="editingId === null ? '新增任务' : '编辑任务'"
      :width="720"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      @ok="save"
    >
      <a-form class="form-grid" layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item v-if="editingId === null" label="任务">
          <a-select v-model:value="form.job_key" :options="handlers" placeholder="选择任务" />
        </a-form-item>
        <a-form-item v-else label="任务">
          <a-input :value="form.job_key" disabled />
        </a-form-item>
        <a-form-item label="触发类型">
          <a-select v-model:value="form.trigger_type" :options="triggerOptions" />
        </a-form-item>
        <a-form-item label="启用">
          <a-switch v-model:checked="form.enabled" />
        </a-form-item>
        <a-form-item v-if="form.trigger_type === 'interval'" label="间隔（小时）">
          <a-input-number v-model:value="form.interval_hours" :min="1" :max="720" style="width: 100%" />
        </a-form-item>
        <a-form-item v-else class="span-2" label="Cron 表达式">
          <a-input v-model:value="form.cron_expr" placeholder="0 3 * * *" />
        </a-form-item>
        <a-form-item v-if="showRetention" label="日志保留天数">
          <a-input-number v-model:value="form.retention_days" :min="1" :max="3650" style="width: 100%" />
        </a-form-item>
        <a-form-item class="span-2" label="备注">
          <a-textarea v-model:value="form.remark" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="cleanOpen"
      title="清理执行日志"
      :width="520"
      :confirm-loading="cleaning"
      ok-text="清理"
      cancel-text="取消"
      @ok="doCleanup"
    >
      <p class="clean-tip">清理后不可恢复，执行日志会从所有任务里删除。</p>
      <a-radio-group v-model:value="cleanRule" class="clean-options">
        <a-radio value="all">全部清理（共 {{ cleanStats?.total ?? 0 }} 条）</a-radio>
        <a-radio value="7">清理 7 天前的日志（{{ cleanStats?.older_than_7d ?? 0 }} 条）</a-radio>
        <a-radio value="30">清理 30 天前（1 个月）的日志（{{ cleanStats?.older_than_30d ?? 0 }} 条）</a-radio>
      </a-radio-group>
    </a-modal>

    <a-modal v-model:open="logOpen" :title="`执行日志 · ${logJobName}`" :width="760" :footer="null">
      <a-table
        row-key="id"
        size="small"
        :columns="logColumns"
        :data-source="logItems"
        :loading="logLoading"
        :pagination="{ current: logPage, pageSize: 10, total: logTotal }"
        @change="onLogTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'started_at'">
            {{ formatDateTime(record.started_at) }}
          </template>
          <template v-else-if="column.dataIndex === 'trigger_mode'">
            {{ triggerModeText(record.trigger_mode) }}
          </template>
          <template v-else-if="column.dataIndex === 'status'">
            <span class="result" :data-ok="record.status === 'success'">
              {{ resultText(record.status) }}
            </span>
          </template>
        </template>
      </a-table>
    </a-modal>
  </section>
</template>

<style scoped>
.clean-tip {
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 13px;
}

.clean-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cell-switch {
  display: flex;
  align-items: center;
}

.result[data-ok='true'] {
  color: #0e7c74;
}

.result[data-ok='false'] {
  color: #a33b32;
}
</style>
