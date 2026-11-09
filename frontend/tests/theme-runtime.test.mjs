import test from 'node:test'
import assert from 'node:assert/strict'

import { DEFAULT_PALETTE_ID, getPalette } from '../src/theme/presets.ts'
import { isLightColor, paletteToCssVars, readStoredPaletteId } from '../src/theme/runtime.ts'

test('paletteToCssVars 输出全部主题变量且不含 id/label', () => {
  const vars = paletteToCssVars(getPalette('ocean'))
  assert.equal(vars['--accent'], '#2563C9')
  assert.equal(vars['--ink'], '#14243D')
  assert.equal(vars['--menu-sub'], '#0F1C31')
  assert.equal(vars['--row-alt'], '#F3F6FB')
  assert.equal(vars['--header-bg'], '#F6F9FD')
  assert.equal(vars['--accent-soft'], '#EDF3FC')
  assert.equal(vars['--login-hue'], '45deg')
  assert.equal(vars['--id'], undefined)
  assert.equal(vars['--label'], undefined)
})

test('readStoredPaletteId 读取有效值', () => {
  const storage = { getItem: (key) => (key === 'admin:theme' ? 'ocean' : null) }
  assert.equal(readStoredPaletteId(storage), 'ocean')
})

test('readStoredPaletteId 未知值回退默认', () => {
  const storage = { getItem: () => 'nope' }
  assert.equal(readStoredPaletteId(storage), DEFAULT_PALETTE_ID)
})

test('readStoredPaletteId 无存储或读取异常时回退默认', () => {
  assert.equal(readStoredPaletteId(null), DEFAULT_PALETTE_ID)
  const broken = {
    getItem: () => {
      throw new Error('denied')
    },
  }
  assert.equal(readStoredPaletteId(broken), DEFAULT_PALETTE_ID)
})

test('isLightColor 区分深浅底色', () => {
  assert.equal(isLightColor('#FFFFFF'), true)
  assert.equal(isLightColor('#F1F3F4'), true)
  assert.equal(isLightColor('#163033'), false)
  assert.equal(isLightColor('#1F2328'), false)
})

test('登录页底色由侧栏深浅推导', () => {
  assert.equal(paletteToCssVars(getPalette('snow'))['--login-bg'], '#1B1F22')
  assert.equal(paletteToCssVars(getPalette('celadon'))['--login-bg'], '#163033')
  assert.equal(paletteToCssVars(getPalette('snow'))['--login-saturate'], '0.35')
  assert.equal(paletteToCssVars(getPalette('celadon'))['--login-saturate'], '1')
})
