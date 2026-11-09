<script setup lang="ts">
import { ConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
</script>

<template>
  <ConfigProvider
    :locale="zhCN"
    :theme="themeStore.themeConfig"
    :auto-insert-space-in-button="false"
  >
    <router-view />
  </ConfigProvider>
</template>
