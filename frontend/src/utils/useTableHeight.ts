import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/**
 * 实测表格可滚动高度：容器高度 - 表头 - 分页 - 边框。
 *
 * 容器必须是 `page-fill-body table-fill` 里的弹性区域（高度由窗口决定），
 * 这样窗口缩放、筛选条换行时表体都会重新计算，不需要写死 `calc(100vh - N)`。
 */
export function useTableHeight(wrap: Ref<HTMLElement | null>, min = 120) {
  const tableY = ref(Math.max(min, 320))
  let observer: ResizeObserver | null = null
  let frame = 0

  function measure() {
    const el = wrap.value
    if (!el) return
    const header = el.querySelector<HTMLElement>('.ant-table-header')
    const pager = el.querySelector<HTMLElement>('.ant-table-pagination')
    const headerHeight = header?.getBoundingClientRect().height ?? 0
    let pagerHeight = 0
    if (pager) {
      const style = getComputedStyle(pager)
      pagerHeight =
        pager.getBoundingClientRect().height +
        Number.parseFloat(style.marginTop || '0') +
        Number.parseFloat(style.marginBottom || '0')
    }
    const next = Math.max(min, Math.floor(el.clientHeight - headerHeight - pagerHeight - 2))
    if (next !== tableY.value) {
      tableY.value = next
    }
  }

  function schedule() {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(measure)
  }

  onMounted(() => {
    schedule()
    observer = new ResizeObserver(schedule)
    if (wrap.value) {
      observer.observe(wrap.value)
    }
  })

  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    observer?.disconnect()
  })

  return tableY
}
