import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import 'virtual:uno.css'
import './custom.css'

export default {
  extends: DefaultTheme
} satisfies Theme
