import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // DeerFlow 对话请求可能耗时数十秒，放宽代理超时避免被提前掐断
        timeout: 130000,
        proxyTimeout: 130000
      }
    }
  }
})
