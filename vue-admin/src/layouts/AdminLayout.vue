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
      return
    }
  }

  if (!siteStore.sites.length) {
    try {
      await siteStore.fetchSites()
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

      <div class="flex min-h-screen w-full flex-1 flex-col lg:pl-64">
        <Topbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />

        <main class="flex-1 px-4 py-5 sm:px-6 sm:py-7 lg:px-8">
          <RouterView />
        </main>
      </div>
    </div>
  </div>
</template>
