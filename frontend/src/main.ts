import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/600.css'
import App from './App.vue'
import { router } from './router'
import { setupPermission } from './directives/permission'
import './styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Antd)
setupPermission(app)
app.mount('#app')
