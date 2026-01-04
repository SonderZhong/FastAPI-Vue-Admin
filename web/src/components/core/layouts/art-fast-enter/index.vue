<!-- 顶部快速入口面板 -->
<template>
  <ElPopover
    ref="popoverRef"
    :width="700"
    trigger="hover"
    popper-class="fast-enter-popover"
    :show-arrow="false"
    placement="bottom-start"
    :offset="0"
    :popper-style="{
      border: '1px solid var(--art-border-dashed-color)',
      borderRadius: 'calc(var(--custom-radius) / 2 + 4px)'
    }"
  >
    <template #reference>
      <div class="fast-enter-trigger">
        <div class="btn">
          <i class="iconfont-sys">&#xe81a;</i>
        </div>
      </div>
    </template>

    <div class="fast-enter">
      <div class="apps-section">
        <div class="apps-grid">
          <!-- 应用列表 -->
          <div
            v-for="application in enabledApplications"
            :key="application.name"
            class="app-item"
            @click="handleApplicationClick(application)"
          >
            <div class="app-icon" :style="{ backgroundColor: `${application.iconColor}15` }">
              <i
                class="iconfont-sys"
                v-html="application.icon"
                :style="{ color: application.iconColor }"
              />
            </div>
            <div class="app-info">
              <h3>{{ translateText(application.name) }}</h3>
              <p>{{ translateText(application.description) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="quick-links">
        <h3>{{ $t('fastEnter.quickLinks.title', '快速链接') }}</h3>
        <ul>
          <li
            v-for="quickLink in enabledQuickLinks"
            :key="quickLink.name"
            @click="handleQuickLinkClick(quickLink)"
          >
            <i v-if="quickLink.icon" class="iconfont-sys link-icon" v-html="quickLink.icon"></i>
            <span>{{ translateText(quickLink.name) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </ElPopover>
</template>

<script setup lang="ts">
  import { useFastEnter } from '@/composables/useFastEnter'
  import type { FastEnterApplication, FastEnterQuickLink } from '@/types/config'
  import { useI18n } from 'vue-i18n'

  defineOptions({ name: 'ArtFastEnter' })

  const router = useRouter()
  const popoverRef = ref()
  const { t } = useI18n()

  // 使用快速入口配置
  const { enabledApplications, enabledQuickLinks } = useFastEnter()

  /**
   * 翻译文本，支持国际化key和普通文本
   * @param text 文本或国际化key
   */
  const translateText = (text: string | undefined): string => {
    if (!text) return ''

    // 如果是国际化key（包含点号），尝试翻译
    if (text.includes('.')) {
      const translated = t(text)
      // 如果翻译失败（返回原key），尝试提取最后一部分作为备用
      return translated !== text ? translated : text.split('.').pop() || text
    }

    // 否则直接返回文本
    return text
  }

  /**
   * 处理导航跳转
   * @param routeName 路由名称
   * @param path 路由路径
   * @param link 外部链接
   */
  const handleNavigate = (routeName?: string, path?: string, link?: string): void => {
    const targetPath = routeName || path || link

    if (!targetPath) {
      console.warn('导航配置无效：缺少路由名称或链接')
      return
    }

    if (targetPath.startsWith('http')) {
      window.open(targetPath, '_blank')
    } else {
      // 优先使用 path 进行路由跳转，其次使用 routeName
      if (path) {
        router.push(path)
      } else if (routeName) {
        router.push({ name: routeName })
      } else {
        router.push(targetPath)
      }
    }

    popoverRef.value?.hide()
  }

  /**
   * 处理应用项点击
   * @param application 应用配置对象
   */
  const handleApplicationClick = (application: FastEnterApplication): void => {
    handleNavigate(application.routeName, application.path, application.link)
  }

  /**
   * 处理快速链接点击
   * @param quickLink 快速链接配置对象
   */
  const handleQuickLinkClick = (quickLink: FastEnterQuickLink): void => {
    handleNavigate(quickLink.routeName, quickLink.path, quickLink.link)
  }
</script>

<style lang="scss" scoped>
  @use './style';
</style>
