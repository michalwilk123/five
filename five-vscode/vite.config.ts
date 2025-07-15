import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/extension.ts'),
      name: 'five-code-agent',
      fileName: 'extension',
      formats: ['cjs']
    },
    outDir: 'out',
    rollupOptions: {
      external: ['vscode'],
      output: {
        globals: {
          vscode: 'vscode'
        }
      }
    },
    target: 'node16',
    minify: false,
    sourcemap: true
  }
}) 