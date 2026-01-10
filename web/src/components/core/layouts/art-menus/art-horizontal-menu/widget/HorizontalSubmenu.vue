<template>
  <!-- 有多个子菜单时显示为展开菜单 -->
  <ElSubMenu v-if="hasMultipleChildren" :index="item.path || item.meta.title">
    <template #title>
      <i
        class="menu-icon iconfont-sys"
        :style="{ color: theme?.iconColor }"
        v-html="item.meta.icon"
      ></i>
      <span>{{ formatMenuTitle(item.meta.title) }}</span>
      <div v-if="item.meta.showBadge" class="art-badge art-badge-horizontal" />
      <div v-if="item.meta.showTextBadge" class="art-text-badge">
        {{ item.meta.showTextBadge }}
      </div>
    </template>

    <!-- 递归调用自身处理子菜单 -->
    <HorizontalSubmenu
      v-for="child in filteredChildren"
      :key="child.path"
      :item="child"
      :theme="theme"
      :is-mobile="isMobile"
      :level="level + 1"
      @close="closeMenu"
    />
  </ElSubMenu>

  <!-- 普通菜单项（包括只有一个子路由的情况） -->
  <ElMenuItem
    v-else-if="!item.meta.isHide"
    :index="getMenuItemPath"
    @click="goPage(getMenuItemTarget)"
  >
    <i
      class="menu-icon iconfont-sys"
      :style="{ color: theme?.iconColor }"
      v-html="item.meta.icon"
    ></i>
    <span>{{ formatMenuTitle(getSingleChildTitle) }}</span>
    <div
      v-if="item.meta.showBadge"
      class="art-badge"
      :style="{ right: level === 0 ? '10px' : '20px' }"
    />
    <div v-if="item.meta.showTextBadge && level !== 0" class="art-text-badge">
      {{ item.meta.showTextBadge }}
    </div>
  </ElMenuItem>
</template>

<script lang="ts" setup>
  import { computed, type PropType } from 'vue'
  import { AppRouteRecord } from '@/types/router'
  import { handleMenuJump } from '@/utils/navigation'
  import { formatMenuTitle } from '@/router/utils/utils'

  const props = defineProps({
    item: {
      type: Object as PropType<AppRouteRecord>,
      required: true
    },
    theme: {
      type: Object,
      default: () => ({})
    },
    isMobile: Boolean,
    level: {
      type: Number,
      default: 0
    }
  })

  const emit = defineEmits(['close'])

  // 过滤后的子菜单项（不包含隐藏的）
  const filteredChildren = computed(() => {
    return props.item.children?.filter((child) => !child.meta.isHide) || []
  })

  // 计算当前项是否有多个可见的子菜单（只有多于1个时才展开）
  const hasMultipleChildren = computed(() => {
    return filteredChildren.value.length > 1
  })

  // 判断是否只有一个子路由
  const hasSingleChild = computed(() => {
    return filteredChildren.value.length === 1
  })

  // 获取菜单项的实际跳转目标
  const getMenuItemTarget = computed(() => {
    if (hasSingleChild.value) {
      return filteredChildren.value[0]
    }
    return props.item
  })

  // 获取菜单项的路径
  const getMenuItemPath = computed(() => {
    const target = getMenuItemTarget.value
    return target.path || target.meta.title
  })

  // 获取菜单项显示的标题
  const getSingleChildTitle = computed(() => {
    const target = getMenuItemTarget.value
    return target.meta.title
  })

  const goPage = (item: AppRouteRecord) => {
    closeMenu()
    handleMenuJump(item)
  }

  const closeMenu = () => {
    emit('close')
  }
</script>

<style lang="scss" scoped>
  .el-sub-menu {
    padding: 0 !important;

    :deep(.el-sub-menu__title) {
      .el-sub-menu__icon-arrow {
        right: 10px !important;
      }
    }
  }

  .menu-icon {
    margin-right: 5px;
    font-size: 16px;
  }
</style>
