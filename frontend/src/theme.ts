import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

import type { ThemePalette } from './theme/presets.ts'
import { isLightColor } from './theme/runtime.ts'

function menuTextOn(background: string, palette: ThemePalette): string {
  return isLightColor(background) ? palette.text : '#F7FBFA'
}

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
        colorItemTextHover: menuTextOn(palette.menuHover, palette),
        colorItemTextSelected: menuTextOn(palette.accent, palette),
      },
      Layout: {
        colorBgHeader: palette.headerBg,
        colorBgBody: palette.paper,
      },
    },
  }
}

