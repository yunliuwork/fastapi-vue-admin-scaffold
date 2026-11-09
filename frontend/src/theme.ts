import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

import { palettes, type ThemePalette } from './theme/presets'

const baseToken = {
  borderRadius: 8,
  fontFamily: '"IBM Plex Sans", "PingFang SC", "Microsoft YaHei", sans-serif',
  controlHeight: 36,
}

export function buildAntdTheme(palette: ThemePalette): ThemeConfig {
  return {
    token: {
      ...baseToken,
      colorPrimary: palette.accent,
      colorInfo: palette.accent,
      colorLink: palette.accent,
      colorBgLayout: palette.paper,
      colorText: palette.text,
      colorTextSecondary: palette.muted,
      colorBorder: palette.line,
    },
    components: {
      Menu: {
        colorItemBg: palette.ink,
        colorSubItemBg: palette.menuSub,
        colorItemBgSelected: palette.accent,
        colorItemBgHover: palette.menuHover,
        colorItemText: palette.menuText,
        colorItemTextHover: '#F7FBFA',
        colorItemTextSelected: '#F7FBFA',
      },
      Layout: {
        colorBgHeader: palette.headerBg,
        colorBgBody: palette.paper,
      },
    },
  }
}

export const theme = buildAntdTheme(palettes[0])
