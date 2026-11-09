import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { palettes, getPalette } from '../src/theme/presets.ts'
import { paletteToCssVars } from '../src/theme/runtime.ts'
import { buildAntdTheme } from '../src/theme.ts'

const SRC = fileURLToPath(new URL('../src', import.meta.url))

test('paletteToCssVars 为每套配色输出 18 个变量', () => {
  for (const palette of palettes) {
    const vars = paletteToCssVars(palette)
    assert.equal(Object.keys(vars).length, 18, palette.id)
    for (const key of ['--row-alt', '--row-hover', '--menu-sub', '--menu-hover', '--accent']) {
      assert.ok(vars[key], `${palette.id} ${key}`)
    }
  }
})

test('buildAntdTheme 把配色映射到 AntD token', () => {
  const theme = buildAntdTheme(getPalette('ocean'))
  assert.equal(theme.token.colorPrimary, '#2563C9')
  assert.equal(theme.token.colorBgLayout, '#F2F5FA')
  assert.equal(theme.components.Menu.colorItemBg, '#14243D')
  assert.equal(theme.components.Layout.colorBgHeader, '#F6F9FD')
})

test('源码里的主题变量都由 paletteToCssVars 提供', () => {
  const staticVars = new Set(['--table-row'])
  const known = new Set(Object.keys(paletteToCssVars(palettes[0])))
  const files = []
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name)
      if (statSync(full).isDirectory()) {
        walk(full)
      } else if (/\.(vue|css)$/.test(name)) {
        files.push(full)
      }
    }
  }
  walk(SRC)

  const missing = new Set()
  for (const file of files) {
    const text = readFileSync(file, 'utf8')
    for (const match of text.matchAll(/var\((--[a-z-]+)/g)) {
      if (!known.has(match[1]) && !staticVars.has(match[1])) {
        missing.add(match[1])
      }
    }
  }
  assert.deepEqual([...missing].sort(), [])
})

test('皓白主题在浅色侧栏上使用深色悬停文字', () => {
  const theme = buildAntdTheme(getPalette('snow'))
  assert.equal(theme.components.Menu.colorItemBg, '#FFFFFF')
  assert.equal(theme.components.Menu.colorItemTextHover, '#1B1F22')
  assert.equal(theme.components.Menu.colorItemTextSelected, '#F7FBFA')
  assert.equal(theme.components.Menu.colorItemBgSelected, '#1F2328')
  assert.equal(theme.components.Layout.colorBgHeader, '#FBFCFC')
})
