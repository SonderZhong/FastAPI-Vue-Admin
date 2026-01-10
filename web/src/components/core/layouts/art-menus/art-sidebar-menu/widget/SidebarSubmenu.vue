<template>
  <template v-for="item in filteredMenuItems" :key="item.path">
    <!-- 包含子菜单的项目（多于1个子路由时才展开） -->
    <ElSubMenu v-if="hasMultipleChildren(item)" :index="item.path || item.meta.title" :level="level">
      <template #title>
        <MenuItemIcon :icon="item.meta.icon" :color="theme?.iconColor" />
        <span class="menu-name">
          {{ formatMenuTitle(item.meta.title) }}
        </span>
        <div v-if="item.meta.showBadge" class="art-badge" style="right: 10px" />
      </template>

      <SidebarSubmenu
        :list="item.children"
        :is-mobile="isMobile"
        :level="level + 1"
        :theme="theme"
        @close="closeMenu"
      />
    </ElSubMenu>

    <!-- 普通菜单项（包括只有一个子路由的情况） -->
    <ElMenuItem
      v-else
      :index="isExternalLink(item) ? undefined : getMenuItemPath(item)"
      :level-item="level + 1"
      @click="goPage(getMenuItemTarget(item))"
    >
      <MenuItemIcon :icon="item.meta.icon" :color="theme?.iconColor" />
      <div
        v-show="item.meta.showBadge && level === 0 && !menuOpen"
        class="art-badge"
        style="right: 5px"
      />

      <template #title>
        <span class="menu-name">
          {{ formatMenuTitle(getSingleChildTitle(item)) }}
        </span>
        <div v-if="item.meta.showBadge" class="art-badge" />
        <div v-if="item.meta.showTextBadge && (level > 0 || menuOpen)" class="art-text-badge">
          {{ item.meta.showTextBadge }}
        </div>
      </template>
    </ElMenuItem>
  </template>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import type { AppRouteRecord } from '@/types/router'
  import { formatMenuTitle } from '@/router/utils/utils'
  import { handleMenuJump } from '@/utils/navigation'
  import { useSettingStore } from '@/store/modules/setting'

  interface MenuTheme {
    iconColor?: string
  }

  interface Props {
    /** 菜单标题 */
    title?: string
    /** 菜单列表 */
    list?: AppRouteRecord[]
    /** 主题配置 */
    theme?: MenuTheme
    /** 是否为移动端模式 */
    isMobile?: boolean
    /** 菜单层级 */
    level?: number
  }

  interface Emits {
    /** 关闭菜单事件 */
    (e: 'close'): void
  }

  const props = withDefaults(defineProps<Props>(), {
    title: '',
    list: () => [],
    theme: () => ({}),
    isMobile: false,
    level: 0
  })

  const emit = defineEmits<Emits>()

  const settingStore = useSettingStore()

  const { menuOpen } = storeToRefs(settingStore)

  /**
   * 过滤后的菜单项列表
   * 只显示未隐藏的菜单项
   */
  const filteredMenuItems = computed(() => filterRoutes(props.list))

  /**
   * 跳转到指定页面
   * @param item 菜单项数据
   */
  const goPage = (item: AppRouteRecord): void => {
    closeMenu()
    handleMenuJump(item)
  }

  /**
   * 关闭菜单
   * 触发父组件的关闭事件
   */
  const closeMenu = (): void => {
    emit('close')
  }

  /**
   * 递归过滤菜单路由，移除隐藏的菜单项
   * 如果一个父菜单的所有子菜单都被隐藏，则父菜单也会被隐藏
   * @param items 菜单项数组
   * @returns 过滤后的菜单项数组
   */
  const filterRoutes = (items: AppRouteRecord[]): AppRouteRecord[] => {
    return items
      .filter((item) => {
        // 如果当前项被隐藏，直接过滤掉
        if (item.meta.isHide) {
          return false
        }

        // 如果有子菜单，递归过滤子菜单
        if (item.children && item.children.length > 0) {
          const filteredChildren = filterRoutes(item.children)
          // 如果所有子菜单都被过滤掉了，则隐藏父菜单
          return filteredChildren.length > 0
        }

        // 叶子节点且未被隐藏，保留
        return true
      })
      .map((item) => ({
        ...item,
        children: item.children ? filterRoutes(item.children) : undefined
      }))
  }

  /**
   * 判断菜单项是否包含多个可见的子菜单
   * 只有多于1个子路由时才显示为展开菜单
   * @param item 菜单项数据
   * @returns 是否包含多个可见的子菜单
   */
  const hasMultipleChildren = (item: AppRouteRecord): boolean => {
    if (!item.children || item.children.length === 0) {
      return false
    }
    // 递归检查是否有可见的子菜单
    const filteredChildren = filterRoutes(item.children)
    // 只有多于1个子路由时才返回true
    return filteredChildren.length > 1
  }

  /**
   * 判断菜单项是否只有一个子路由
   * @param item 菜单项数据
   * @returns 是否只有一个子路由
   */
  const hasSingleChild = (item: AppRouteRecord): boolean => {
    if (!item.children || item.children.length === 0) {
      return false
    }
    const filteredChildren = filterRoutes(item.children)
    return filteredChildren.length === 1
  }

  /**
   * 获取菜单项的实际跳转目标
   * 如果只有一个子路由，返回该子路由
   * @param item 菜单项数据
   * @returns 实际跳转的菜单项
   */
  const getMenuItemTarget = (item: AppRouteRecord): AppRouteRecord => {
    if (hasSingleChild(item)) {
      const filteredChildren = filterRoutes(item.children!)
      return filteredChildren[0]
    }
    return item
  }

  /**
   * 获取菜单项的路径
   * 如果只有一个子路由，返回该子路由的路径
   * @param item 菜单项数据
   * @returns 菜单项路径
   */
  const getMenuItemPath = (item: AppRouteRecord): string => {
    const target = getMenuItemTarget(item)
    return target.path || target.meta.title
  }

  /**
   * 获取菜单项显示的标题
   * 如果只有一个子路由，返回该子路由的标题
   * @param item 菜单项数据
   * @returns 菜单项标题
   */
  const getSingleChildTitle = (item: AppRouteRecord): string => {
    const target = getMenuItemTarget(item)
    return target.meta.title
  }

  /**
   * 判断是否为外部链接
   * @param item 菜单项数据
   * @returns 是否为外部链接
   */
  const isExternalLink = (item: AppRouteRecord): boolean => {
    return !!(item.meta.link && !item.meta.isIframe)
  }
</script>

<script lang="ts">
  /**
   * 菜单图标组件
   * 用于渲染菜单项的图标
   */
  const MenuItemIcon = defineComponent({
    name: 'MenuItemIcon',
    props: {
      /** 图标内容 */
      icon: {
        type: String,
        default: ''
      },
      /** 图标颜色 */
      color: {
        type: String,
        default: ''
      }
    },
    setup(props) {
      return () =>
        h('i', {
          class: 'menu-icon iconfont-sys',
          style: props.color ? { color: props.color } : undefined,
          innerHTML: props.icon
        })
    }
  })
</script>
