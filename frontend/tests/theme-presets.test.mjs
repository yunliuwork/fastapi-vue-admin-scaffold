import test from 'node:test'
import assert from 'node:assert/strict'

import { DEFAULT_PALETTE_ID, getPalette, palettes } from '../src/theme/presets.ts'

const COLOR_KEYS = [
  'accent',
  'ink',
  'menuSub',
  'menuHover',
  'menuText',
  'paper',
  'sheet',
  'line',
  'text',
  'muted',
  'rowAlt',
  'rowHover',
  'headerBg',
  'accentSoft',
  'accountHover',
]

test('四套配色 id 唯一且默认存在', () => {
  const ids = palettes.map((p) => p.id)
  assert.equal(ids.length, 4)
  assert.equal(new Set(ids).size, 4)
  assert.ok(ids.includes(DEFAULT_PALETTE_ID))
})

test('每套配色都定义了全部颜色且是十六进制', () => {
  for (const p of palettes) {
    for (const key of COLOR_KEYS) {
      assert.match(p[key], /^#[0-9a-fA-F]{6}$/, `${p.id}.${key}`)
    }
    assert.match(p.loginHue, /^-?\d+deg$/, `${p.id}.loginHue`)
  }
})

test('getPalette 未知 id 回退默认', () => {
  assert.equal(getPalette('nope').id, DEFAULT_PALETTE_ID)
  assert.equal(getPalette('ocean').id, 'ocean')
})
