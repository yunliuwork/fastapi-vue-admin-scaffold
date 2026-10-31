<script setup lang="ts">
import { ConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { theme } from './theme'
</script>

<template>
  <ConfigProvider :locale="zhCN" :theme="theme" :auto-insert-space-in-button="false">
    <router-view />
  </ConfigProvider>
</template>
