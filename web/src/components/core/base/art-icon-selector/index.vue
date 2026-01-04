<!-- 图标选择器 -->
<template>
  <div class="icon-selector">
    <div
      class="select"
      @click="handleClick"
      :style="{ width: props.width }"
      :class="[size, { 'is-disabled': disabled }, { 'has-icon': selectValue }]"
    >
      <div class="icon">
        <i
          :class="`iconfont-sys ${selectValue}`"
          :style="{ color: iconColors.get(selectValue) }"
          v-show="props.iconType === IconTypeEnum.CLASS_NAME"
        ></i>
        <i
          class="iconfont-sys"
          v-html="selectValue"
          :style="{ color: iconColors.get(selectValue) }"
          v-show="props.iconType === IconTypeEnum.UNICODE"
        ></i>
      </div>
      <div class="text"> {{ props.text }} </div>
      <div class="arrow">
        <i class="iconfont-sys arrow-icon">&#xe709;</i>
        <i class="iconfont-sys clear-icon" @click.stop="clearIcon">&#xe83a;</i>
      </div>
    </div>

    <el-dialog title="选择图标" width="40%" v-model="visible" align-center draggable>
      <el-scrollbar height="400px" ref="scrollbarRef">
        <ul class="icons-list" v-show="activeName === 'icons'">
          <li
            v-for="icon in iconsList"
            :key="icon.className"
            @click="selectorIcon(icon)"
            :class="{ selected: isIconSelected(icon) }"
          >
            <i
              :class="`iconfont-sys ${icon.className}`"
              :style="{ color: iconColors.get(icon.className) }"
              v-show="iconType === IconTypeEnum.CLASS_NAME"
            ></i>
            <i
              class="iconfont-sys"
              v-html="icon.unicode"
              :style="{ color: iconColors.get(icon.className) }"
              v-show="iconType === IconTypeEnum.UNICODE"
            ></i>
          </li>
        </ul>
      </el-scrollbar>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="visible = false">取 消</el-button>
          <el-button type="primary" @click="visible = false">确 定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { IconTypeEnum } from '@/enums/appEnum'
  import { extractIconClasses, type IconfontType } from '@/utils/constants'

  defineOptions({ name: 'ArtIconSelector' })

  // 组件大小类型
  type ComponentSize = 'large' | 'default' | 'small'

  // Props 接口定义
  interface Props {
    /** 图标类型 */
    iconType?: IconTypeEnum
    /** v-model 绑定的图标值 */
    modelValue?: string
    /** 显示文本 */
    text?: string
    /** 组件宽度 */
    width?: string
    /** 组件大小 */
    size?: ComponentSize
    /** 是否禁用 */
    disabled?: boolean
  }

  // Emits 接口定义
  interface Emits {
    'update:modelValue': [value: string]
    getIcon: [value: string]
  }

  // 使用 withDefaults 定义 props
  const props = withDefaults(defineProps<Props>(), {
    iconType: IconTypeEnum.CLASS_NAME,
    modelValue: '',
    text: '图标选择器',
    width: '200px',
    size: 'default',
    disabled: false
  })

  // 定义 emits
  const emits = defineEmits<Emits>()

  // 响应式数据
  const selectValue = ref<string>(props.modelValue)
  const visible = ref<boolean>(false)
  const activeName = ref<string>('icons')
  const scrollbarRef = ref()

  // 图标列表 - 使用计算属性优化性能
  const iconsList = computed<IconfontType[]>(() => extractIconClasses())

  // 为每个图标生成固定的随机颜色（使用计算属性确保颜色稳定）
  const iconColors = computed(() => {
    const colorMap = new Map<string, string>()
    iconsList.value.forEach((icon) => {
      // 使用图标的className作为种子，确保同一个图标总是显示相同的颜色
      const seed = icon.className.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      const colorIndex = seed % 25 // 25个颜色选项
      const colors = [
        '#E53E3E',
        '#D53F8C',
        '#9F7AEA',
        '#667EEA',
        '#4299E1',
        '#0BC5EA',
        '#00B5D8',
        '#38B2AC',
        '#48BB78',
        '#68D391',
        '#9AE6B4',
        '#F6E05E',
        '#ED8936',
        '#F56500',
        '#FF6B6B',
        '#FF5722',
        '#E91E63',
        '#9C27B0',
        '#673AB7',
        '#3F51B5',
        '#2196F3',
        '#03A9F4',
        '#00BCD4',
        '#009688',
        '#4CAF50'
      ]
      colorMap.set(icon.className, colors[colorIndex])
    })
    return colorMap
  })

  // 监听 modelValue 变化
  watch(
    () => props.modelValue,
    (newVal: string) => {
      selectValue.value = newVal
    },
    { immediate: true }
  )

  // 选择图标
  const selectorIcon = (icon: IconfontType): void => {
    const iconValue =
      props.iconType === IconTypeEnum.CLASS_NAME ? icon.className : icon.unicode || ''

    selectValue.value = iconValue
    visible.value = false

    // 发射 v-model 更新事件和自定义事件
    emits('update:modelValue', iconValue)
    emits('getIcon', iconValue)
  }

  // 处理点击事件
  const handleClick = (): void => {
    if (!props.disabled) {
      visible.value = true
      // 打开对话框后自动滚动到已选择的图标
      nextTick(() => {
        scrollToSelectedIcon()
      })
    }
  }

  // 滚动到已选择的图标位置
  const scrollToSelectedIcon = (): void => {
    if (!selectValue.value || !scrollbarRef.value) return

    const selectedIconValue =
      props.iconType === IconTypeEnum.CLASS_NAME
        ? selectValue.value
        : iconsList.value.find((icon) => icon.unicode === selectValue.value)?.className

    if (!selectedIconValue) return

    const iconIndex = iconsList.value.findIndex((icon) =>
      props.iconType === IconTypeEnum.CLASS_NAME
        ? icon.className === selectedIconValue
        : icon.unicode === selectValue.value
    )

    if (iconIndex !== -1) {
      // 添加延迟确保DOM完全渲染
      setTimeout(() => {
        if (!scrollbarRef.value || !scrollbarRef.value.setScrollTop) return

        // 获取图标列表元素
        const iconsListElement = document.querySelector('.icons-list')
        const allIcons = iconsListElement?.querySelectorAll('li')

        if (allIcons && allIcons[iconIndex]) {
          // 获取第一个图标的高度作为标准高度
          const firstIcon = allIcons[0] as HTMLElement
          const iconHeight = firstIcon.getBoundingClientRect().height

          // 计算选中图标所在行（每行10个图标）
          const row = Math.floor(iconIndex / 10)

          // 计算图标行的顶部位置
          const iconRowTop = row * iconHeight

          // 滚动容器高度固定为400px
          const containerHeight = 400

          // 计算让图标行显示在容器中间的滚动位置
          const centeredScrollTop = iconRowTop - containerHeight / 2 + iconHeight / 2

          // 确保滚动位置不小于0
          const finalScrollTop = Math.max(0, centeredScrollTop)

          // 使用专属方法设置滚动位置
          scrollbarRef.value.setScrollTop(finalScrollTop)
        }
      }, 200) // 确保DOM完全渲染
    }
  }

  // 清除图标
  const clearIcon = (): void => {
    selectValue.value = ''

    // 发射 v-model 更新事件和自定义事件
    emits('update:modelValue', '')
    emits('getIcon', '')
  }

  // 计算属性：当前图标类型（用于模板中的判断）
  const iconType = computed<IconTypeEnum>(() => props.iconType)

  // 判断图标是否被选中
  const isIconSelected = (icon: IconfontType): boolean => {
    if (!selectValue.value) return false

    return props.iconType === IconTypeEnum.CLASS_NAME
      ? icon.className === selectValue.value
      : icon.unicode === selectValue.value
  }
