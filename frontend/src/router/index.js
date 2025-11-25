import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import RecipeBookView from '../views/RecipeBookView.vue'
import ChefDashboard from '../views/ChefDashboard.vue'
import AdminLandingView from '../views/AdminLandingView.vue'
import MyOrdersView from '../views/MyOrdersView.vue'
import RecipeManagerView from '../views/RecipeManagerView.vue'
import RecipeEditorView from '../views/RecipeEditorView.vue'

import InventoryView from '../views/InventoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/my-orders',
      name: 'my-orders',
      component: MyOrdersView
    },
    {
      path: '/recipe/:id',
      name: 'recipe-book',
      component: RecipeBookView
    },
    {
      path: '/chef',
      name: 'chef-landing',
      component: AdminLandingView
    },
    {
      path: '/chef/orders',
      name: 'chef-orders',
      component: ChefDashboard
    },
    {
      path: '/chef/recipes',
      name: 'chef-recipes',
      component: RecipeManagerView
    },
    {
      path: '/chef/recipes/new',
      name: 'chef-recipe-new',
      component: RecipeEditorView
    },
    {
      path: '/chef/recipes/:id/edit',
      name: 'chef-recipe-edit',
      component: RecipeEditorView
    },
    {
      path: '/chef/inventory',
      name: 'chef-inventory',
      component: InventoryView
    }
  ]
})

export default router

