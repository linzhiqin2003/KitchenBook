import { createRouter, createWebHistory } from 'vue-router'

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
const AuthView = () => import('../views/AuthView.vue')
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
    // 公开页面
    // ========================================
    {
      path: '/',
      name: 'home',
      component: PortfolioHomeView,
      meta: { public: true, title: 'LZQ的个人空间' }
    },
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      meta: { public: true, title: '登录 | LZQ Space' }
    },

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

    // 厨师登录页面（需要 JWT 登录，但不需要厨师密码）
    {
      path: '/kitchen/chef/login',
      name: 'chef-login',
      component: ChefLoginView,
      meta: { title: '厨师登录' }
    },
    // 以下路由需要厨师密码验证
    {
      path: '/kitchen/chef',
      name: 'chef-landing',
      component: AdminLandingView,
      meta: { requiresAuth: true, authType: 'chef', title: '管理后台 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/orders',
      name: 'chef-orders',
      component: ChefDashboard,
      meta: { requiresAuth: true, authType: 'chef', title: '订单管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes',
      name: 'chef-recipes',
      component: RecipeManagerView,
      meta: { requiresAuth: true, authType: 'chef', title: '菜谱管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes/new',
      name: 'chef-recipe-new',
      component: RecipeEditorView,
      meta: { requiresAuth: true, authType: 'chef', title: '新建菜谱 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/recipes/:id/edit',
      name: 'chef-recipe-edit',
      component: RecipeEditorView,
      meta: { requiresAuth: true, authType: 'chef', title: '编辑菜谱 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/inventory',
      name: 'chef-inventory',
      component: InventoryView,
      meta: { requiresAuth: true, authType: 'chef', title: '库存管理 | 私房厨房' }
    },
    // 博客管理路由（需要厨师密码）
    {
      path: '/kitchen/chef/blog',
      name: 'chef-blog',
      component: BlogManagerView,
      meta: { requiresAuth: true, authType: 'chef', title: '博客管理 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/blog/new',
      name: 'chef-blog-new',
      component: BlogEditorView,
      meta: { requiresAuth: true, authType: 'chef', title: '新建博客 | 私房厨房' }
    },
    {
      path: '/kitchen/chef/blog/:id/edit',
      name: 'chef-blog-edit',
      component: BlogEditorView,
      meta: { requiresAuth: true, authType: 'chef', title: '编辑博客 | 私房厨房' }
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
    // AI Lab 模块 - /ai-lab 路径下
    // ========================================
    {
      path: '/ai-lab',
      name: 'ai-lab',
      component: AiLabView,
      meta: { title: 'AI Lab | DeepSeek Reasoner' }
    },
    {
      path: '/ai-lab/studio',
      name: 'ai-lab-studio',
      component: AiLabStudioView,
      meta: { title: 'AI Studio | LZQ' }
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
  ]
})

// 路由守卫
let initPromise = null

router.beforeEach(async (to, from, next) => {
  // 动态设置页面标题
  document.title = to.meta.title || DEFAULT_TITLE

  // Lazy-import auth store (Pinia must be installed by this point)
  const { useAuthStore } = await import('../store/auth')
  const authStore = useAuthStore()

  // Initialize auth state once
  if (!initPromise) {
    initPromise = authStore.init()
  }
  await initPromise

  const isPublic = to.meta.public === true

  // Public routes — let through; redirect logged-in users away from /login
  if (isPublic) {
    if (to.path === '/login' && authStore.isLoggedIn) {
      return next(to.query.redirect ? String(to.query.redirect) : '/kitchen')
    }
    return next()
  }

  // All non-public routes require JWT login
  if (!authStore.isLoggedIn) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // Chef routes require second-level auth
  if (to.meta.authType === 'chef') {
    if (!authStore.checkChefAuth()) {
      return next({ path: '/kitchen/chef/login', query: { redirect: to.fullPath } })
    }
  }

  next()
})

export default router
