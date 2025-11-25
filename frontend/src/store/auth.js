import { reactive } from 'vue'

export const auth = reactive({
    isLoggedIn: localStorage.getItem('chef_logged_in') === 'true',
    token: localStorage.getItem('chef_token') || '',
    
    login(token) {
        this.token = token
        this.isLoggedIn = true
        localStorage.setItem('chef_token', token)
        localStorage.setItem('chef_logged_in', 'true')
    },
    
    logout() {
        this.token = ''
        this.isLoggedIn = false
        localStorage.removeItem('chef_token')
        localStorage.removeItem('chef_logged_in')
    },
    
    checkAuth() {
        return this.isLoggedIn && this.token
    }
})

