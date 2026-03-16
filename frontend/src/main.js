import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import halleyxComponents from 'halleyx-ui-framework'
import 'halleyx-ui-framework/dist/es/index.css'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(halleyxComponents)
app.mount('#app')
