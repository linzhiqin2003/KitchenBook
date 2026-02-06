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
const AiLabStudioView = () => import('../views/AiLabStudioView.vue')
const AiLabLoginView = () => import('../views/AiLabLoginView.vue')
const QuestionGenView = () => import('../views/QuestionGenView.vue')
const PortfolioHomeView = () => import('../views/PortfolioHomeView.vue')
const GamesHubView = () => import('../views/GamesHubView.vue')
const GomokuView = () => import('../views/GomokuView.vue')
const TarotSanctumView = () => import('../views/tarot/TarotSanctumView.vue')
const TarotRitualView = () => import('../views/tarot/TarotRitualView.vue')

// 默认站点标题
const DEFAULT_TITLE = 'LZQ的个人空间'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ========================================
    // Kitchen 模块 - /kitchen 路径下
    // ========================================
    {
      path: '/kitchen',
      name: 'kitchen-home',
      component: HomeView,
      meta: { title: '私房菜谱 | LZQ' }
    },
    {
      path: '/kitchen/my-orders',
      name: 'my-orders',
      component: MyOrdersView,
      meta: { title: '我的订单 | 私房厨房' }
    },
    {
      path: '/kitchen/recipe/:id',
      name: 'recipe-book',
      component: RecipeBookView,
      meta: { title: '菜谱详情 | 私房厨房' }
    },

    // 登录页面（不需要验证）
    {
      path: '/kitchen/chef/login',
      name: 'chef-login',
      component: ChefLoginView,
      meta: { requiresAuth: false, title: '厨师登录' }
    },
    // 以下路由需要登录验证
    {
      path: '/kitchen/chef',
      name: 'chef-landing',
      component: AdminLandingView,
      meta: { requiresAuth: true, title: '管理后台 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/orders',
      name: 'chef-orders',
      component: ChefDashboard,
      meta: { requiresAuth: true, title: '订单管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes',
      name: 'chef-recipes',
      component: RecipeManagerView,
      meta: { requiresAuth: true, title: '菜谱管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes/new',
      name: 'chef-recipe-new',
      component: RecipeEditorView,
      meta: { requiresAuth: true, title: '新建菜谱 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes/:id/edit',
      name: 'chef-recipe-edit',
      component: RecipeEditorView,
      meta: { requiresAuth: true, title: '编辑菜谱 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/inventory',
      name: 'chef-inventory',
      component: InventoryView,
      meta: { requiresAuth: true, title: '库存管理 | 私房厨房' }
    },
    // 博客管理路由（需要登录）
    {
      path: '/kitchen/chef/blog',
      name: 'chef-blog',
      component: BlogManagerView,
      meta: { requiresAuth: true, title: '博客管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/blog/new',
      name: 'chef-blog-new',
      component: BlogEditorView,
      meta: { requiresAuth: true, title: '新建博客 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/blog/:id/edit',
      name: 'chef-blog-edit',
      component: BlogEditorView,
      meta: { requiresAuth: true, title: '编辑博客 | 私房厨房' }
    },

    // ========================================
    // Blog 模块 - /blog 路径下
    // ========================================
    {
      path: '/blog',
      name: 'blog',
      component: BlogListView,
      meta: { title: '技术博客 | LZQ' }
    },
    {
      path: '/blog/:slug',
      name: 'blog-post',
      component: BlogPostView,
      meta: { title: '博客文章 | LZQ' }
    },

    // ========================================
    // QuestionGen 模块 - /questiongen 路径下
    // ========================================
    {
      path: '/questiongen',
      name: 'questiongen',
      component: QuestionGenView,
      meta: { title: 'AI 刷题 | LZQ' }
    },

    // ========================================
    // Tarot 模块 - /tarot 路径下
    // ========================================
    {
      path: '/tarot',
      name: 'tarot',
      component: TarotSanctumView,
      meta: { title: 'Tarot Sanctum | LZQ' }
    },
    {
      path: '/tarot/ritual',
      name: 'tarot-ritual',
      component: TarotRitualView,
      meta: { title: 'Tarot Ritual | LZQ' }
    },

    // ========================================
    // AI Lab 模块 - /ai-lab 路径下 (需要登录)
    // ========================================
    {
      path: '/ai-lab/login',
      name: 'ai-lab-login',
      component: AiLabLoginView,
      meta: { title: 'AI Lab 登录 | LZQ' }
    },
    {
      path: '/ai-lab',
      name: 'ai-lab',
      component: AiLabView,
      meta: { requiresAuth: true, authType: 'ai-lab', title: 'AI Lab | DeepSeek Reasoner' }
    },
    {
      path: '/ai-lab/studio',
      name: 'ai-lab-studio',
      component: AiLabStudioView,
      meta: { requiresAuth: true, authType: 'ai-lab', title: 'AI Studio | LZQ' }
    },

    // ========================================
    // Games 模块 - /games 路径下
    // ========================================
    {
      path: '/games',
      name: 'games-hub',
      component: GamesHubView,
      meta: { title: '联机小游戏 | LZQ' }
    },
    {
      path: '/games/gomoku/:roomId?',
      name: 'games-gomoku',
      component: GomokuView,
      meta: { title: '五子棋联机 | LZQ' }
    },

    // ========================================
    // 根路径 - 个人网站首页
    // ========================================
    {
      path: '/',
      name: 'home',
      component: PortfolioHomeView,
      meta: { title: 'LZQ的个人空间' }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 动态设置页面标题
  document.title = to.meta.title || DEFAULT_TITLE

  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    if (auth.checkAuth()) {
      next() // 已登录，允许访问
    } else {
      // 根据 authType 决定跳转到哪个登录页
      const loginPath = to.meta.authType === 'ai-lab' ? '/ai-lab/login' : '/kitchen/chef/login'
      next({
        path: loginPath,
        query: { redirect: to.fullPath }
      })
    }
  } else {
    next() // 不需要认证，直接访问
  }
})

export default router
