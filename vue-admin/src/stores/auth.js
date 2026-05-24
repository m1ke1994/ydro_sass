import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { loginRequest, meRequest } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  function setTokens({ access, refresh }) {
    accessToken.value = access || ''
    refreshToken.value = refresh || ''

    if (accessToken.value) {
      localStorage.setItem('access_token', accessToken.value)
    } else {
      localStorage.removeItem('access_token')
    }

    if (refreshToken.value) {
      localStorage.setItem('refresh_token', refreshToken.value)
    } else {
      localStorage.removeItem('refresh_token')
    }
  }

  async function login({ email, password }) {
    const { data } = await loginRequest({ username: email, password })
    setTokens({ access: data.access, refresh: data.refresh })
    await getCurrentUser()
    return data
  }

  function logout() {
    user.value = null
    setTokens({ access: '', refresh: '' })
  }

  async function getCurrentUser() {
    if (!accessToken.value) {
      user.value = null
      return null
    }

    try {
      const { data } = await meRequest()
      user.value = data
      return data
    } catch (error) {
      logout()
      throw error
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    setTokens,
    login,
    logout,
    getCurrentUser,
  }
})
