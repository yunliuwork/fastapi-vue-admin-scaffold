import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { useSessionStore } from '@/stores/session'
import { firstPagePath, registerAccessRoutes } from './access'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login/index.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'root',
      component: AdminLayout,
      children: [
        {
          path: 'welcome',
          name: 'welcome',
          component: () => import('@/views/welcome/index.vue'),
        },
        {
          path: ':pathMatch(.*)*',
          name: 'not-found',
          component: () => import('@/views/error/404.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  if (to.meta.public) {
    if (to.name === 'login' && session.accessToken) {
      try {
        if (!session.loaded) {
          await session.fetchProfile()
          registerAccessRoutes(router, session.menus)
        }
        return firstPagePath(session.menus)
      } catch {
        session.clear()
      }
    }
    return true
  }
  if (!session.accessToken) {
    return { name: 'login', query: to.fullPath === '/' ? undefined : { redirect: to.fullPath } }
  }
  if (!session.loaded) {
    try {
      await session.fetchProfile()
      registerAccessRoutes(router, session.menus)
    } catch {
      session.clear()
      return { name: 'login' }
    }
    return to.fullPath
  }
  if (to.path === '/') {
    return firstPagePath(session.menus)
  }
  return true
})
