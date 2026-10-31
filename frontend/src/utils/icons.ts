import * as Icons from '@ant-design/icons-vue'
import type { Component } from 'vue'

const iconMap = Icons as unknown as Record<string, Component>

export function resolveIcon(name: string): Component {
  return iconMap[name] ?? Icons.AppstoreOutlined
}
