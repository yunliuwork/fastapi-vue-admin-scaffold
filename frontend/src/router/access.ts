import type { Router, RouteRecordRaw } from 'vue-router'
import type { MenuNode } from '@/api/types'
import { useSessionStore } from '@/stores/session'

const viewModules = import.meta.glob('../views/**/*.vue') as Record<
  string,
  (() => Promise<unknown>) | undefined
>

function walkMenus(nodes: MenuNode[], visit: (node: MenuNode) => void) {
  nodes.forEach((node) => {
    visit(node)
    if (node.children?.length) {
      walkMenus(node.children, visit)
    }
  })
}

export function registerAccessRoutes(router: Router, menus: MenuNode[]) {
  walkMenus(menus, (node) => {
    if (node.menu_type !== 'menu' || !node.component || !node.path) {
      return
    }
    const name = `menu-${node.id}`
    if (router.hasRoute(name)) {
      return
    }
    const loader = viewModules[`../views/${node.component}.vue`]
    const route: RouteRecordRaw = {
      path: node.path.replace(/^\//, ''),
      name,
      component: loader ?? (() => import('../views/error/missing.vue')),
      meta: { title: node.name, missingComponent: loader ? '' : node.component },
    }
    router.addRoute('root', route)
  })
}

export function resetAccessRoutes(router: Router) {
  router.getRoutes().forEach((route) => {
    if (typeof route.name === 'string' && route.name.startsWith('menu-')) {
      router.removeRoute(route.name)
    }
  })
}

export async function reloadAccess(router: Router) {
  const session = useSessionStore()
  const current = router.currentRoute.value.fullPath
  await session.fetchProfile()
  resetAccessRoutes(router)
  registerAccessRoutes(router, session.menus)
  if (router.currentRoute.value.fullPath !== current) {
    await router.replace(current)
  }
}

export function firstPagePath(menus: MenuNode[]): string {
  let found = ''
  walkMenus(menus, (node) => {
    if (!found && node.menu_type === 'menu' && node.path) {
      found = node.path
    }
  })
  return found || '/welcome'
}
