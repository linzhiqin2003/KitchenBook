import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '../store/auth'

// 使用懒加载（动态导入）减小首屏加载体积
// 首页直接加载，其他页面按需加载
import HomeView from '../views/HomeView.vue'

// 懒加载其他视图
const RecipeBookView = () => import('../views/RecipeBookView.vue')
const ChefDashboard = () => import('../views/ChefDashboard.vue')
const AdminLandingView = () => import('../views/AdminLandingView.vue')
const MyOrdersView = () => import('../views/MyOrdersView.vue')
const RecipeManagerView = () => import('../views/RecipeManagerView.vue')
const RecipeEditorView = () => import('../views/RecipeEditorView.vue')
const ChefLoginView = () => import('../views/ChefLoginView.vue')
const InventoryView = () => import('../views/InventoryView.vue')
const BlogListView = () => import('../views/BlogListView.vue')
const BlogPostView = () => import('../views/BlogPostView.vue')
const BlogEditorView = () => import('../views/BlogEditorView.vue')
const BlogManagerView = () => import('../views/BlogManagerView.vue')
const AiLabView = () => import('../views/AiLabView.vue')
const QuestionGenView = () => import('../views/QuestionGenView.vue')

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
