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
    // ========================================
    // Kitchen 模块 - /kitchen 路径下
    // ========================================
    {
      path: '/kitchen',
      name: 'kitchen-home',
      component: HomeView
    },
    {
      path: '/kitchen/my-orders',
      name: 'my-orders',
      component: MyOrdersView
    },
    {
      path: '/kitchen/recipe/:id',
      name: 'recipe-book',
      component: RecipeBookView
    },
    // AI 实验室 - DeepSeek V3.2 Speciale 思考模型
    {
      path: '/kitchen/ai-lab',
      name: 'ai-lab',
      component: AiLabView
    },
    // 登录页面（不需要验证）
    {
      path: '/kitchen/chef/login',
      name: 'chef-login',
      component: ChefLoginView,
      meta: { requiresAuth: false }
    },
    // 以下路由需要登录验证
    {
      path: '/kitchen/chef',
      name: 'chef-landing',
      component: AdminLandingView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/orders',
      name: 'chef-orders',
      component: ChefDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/recipes',
      name: 'chef-recipes',
      component: RecipeManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/recipes/new',
      name: 'chef-recipe-new',
      component: RecipeEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/recipes/:id/edit',
      name: 'chef-recipe-edit',
      component: RecipeEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/inventory',
      name: 'chef-inventory',
      component: InventoryView,
      meta: { requiresAuth: true }
    },
    // 博客管理路由（需要登录）
    {
      path: '/kitchen/chef/blog',
      name: 'chef-blog',
      component: BlogManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/blog/new',
      name: 'chef-blog-new',
      component: BlogEditorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/kitchen/chef/blog/:id/edit',
      name: 'chef-blog-edit',
      component: BlogEditorView,
      meta: { requiresAuth: true }
    },

    // ========================================
    // Blog 模块 - /blog 路径下
    // ========================================
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

    // ========================================
    // QuestionGen 模块 - /questiongen 路径下
    // ========================================
    {
      path: '/questiongen',
      name: 'questiongen',
      component: QuestionGenView
    },

    // ========================================
    // 根路径重定向
    // ========================================
    {
      path: '/',
      redirect: '/kitchen'
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
      next('/kitchen/chef/login') // 未登录，跳转到登录页
    }
  } else {
    next() // 不需要认证，直接访问
  }
})

export default router
