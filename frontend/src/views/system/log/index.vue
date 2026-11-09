<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { TableColumnsType } from 'ant-design-vue'
import { listOperationLogs, type OperationLogItem } from '@/api/log'
import { useTableHeight } from '@/utils/useTableHeight'

const loading = ref(false)
const items = ref<OperationLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const query = reactive({ username: '', action: '', outcome: undefined as string | undefined })
const detailOpen = ref(false)
const current = ref<OperationLogItem | null>(null)
const outcomeOptions = [
  { value: 'success', label: '成功' },
  { value: 'failure', label: '失败' },
]
const tableWrap = ref<HTMLElement | null>(null)
const tableY = useTableHeight(tableWrap)
const columns: TableColumnsType = [
  { title: '操作人', dataIndex: 'username', width: 90, ellipsis: true },
  { title: '动作', dataIndex: 'action', width: 110, ellipsis: true },
  { title: '对象', dataIndex: 'target', width: 240, ellipsis: true },
  { title: '状态', dataIndex: 'status_code', width: 80 },
  { title: '时间', dataIndex: 'created_at', width: 170 },
  { title: '操作', dataIndex: 'actions', width: 70, fixed: 'right' },
]

function statusText(code: number | null) {
  if (code == null) return '—'
  return code < 400 ? '成功' : '失败'
}

function formatBlock(value: string) {
  if (!value) return '无'
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}

async function load() {
  loading.value = true
  try {
    const data = await listOperationLogs({
      username: query.username || undefined,
      action: query.action || undefined,
      outcome: query.outcome,
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

function onTableChange(pagination: { current?: number; pageSize?: number }) {
  page.value = pagination.current ?? 1
  pageSize.value = pagination.pageSize ?? 10
  void load()
}

function openDetail(record: OperationLogItem) {
  current.value = record
  detailOpen.value = true
}

onMounted(load)
</script>

<template>
  <section class="page page-fill">
    <h1>操作日志</h1>
    <div class="toolbar">
      <a-form layout="inline" :model="query" @finish="search">
        <a-form-item label="操作人">
          <a-input v-model:value="query.username" allow-clear />
        </a-form-item>
        <a-form-item label="动作">
          <a-input v-model:value="query.action" allow-clear />
        </a-form-item>
        <a-form-item label="状态">
          <a-select
            v-model:value="query.outcome"
            allow-clear
            placeholder="全部"
            style="width: 120px"
            :options="outcomeOptions"
          />
        </a-form-item>
        <a-form-item>
          <a-button html-type="submit">查询</a-button>
        </a-form-item>
      </a-form>
    </div>
    <div ref="tableWrap" class="page-fill-body table-fill">
      <a-table
        row-key="id"
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :scroll="{ x: 760, y: tableY }"
        :pagination="{ current: page, pageSize, total, showSizeChanger: true }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status_code'">
            <span class="status" :data-ok="record.status_code == null ? undefined : record.status_code < 400">
              {{ statusText(record.status_code) }}
            </span>
          </template>
          <template v-else-if="column.dataIndex === 'actions'">
            <a-button type="link" size="small" @click="openDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="detailOpen" title="日志详情" :width="720" :footer="null">
      <dl v-if="current" class="detail">
        <div>
          <dt>操作人</dt>
          <dd>{{ current.username || '—' }}</dd>
        </div>
        <div>
          <dt>动作</dt>
          <dd>{{ current.action }}</dd>
        </div>
        <div>
          <dt>对象</dt>
          <dd>{{ current.target || '—' }}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>{{ current.status_code == null ? '—' : `${current.status_code} ${statusText(current.status_code)}` }}</dd>
        </div>
        <div>
          <dt>IP</dt>
          <dd>{{ current.ip || '—' }}</dd>
        </div>
        <div>
          <dt>时间</dt>
          <dd>{{ current.created_at }}</dd>
        </div>
        <div class="span">
          <dt>参数</dt>
          <dd><pre>{{ formatBlock(current.params) }}</pre></dd>
        </div>
        <div class="span">
          <dt>响应</dt>
          <dd><pre>{{ formatBlock(current.response) }}</pre></dd>
        </div>
      </dl>
    </a-modal>
  </section>
</template>

<style scoped>
.page :deep(.ant-table-thead > tr > th),
.page :deep(.ant-table-tbody > tr > td) {
  padding-right: 12px;
  padding-left: 12px;
}

.page :deep(.ant-btn-link) {
  padding: 0;
  height: auto;
}
.status[data-ok='true'] {
  color: #0e7c74;
}

.status[data-ok='false'] {
  color: #a33b32;
}

.detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
  margin: 0;
}

.detail .span {
  grid-column: 1 / -1;
}

.detail dt {
  color: var(--muted);
  font-size: 13px;
}

.detail dd {
  margin: 4px 0 0;
}

.detail pre {
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 8px;
  background: var(--header-bg);
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
}

@media (max-width: 720px) {
  .detail {
    grid-template-columns: 1fr;
  }
}
</style>
