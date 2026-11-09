import { ConfigProvider } from 'ant-design-vue'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { buildAntdTheme } from '@/theme'
import { getPalette, type ThemePalette } from '@/theme/presets'
import { paletteToCssVars, readStoredPaletteId, THEME_STORAGE_KEY } from '@/theme/runtime'

export const useThemeStore = defineStore('theme', () => {
  const paletteId = ref<string>(
    readStoredPaletteId(typeof localStorage === 'undefined' ? null : localStorage),
  )
  const palette = computed<ThemePalette>(() => getPalette(paletteId.value))
  const themeConfig = computed(() => buildAntdTheme(palette.value))

  function apply() {
    if (typeof document !== 'undefined') {
      const root = document.documentElement
      for (const [name, value] of Object.entries(paletteToCssVars(palette.value))) {
        root.style.setProperty(name, value)
      }
      root.setAttribute('data-theme', palette.value.id)
    }
    // 静态 Modal.confirm / message 不继承组件树里的 ConfigProvider，需要同步到全局配置。
    // antd-vue 4 的 config() 类型还停留在旧版 Theme，运行时会按 ThemeConfig 处理，这里做一次断言。
    ConfigProvider.config({
      theme: themeConfig.value,
      autoInsertSpaceInButton: false,
    } as unknown as Parameters<typeof ConfigProvider.config>[0])
  }

  function setPalette(id: string) {
    paletteId.value = getPalette(id).id
    try {
      localStorage.setItem(THEME_STORAGE_KEY, paletteId.value)
    } catch {
      // 隐私模式下写不了存储，不影响本次切换
    }
    apply()
  }

  return { paletteId, palette, themeConfig, apply, setPalette }
})
