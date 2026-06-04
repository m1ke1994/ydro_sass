import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import SiteOverviewView from '../views/SiteOverviewView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import LoginView from '../views/LoginView.vue'
import LeadsView from '../views/LeadsView.vue'
import SectionEditView from '../views/SectionEditView.vue'
import SectionsView from '../views/SectionsView.vue'
import MiniLayoutView from '../views/mini/MiniLayoutView.vue'
import MiniOverviewView from '../views/mini/MiniOverviewView.vue'
import MiniLeadsView from '../views/mini/MiniLeadsView.vue'
import MiniSeoAuditView from '../views/mini/MiniSeoAuditView.vue'
import MiniReportsView from '../views/mini/MiniReportsView.vue'
import MiniSettingsView from '../views/mini/MiniSettingsView.vue'
import MiniIntegrationView from '../views/mini/MiniIntegrationView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      { path: 'dashboard', name: 'dashboard', component: DashboardView },
      { path: 'sites/:siteId/overview', name: 'site-overview', component: SiteOverviewView, props: true },
      { path: 'sites/:siteId/sections', name: 'sections', component: SectionsView, props: true },
      { path: 'sites/:siteId/analytics', name: 'analytics', component: AnalyticsView, props: true },
      { path: 'sites/:siteId/leads', name: 'leads', component: LeadsView, props: true },
      { path: 'sites/:siteId/seo', name: 'site-seo', component: MiniSeoAuditView, props: true },
      { path: 'sites/:siteId/integration', name: 'site-integration', component: MiniIntegrationView, props: true },
      {
        path: 'mini',
        component: MiniLayoutView,
        children: [
          { path: '', name: 'mini-overview', component: MiniOverviewView },
          { path: 'leads', name: 'mini-leads', component: MiniLeadsView },
          { path: 'seo', name: 'mini-seo', component: MiniSeoAuditView },
          { path: 'reports', name: 'mini-reports', component: MiniReportsView },
          { path: 'settings', name: 'mini-settings', component: MiniSettingsView },
          { path: 'integration', name: 'mini-integration', component: MiniIntegrationView },
        ],
      },
      {
        path: 'sites/:siteId/sections/:sectionId',
        name: 'section-edit',
        component: SectionEditView,
        props: true,
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }

  if (to.meta.guestOnly && token) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
