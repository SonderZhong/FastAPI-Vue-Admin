<template>
  <span class="count-up">{{ displayValue }}</span>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

interface Props {
  endValue: number
  duration?: number
  startValue?: number
}

const props = withDefaults(defineProps<Props>(), {
  duration: 1500,
  startValue: 0
})

const displayValue = ref(props.startValue)

const animate = () => {
  const start = props.startValue
  const end = props.endValue
  const duration = props.duration
  const startTime = Date.now()

  const updateValue = () => {
    const currentTime = Date.now()
    const elapsed = currentTime - startTime

    if (elapsed < duration) {
      const progress = elapsed / duration
      // 使用easeOutQuart缓动函数
      const easeProgress = 1 - Math.pow(1 - progress, 4)
      displayValue.value = Math.floor(start + (end - start) * easeProgress)
      requestAnimationFrame(updateValue)
    } else {
      displayValue.value = end
    }
  }

  requestAnimationFrame(updateValue)
}

watch(() => props.endValue, () => {
  animate()
})

onMounted(() => {
  animate()
})
</script>

<style lang="scss" scoped>
.count-up {
  display: inline-block;
}
</style>

