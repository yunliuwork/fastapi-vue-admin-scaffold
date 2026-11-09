<script setup lang="ts">
const stats = [
  { label: '今日订单', value: '86' },
  { label: '今日销售额', value: '¥12,480' },
  { label: '待发货', value: '23' },
  { label: '退款中', value: '4' },
]

const columns = [
  { title: '订单号', dataIndex: 'no' },
  { title: '商品', dataIndex: 'product' },
  { title: '金额', dataIndex: 'amount' },
  { title: '状态', dataIndex: 'status' },
  { title: '时间', dataIndex: 'time' },
]

const records = [
  { id: 1, no: '10231', product: '蓝牙耳机', amount: '¥199', status: '待发货', time: '10-31 09:12' },
  { id: 2, no: '10232', product: '棉麻衬衫', amount: '¥268', status: '已发货', time: '10-31 09:40' },
  { id: 3, no: '10233', product: '不锈钢杯', amount: '¥59', status: '已完成', time: '10-31 10:05' },
  { id: 4, no: '10234', product: '运动鞋', amount: '¥429', status: '待付款', time: '10-31 10:28' },
  { id: 5, no: '10235', product: '台灯', amount: '¥156', status: '退款中', time: '10-31 11:03' },
]
</script>

<template>
  <section class="page">
    <h1>工作台</h1>
    <p class="lead">静态示例。下面是一组电商数字和订单，写在页面里，没有请求接口。</p>
    <dl class="stats">
      <div v-for="item in stats" :key="item.label" :class="{ focus: item.label === '今日销售额' }">
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value }}</dd>
      </div>
    </dl>
    <h2>近期订单</h2>
    <div class="sheet">
      <a-table row-key="id" :columns="columns" :data-source="records" :pagination="false">
        <template #bodyCell="{ column, text, record }">
          <span
            v-if="column.dataIndex === 'status'"
            class="mark"
            :data-hot="record.status === '待发货' || record.status === '退款中'"
          >
            {{ text }}
          </span>
          <span v-else-if="column.dataIndex === 'amount'" class="amount">{{ text }}</span>
          <template v-else>{{ text }}</template>
        </template>
      </a-table>
    </div>
  </section>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0 0 28px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--sheet);
}

.stats div {
  padding: 18px 20px 16px;
  border-right: 1px solid var(--line);
}

.stats .focus {
  background: var(--accent-soft);
}

.stats div:last-child {
  border-right: 0;
}

.stats dt {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.stats dd {
  margin: 8px 0 0;
  font-size: 28px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  letter-spacing: 0;
}

h2 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.sheet :deep(.ant-table-wrapper) {
  border-radius: 10px;
}

.sheet :deep(.ant-table-thead > tr > th) {
  background: var(--header-bg);
  color: var(--muted);
  font-weight: 600;
}

.sheet :deep(.ant-table-tbody > tr:last-child > td) {
  border-bottom: 0;
}

.amount {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.mark {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 6px;
  background: var(--row-alt);
  color: var(--muted);
  font-size: 12px;
  line-height: 20px;
}

.mark[data-hot='true'] {
  background: var(--accent-soft);
  color: var(--accent);
}

@media (max-width: 720px) {
  .stats {
    grid-template-columns: 1fr 1fr;
  }

  .stats div:nth-child(2) {
    border-right: 0;
  }

  .stats div:nth-child(-n + 2) {
    border-bottom: 1px solid var(--line);
  }
}
</style>
