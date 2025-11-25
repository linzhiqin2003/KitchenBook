import { reactive, watch } from 'vue'
import axios from 'axios'
import API_BASE_URL from '../config/api'

// Load initial state from localStorage
const savedOrderIds = JSON.parse(localStorage.getItem('kitchen_book_orders') || '[]')

export const cart = reactive({
    items: [],
    customerName: localStorage.getItem('kitchen_book_customer_name') || '',
    isOpen: false,
    myOrderIds: savedOrderIds,
    
    addItem(recipe) {
        const existing = this.items.find(i => i.recipe.id === recipe.id)
        if (existing) {
            existing.quantity++
        } else {
            this.items.push({ recipe, quantity: 1, note: '' })
        }
        this.isOpen = true
    },
    
    removeItem(recipeId) {
        const index = this.items.findIndex(i => i.recipe.id === recipeId)
        if (index > -1) {
            this.items.splice(index, 1)
        }
    },
    
    updateNote(recipeId, note) {
        const item = this.items.find(i => i.recipe.id === recipeId)
        if (item) {
            item.note = note
        }
    },
    
    async submitOrder() {
        if (!this.customerName) {
            alert('请告诉大厨您的称呼')
            return
        }
        if (this.items.length === 0) return
        
        try {
            // Save name for next time
            localStorage.setItem('kitchen_book_customer_name', this.customerName)

            const payload = {
                customer_name: this.customerName,
                items: this.items.map(i => ({
                    recipe: i.recipe.id,
                    quantity: i.quantity,
                    note: i.note || ''
                }))
            }
            
            const response = await axios.post(`${API_BASE_URL}/api/orders/`, payload)
            
            // Track this new order
            this.myOrderIds.push(response.data.id)
            localStorage.setItem('kitchen_book_orders', JSON.stringify(this.myOrderIds))
            
            this.items = []
            this.isOpen = false
            
            // Optionally redirect to tracking page or show notification
            const confirmTrack = confirm('订单已提交！是否查看订单进度？')
            if (confirmTrack) {
                window.location.href = '/my-orders' // Simple redirect
            }
            
        } catch (error) {
            console.error('Order failed', error)
            alert('下单失败，请重试')
        }
    }
})
