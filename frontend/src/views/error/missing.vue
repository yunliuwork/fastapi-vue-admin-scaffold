<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const component = computed(() => String(route.meta.missingComponent || ''))
</script>

<template>
  <section class="page">
    <h1>组件文件不存在</h1>
    <p class="lead">
      菜单里的组件写成了 <b>{{ component }}</b>，views 下没有这个页面。改成实际文件路径后再打开。
    </p>
  </section>
</template>
