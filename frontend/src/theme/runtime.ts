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

function toKebabCase(name: string): string {
  return name.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`)
}

export function paletteToCssVars(palette: ThemePalette): Record<string, string> {
  const vars: Record<string, string> = {}
  for (const field of CSS_VAR_FIELDS) {
    vars[`--${toKebabCase(field)}`] = palette[field]
  }
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
