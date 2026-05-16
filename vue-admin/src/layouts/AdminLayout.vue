<script setup>
import { onMounted, ref } from 'vue'

import Sidebar from '../components/Sidebar.vue'
import Topbar from '../components/Topbar.vue'
import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

const authStore = useAuthStore()
const siteStore = useSiteStore()

const sidebarOpen = ref(false)

function closeSidebar() {
  sidebarOpen.value = false
}

onMounted(async () => {
  if (!authStore.user) {
    try {
      await authStore.getCurrentUser()
    } catch {
      // handled by interceptor
    }
  }

  if (!siteStore.site) {
    try {
      await siteStore.fetchSite()
    } catch {
      // optional
    }
  }
})
</script>

<template>
  <div class="min-h-screen bg-slate-100">
    <div class="flex min-h-screen">
      <Sidebar :open="sidebarOpen" @close="closeSidebar" />

      <div class="flex min-h-screen w-full flex-1 flex-col lg:pl-72">
        <Topbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />

        <main class="flex-1 p-4 sm:p-6 lg:p-8">
          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>
