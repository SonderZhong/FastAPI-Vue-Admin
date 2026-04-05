/**
 * 数据字典管理 API
 */

import request from '@/utils/http'

/** 数据字典信息接口 */
export interface DictionaryInfo {
    /** 字典ID */
    id: string
    /** 字典名称 */
    dict_name: string
    /** 字典编码 */
    dict_code: string
    /** 字典类型 */
    dict_type: string
    /** 状态：0-禁用，1-启用 */
    status: number
    /** 排序 */
    sort: number
    /** 备注 */
    remark?: string
    /** 创建时间 */
    created_at: string
    /** 更新时间 */
    updated_at: string
}

/** 数据字典项信息接口 */
export interface DictionaryItemInfo {
    /** 字典项ID */
    id: string
    /** 所属字典ID */
    dictionary_id: string
    /** 字典项标签 */
    label: string
    /** 字典项值 */
    value: string
    /** 状态：0-禁用，1-启用 */
    status: number
    /** 排序 */
    sort: number
    /** 标签颜色 */
    tag_color?: string
    /** 备注 */
    remark?: string
    /** 创建时间 */
    created_at: string
    /** 更新时间 */
    updated_at: string
}

/** 数据字典查询参数 */
export interface DictionaryQueryParams {
    /** 当前页码 */
    page?: number
    /** 每页数量 */
    pageSize?: number
    /** 字典名称 */
    dict_name?: string
    /** 字典编码 */
    dict_code?: string
    /** 字典类型 */
    dict_type?: string
    /** 备注 */
    remark?: string
}

/** 数据字典项查询参数 */
export interface DictionaryItemQueryParams {
    /** 当前页码 */
    page?: number
    /** 每页数量 */
    pageSize?: number
    /** 所属字典ID */
    dictionary_id?: string
    /** 字典项标签 */
    label?: string
    /** 字典项值 */
    value?: string
    /** 标签颜色 */
    tag_color?: string
    /** 备注 */
    remark?: string
}

/** 新增数据字典参数 */
export interface AddDictionaryParams {
    /** 字典名称 */
    dict_name: string
    /** 字典编码 */
    dict_code: string
    /** 字典类型 */
    dict_type: string
    /** 状态：0-禁用，1-启用 */
    status?: number
    /** 排序 */
    sort?: number
    /** 备注 */
    remark?: string
}

/** 更新数据字典参数 */
export interface UpdateDictionaryParams {
    /** 字典名称 */
    dict_name?: string
    /** 字典编码 */
    dict_code?: string
    /** 字典类型 */
    dict_type?: string
    /** 状态：0-禁用，1-启用 */
    status?: number
    /** 排序 */
    sort?: number
    /** 备注 */
    remark?: string
}

/** 新增数据字典项参数 */
export interface AddDictionaryItemParams {
    /** 所属字典ID */
    dictionary_id: string
    /** 字典项标签 */
    label: string
    /** 字典项值 */
    value: string
    /** 状态：0-禁用，1-启用 */
    status?: number
    /** 排序 */
    sort?: number
    /** 标签颜色 */
    tag_color?: string
    /** 备注 */
    remark?: string
}

/** 更新数据字典项参数 */
export interface UpdateDictionaryItemParams {
    /** 所属字典ID */
    dictionary_id?: string
    /** 字典项标签 */
    label?: string
    /** 字典项值 */
    value?: string
    /** 状态：0-禁用，1-启用 */
    status?: number
    /** 排序 */
    sort?: number
    /** 标签颜色 */
    tag_color?: string
    /** 备注 */
    remark?: string
}

/** 数据字典列表响应数据 */
export interface DictionaryListResponse {
    /** 字典列表 */
    result: DictionaryInfo[]
    /** 总数 */
    total: number
    /** 当前页码 */
    page: number
    /** 每页大小 */
    pageSize: number
}

/** 数据字典项列表响应数据 */
export interface DictionaryItemListResponse {
    /** 字典项列表 */
    result: DictionaryItemInfo[]
    /** 总数 */
    total: number
    /** 当前页码 */
    page: number
    /** 每页大小 */
    pageSize: number
}

/**
 * 获取数据字典列表
 */
export const fetchDictionaryList = (params?: DictionaryQueryParams) =>
    request.get<DictionaryListResponse>({
        url: '/api/dictionary/list',
        params
    })

/**
 * 获取数据字典详情
 */
export const fetchDictionaryInfo = (id: string) =>
    request.get<DictionaryInfo>({
        url: `/api/dictionary/info/${id}`
    })

/**
 * 新增数据字典
 */
export const addDictionary = (data: AddDictionaryParams) =>
    request.post<null>({
        url: '/api/dictionary/add',
        data
    })

/**
 * 更新数据字典
 */
export const updateDictionary = (id: string, data: UpdateDictionaryParams) =>
    request.post<null>({
        url: `/api/dictionary/update/${id}`,
        data
    })

/**
 * 删除数据字典
 */
export const deleteDictionary = (id: string) =>
    request.post<null>({
        url: `/api/dictionary/delete/${id}`
    })

/**
 * 批量删除数据字典
 */
export const deleteDictionaryList = (ids: string[]) =>
    request.post<null>({
        url: '/api/dictionary/deleteList',
        data: { ids }
    })

/**
 * 根据字典编码获取字典项列表（常用接口，带缓存）
 */
export const fetchDictionaryByCode = (code: string) =>
    request.get<DictionaryItemInfo[]>({
        url: `/api/dictionary/code/${code}`
    })

/**
 * 获取数据字典项列表
 */
export const fetchDictionaryItemList = (params?: DictionaryItemQueryParams) =>
    request.get<DictionaryItemListResponse>({
        url: '/api/dictionary/item/list',
        params
    })

/**
 * 获取数据字典项详情
 */
export const fetchDictionaryItemInfo = (id: string) =>
    request.get<DictionaryItemInfo>({
        url: `/api/dictionary/item/info/${id}`
    })

/**
 * 新增数据字典项
 */
export const addDictionaryItem = (data: AddDictionaryItemParams) =>
    request.post<null>({
        url: '/api/dictionary/item/add',
        data
    })

/**
 * 更新数据字典项
 */
export const updateDictionaryItem = (id: string, data: UpdateDictionaryItemParams) =>
    request.post<null>({
        url: `/api/dictionary/item/update/${id}`,
        data
    })

/**
 * 删除数据字典项
 */
export const deleteDictionaryItem = (id: string) =>
    request.post<null>({
        url: `/api/dictionary/item/delete/${id}`
    })

/**
 * 批量删除数据字典项
 */
export const deleteDictionaryItemList = (ids: string[]) =>
    request.post<null>({
        url: '/api/dictionary/item/deleteList',
        data: { ids }
    })
