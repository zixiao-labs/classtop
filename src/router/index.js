import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Settings from '../pages/Settings.vue'
import TopBar from '../TopBar/TopBar.vue'
import Main from '../Main.vue'
import SchedulePage from '../pages/SchedulePage.vue'
import AudioMonitor from '../pages/AudioMonitor.vue'
import Statistics from '../pages/Statistics.vue'

const routes = [
  {
    path: '/',
    component: Main,
    children: [
      { path: '', name: 'Home', component: Home },
      { path: '/schedule', name: 'SchedulePage', component: SchedulePage },
      { path: '/statistics', name: 'Statistics', component: Statistics },
      { path: '/settings', name: 'Settings', component: Settings },
      { path: '/audio', name: 'AudioMonitor', component: AudioMonitor }
    ]
  },
  { path: '/topbar', name: 'TopBar', component: TopBar }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
