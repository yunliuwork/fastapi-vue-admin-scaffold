import type { App, DirectiveBinding } from 'vue'
import { useSessionStore } from '@/stores/session'

function apply(el: HTMLElement, binding: DirectiveBinding<string>) {
  const session = useSessionStore()
  if (!session.permissions.includes(binding.value)) {
    el.remove()
  }
}

export function setupPermission(app: App) {
  app.directive('permission', {
    mounted: apply,
  })
}
