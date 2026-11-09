import test from 'node:test'
import assert from 'node:assert/strict'

import { formatDateTime } from '../src/utils/time.ts'

test('formatDateTime 按本地时区输出到秒', () => {
  const ms = 1794254787565
  const text = formatDateTime(ms)
  assert.match(text, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
  const parsed = new Date(text.replace(' ', 'T'))
  assert.equal(Math.floor(parsed.getTime() / 1000), Math.floor(ms / 1000))
})

test('空值和非法值显示 —', () => {
  assert.equal(formatDateTime(null), '—')
  assert.equal(formatDateTime(undefined), '—')
  assert.equal(formatDateTime(Number.NaN), '—')
})
