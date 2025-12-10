import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import RecipeBookView from '../views/RecipeBookView.vue'
import ChefDashboard from '../views/ChefDashboard.vue'
import AdminLandingView from '../views/AdminLandingView.vue'
import MyOrdersView from '../views/MyOrdersView.vue'
import RecipeManagerView from '../views/RecipeManagerView.vue'
import RecipeEditorView from '../views/RecipeEditorView.vue'
import ChefLoginView from '../views/ChefLoginView.vue'
import InventoryView from '../views/InventoryView.vue'
import BlogListView from '../views/BlogListView.vue'
import BlogPostView from '../views/BlogPostView.vue'
import BlogEditorView from '../views/BlogEditorView.vue'
import BlogManagerView from '../views/BlogManagerView.vue'
import AiLabView from '../views/AiLabView.vue'
import QuestionGenView from '../views/QuestionGenView.vue'
import { auth } from '../store/auth'

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
    // 技术博客路由（公开访问）
    {
      path: '/blog',
      name: 'blog',
      component: BlogListView
    },
    {
      path: '/blog/:slug',
      name: 'blog-post',
      component: BlogPostView
    },
    // AI 实验室 - DeepSeek V3.2 Speciale 思考模型
    {
      path: '/ai-lab',
      name: 'ai-lab',
      component: AiLabView
    },
    // QuestionGen 刷题模块
    {
      path: '/questiongen',
      name: 'questiongen',
      component: QuestionGenView
    },
    // 登录页面（不需要验证）
    {
      path: '/chef/login',
      name: 'chef-login',
      component: ChefLoginView,
      meta: { requiresAuth: false }
    },
    // 以下路由需要登录验证
    {
      path: '/chef',
      name: 'chef-landing',
      component: AdminLandingView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/orders',
      name: 'chef-orders',
      component: ChefDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/recipes',
      name: 'chef-recipes',
      component: RecipeManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/recipes/new',
      name: 'chef-recipe-new',
      component: RecipeEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/recipes/:id/edit',
      name: 'chef-recipe-edit',
      component: RecipeEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/inventory',
      name: 'chef-inventory',
      component: InventoryView,
      meta: { requiresAuth: true }
    },
    // 博客管理路由（需要登录）
    {
      path: '/chef/blog',
      name: 'chef-blog',
      component: BlogManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/blog/new',
      name: 'chef-blog-new',
      component: BlogEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chef/blog/:id/edit',
      name: 'chef-blog-edit',
      component: BlogEditorView,
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    if (auth.checkAuth()) {
      next() // 已登录，允许访问
    } else {
      next('/chef/login') // 未登录，跳转到登录页
    }
  } else {
    next() // 不需要认证，直接访问
  }
})

export default router
