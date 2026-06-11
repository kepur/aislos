import { defineStore } from 'pinia'
import { api } from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('admin_token') || null,
  }),
  getters: {
    isLoggedIn: (s) => !!s.token && !!s.user,
  },
  actions: {
    async login(email, password) {
      const { data } = await api.post('/auth/login', { email, password })
      this.token = data.access_token
      localStorage.setItem('admin_token', data.access_token)
      await this.fetchMe()
      const adminRoles = ['ADMIN', 'SUPER_ADMIN', 'OPS_MANAGER', 'RISK_ANALYST', 'FINANCE_OFFICER', 'DISPUTE_AGENT', 'VERIFICATION_OFFICER', 'AUDITOR']
      if (!adminRoles.includes(this.user?.role)) {
        this.logout()
        throw new Error('Not authorized as admin')
      }
    },
    async fetchMe() {
      const { data } = await api.get('/users/me')
      this.user = data
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('admin_token')
    },
  },
})
