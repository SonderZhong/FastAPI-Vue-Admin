import { computed, ref } from 'vue'
import { fetchDictionaryByCode, type DictionaryItemInfo } from '@/api/system/dictionary'

const dictionaryCache = new Map<string, DictionaryItemInfo[]>()
const dictionaryLoadingMap = new Map<string, Promise<DictionaryItemInfo[]>>()

export function useDictionary(code: string) {
  const items = ref<DictionaryItemInfo[]>(dictionaryCache.get(code) || [])
  const loading = ref(false)

  const load = async (force = false) => {
    if (!force && dictionaryCache.has(code)) {
      items.value = dictionaryCache.get(code) || []
      return items.value
    }

    if (!force && dictionaryLoadingMap.has(code)) {
      loading.value = true
      items.value = await dictionaryLoadingMap.get(code)!
      loading.value = false
      return items.value
    }

    loading.value = true
    const requestPromise = fetchDictionaryByCode(code)
      .then((res) => {
        const result = res.data || []
        dictionaryCache.set(code, result)
        return result
      })
      .finally(() => {
        dictionaryLoadingMap.delete(code)
      })

    dictionaryLoadingMap.set(code, requestPromise)
    items.value = await requestPromise
    loading.value = false
    return items.value
  }

  const getLabel = (value: string | number | undefined | null, fallback = '-') => {
    if (value === undefined || value === null || value === '') {
      return fallback
    }
    const matched = items.value.find((item) => String(item.value) === String(value))
    return matched?.label || fallback
  }

  const getTagColor = (value: string | number | undefined | null) => {
    const matched = items.value.find((item) => String(item.value) === String(value))
    return matched?.tag_color
  }

  const options = computed(() =>
    items.value.map((item) => ({
      label: item.label,
      value: Number.isNaN(Number(item.value)) ? item.value : Number(item.value),
      rawValue: item.value,
      tagColor: item.tag_color
    }))
  )

  return {
    items,
    options,
    loading,
    load,
    getLabel,
    getTagColor
  }
}

export function clearDictionaryCache(code?: string) {
  if (code) {
    dictionaryCache.delete(code)
    dictionaryLoadingMap.delete(code)
    return
  }
  dictionaryCache.clear()
  dictionaryLoadingMap.clear()
}
