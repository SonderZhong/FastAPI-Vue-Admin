import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'FastAPI-Vue-Admin',
  description: '基于 FastAPI + Vue 3 的现代化后台管理系统模板',
  lang: 'zh-CN',
  base: '/FastAPI-Vue-Admin/',
  
  ignoreDeadLinks: [
    /^http:\/\/localhost/,
    /^http:\/\/127\.0\.0\.1/
  ],
  
  sitemap: {
    hostname: 'https://sonderzhong.github.io/FastAPI-Vue-Admin/'
  },
  
  head: [
    ['link', { rel: 'icon', href: '/FastAPI-Vue-Admin/favicon.ico' }]
  ],

  markdown: {
    lineNumbers: true
  },

  themeConfig: {
    logo: '/logo.png',
    
    nav: [
      { text: '指南', link: '/guide/', activeMatch: '/guide/' },
      { text: '配置', link: '/config/', activeMatch: '/config/' },
      { text: 'API', link: '/api/', activeMatch: '/api/' },
      {
        text: '相关链接',
        items: [
          { text: 'GitHub', link: 'https://github.com/SonderZhong/FastAPI-Vue-Admin' },
          { text: '在线演示', link: 'https://fva.hygc.site' },
          { text: 'Art Design Pro', link: 'https://github.com/Daymychen/art-design-pro' },
          { text: 'FastAPI', link: 'https://fastapi.tiangolo.com' },
          { text: 'Vue 3', link: 'https://vuejs.org' }
        ]
      }
    ],

    sidebar: {
      '/guide/': [
        {
          text: '开始',
          items: [
            { text: '项目介绍', link: '/guide/' },
            { text: '快速开始', link: '/guide/getting-started' },
            { text: '项目结构', link: '/guide/structure' }
          ]
        },
        {
          text: '后端指南',
          items: [
            { text: '后端知识库', link: '/guide/backend' },
            { text: '权限控制', link: '/guide/permission' },
            { text: 'MCP 服务', link: '/guide/mcp' }
          ]
        },
        {
          text: '前端指南',
          items: [
            { text: '前端知识库', link: '/guide/frontend' },
            { text: '路由和菜单', link: '/guide/router' },
            { text: '请求和接口', link: '/guide/request' }
          ]
        },
        {
          text: '部署运维',
          items: [
            { text: '部署指南', link: '/guide/deploy' }
          ]
        }
      ],
      '/config/': [
        {
          text: '配置',
          items: [
            { text: '后端配置', link: '/config/' },
            { text: '前端配置', link: '/config/frontend' },
            { text: '环境变量', link: '/config/env' }
          ]
        }
      ],
      '/api/': [
        {
          text: 'API 参考',
          items: [
            { text: '认证接口', link: '/api/' },
            { text: '用户管理', link: '/api/user' },
            { text: '角色管理', link: '/api/role' },
            { text: '权限管理', link: '/api/permission' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/SonderZhong/FastAPI-Vue-Admin' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026 SonderZhong'
    },

    search: {
      provider: 'local'
    },

    outline: {
      level: [2, 3],
      label: '页面导航'
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    lastUpdated: {
      text: '最后更新于'
    }
  }
})
