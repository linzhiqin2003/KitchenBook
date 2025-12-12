import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    chunkSizeWarningLimit: 600, // 降低警告阈值
    rollupOptions: {
      output: {
        // 手动分割代码块，将大型依赖单独打包
        manualChunks: {
          // Vue 核心库
          'vue-vendor': ['vue', 'vue-router'],
          // Markdown 解析
          'markdown': ['marked'],
          // 其他大型库可以按需添加
        },
        // 优化 chunk 命名
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  optimizeDeps: {
    include: ['page-flip']
  }
})
