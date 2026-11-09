import { DEFAULT_PALETTE_ID, getPalette, type ThemePalette } from './presets.ts'

export const THEME_STORAGE_KEY = 'admin:theme'

const CSS_VAR_FIELDS: Array<Exclude<keyof ThemePalette, 'id' | 'label'>> = [
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
  'loginHue',
]

export function isLightColor(hex: string): boolean {
  const match = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim())
  if (!match) {
    return false
  }
  const value = Number.parseInt(match[1], 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.6
}

function toKebabCase(name: string): string {
  return name.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`)
}

export function paletteToCssVars(palette: ThemePalette): Record<string, string> {
  const vars: Record<string, string> = {}
  for (const field of CSS_VAR_FIELDS) {
    vars[`--${toKebabCase(field)}`] = palette[field]
  }
  // 登录页沿用深色底；浅色侧栏（皓白）用正文色兜底，保证卡片可读
  const lightShell = isLightColor(palette.ink)
  vars['--login-bg'] = lightShell ? palette.text : palette.ink
  // 浅色主题把背景光晕压淡，避免青绿光晕和黑白配色打架
  vars['--login-saturate'] = lightShell ? '0.35' : '1'
  return vars
}

export function readStoredPaletteId(storage: Pick<Storage, 'getItem'> | null): string {
  try {
    const stored = storage?.getItem(THEME_STORAGE_KEY) ?? ''
    return getPalette(stored).id || DEFAULT_PALETTE_ID
  } catch {
    return DEFAULT_PALETTE_ID
  }
}