</script>

<style lang="scss" scoped>
  .icon-selector {
    width: 100%;

    .select {
      box-sizing: border-box;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: var(--el-component-custom-height);
      padding: 0 15px;
      cursor: pointer;
      border: 1px solid var(--art-border-dashed-color);
      border-radius: calc(var(--custom-radius) / 3 + 2px) !important;
      transition: border 0.3s;

      @media (width <= 500px) {
        width: 100% !important;
      }

      &.large {
        height: 40px;
      }

      &.small {
        height: 24px;
      }

      &:hover:not(.is-disabled).has-icon {
        .arrow-icon {
          display: none;
        }

        .clear-icon {
          display: block !important;
        }
      }

      &:hover {
        border-color: var(--art-text-gray-400);
      }

      .icon {
        display: flex;
        align-items: center;
        width: 20px;
        color: var(--art-gray-700);

        i {
          display: block;
          margin: 0 auto;
          font-size: 16px;
        }
      }

      .text {
        display: flex;
        display: inline-block;
        align-items: center;
        width: 50%;
        font-size: 14px;
        color: var(--art-gray-600);

        @include ellipsis();

        @media (width <= 500px) {
          display: none;
        }
      }

      .arrow {
        display: flex;
        align-items: center;
        height: calc(100% - 2px);

        i {
          font-size: 13px;
          color: var(--art-gray-600);
        }

        .clear-icon {
          display: none;
        }
      }

      &.is-disabled {
        cursor: not-allowed;
        background-color: var(--el-disabled-bg-color);
        border-color: var(--el-border-color-lighter);

        .icon,
        .text,
        .arrow {
          color: var(--el-text-color-placeholder);
        }

        &:hover {
          border-color: var(--el-border-color-lighter);
        }
      }
    }

    .icons-list {
      display: grid;
      grid-template-columns: repeat(10, 1fr);
      border-top: 1px solid var(--art-border-color);
      border-left: 1px solid var(--art-border-color);

      li {
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        aspect-ratio: 1 / 1;
        color: var(--art-gray-600);
        text-align: center;
        border-right: 1px solid var(--art-border-color);
        border-bottom: 1px solid var(--art-border-color);

        &:hover {
          cursor: pointer;
          background: var(--art-gray-100);
        }

        i {
          font-size: 22px;
          color: var(--art-gray-800);
        }

        &.selected {
          background: var(--el-color-primary-light-9);
          border: 2px solid var(--el-color-primary) !important;
          position: relative;
          z-index: 1;

          i {
            transform: scale(1.1);
            transition: transform 0.2s ease;
          }
        }
      }
    }

    .dialog-footer {
      display: flex;
      justify-content: center;
      gap: 12px;
    }
  }
</style>
