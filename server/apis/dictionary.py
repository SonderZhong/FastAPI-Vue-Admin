# _*_ coding : UTF-8 _*_
# @Time : 2026/04/06 01:08
# @Author : sonder
# @File : dictionary.py
# @Comment : 数据字典管理 API - 包含字典和字典项

import json
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Path, Query
from starlette.responses import JSONResponse

from models import SystemDictionary, SystemDictionaryItem
from schemas.common import BaseResponse, DeleteListParams
from schemas.dictionary import (
    AddDictionaryParams, UpdateDictionaryParams, GetDictionaryInfoResponse, GetDictionaryListResponse,
    AddDictionaryItemParams, UpdateDictionaryItemParams, GetDictionaryItemInfoResponse, GetDictionaryItemListResponse
)
from utils.casbin import CasbinEnforcer, DataScope
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil
from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from exceptions.exception import ServiceException
from utils.log import logger

dictionaryAPI = APIRouter(prefix="/dictionary")


# ==================== 字典缓存工具函数 ====================

async def get_dictionary_from_cache(redis, dict_id: str):
    """从缓存获取字典信息"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}'
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def set_dictionary_to_cache(redis, dict_id: str, data: dict, expire: int = 3600):
    """设置字典信息到缓存"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}'
    await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)


async def delete_dictionary_cache(redis, dict_id: str):
    """删除字典缓存"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}'
    await redis.delete(cache_key)


async def get_dictionary_list_from_cache(redis, cache_key: str):
    """从缓存获取字典列表"""
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def set_dictionary_list_to_cache(redis, cache_key: str, data: dict, expire: int = 600):
    """设置字典列表到缓存"""
    await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)


async def clear_dictionary_list_cache(redis):
    """清除所有字典列表缓存"""
    pattern = f'{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:list:*'
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)


async def get_dictionary_items_from_cache(redis, dict_id: str):
    """从缓存获取字典项列表"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}'
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def set_dictionary_items_to_cache(redis, dict_id: str, data: list, expire: int = 3600):
    """设置字典项列表到缓存"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}'
    await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)


async def clear_dictionary_items_cache(redis, dict_id: str):
    """清除字典项缓存"""
    cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}'
    await redis.delete(cache_key)


# ==================== 数据字典 API ====================

@dictionaryAPI.post("/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增数据字典")
@Log(title="新增数据字典", operation_type=OperationType.INSERT)
@Auth(permission_list=["dictionary:btn:add", "POST:/dictionary/add"])
async def add_dictionary(
        request: Request,
        params: AddDictionaryParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """新增数据字典"""
    try:
        # 检查编码是否已存在
        existing = await SystemDictionary.get_or_none(dict_code=params.dict_code, is_del=False)
        if existing:
            return ResponseUtil.error(msg="添加失败，字典编码已存在！")
        
        # 创建记录
        result = await SystemDictionary.create(**params.dict(exclude_unset=True))
        if result:
            # 清除列表缓存
            await clear_dictionary_list_cache(request.app.state.redis)
            return ResponseUtil.success(msg="添加成功！")
        else:
            return ResponseUtil.error(msg="添加失败！")
    except Exception as e:
        logger.error(f"新增数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"添加失败：{str(e)}")


@dictionaryAPI.delete("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除数据字典")
@dictionaryAPI.post("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除数据字典")
@Log(title="删除数据字典", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionary:btn:delete", "DELETE,POST:/dictionary/delete/*"])
async def delete_dictionary(
        request: Request,
        id: str = Path(..., description="数据字典ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """删除数据字典（级联删除字典项）"""
    try:
        record = await SystemDictionary.get_or_none(id=id, is_del=False)
        if not record:
            return ResponseUtil.error(msg="删除失败，数据字典不存在！")
        
        # 软删除字典
        record.is_del = True
        await record.save()
        
        # 软删除所有字典项
        await SystemDictionaryItem.filter(dictionary_id=id, is_del=False).update(is_del=True)
        
        # 清除缓存
        await delete_dictionary_cache(request.app.state.redis, id)
        await clear_dictionary_items_cache(request.app.state.redis, id)
        await clear_dictionary_list_cache(request.app.state.redis)
        
        return ResponseUtil.success(msg="删除成功！")
    except Exception as e:
        logger.error(f"删除数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"删除失败：{str(e)}")


@dictionaryAPI.delete("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除数据字典")
@dictionaryAPI.post("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除数据字典")
@Log(title="批量删除数据字典", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionary:btn:delete", "DELETE,POST:/dictionary/deleteList"])
async def delete_dictionary_list(
        request: Request,
        params: DeleteListParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """批量删除数据字典"""
    try:
        deleted_count = 0
        for record_id in set(params.ids):
            record = await SystemDictionary.get_or_none(id=record_id, is_del=False)
            if record:
                record.is_del = True
                await record.save()
                # 软删除所有字典项
                await SystemDictionaryItem.filter(dictionary_id=record_id, is_del=False).update(is_del=True)
                # 清除缓存
                await delete_dictionary_cache(request.app.state.redis, record_id)
                await clear_dictionary_items_cache(request.app.state.redis, record_id)
                deleted_count += 1
        
        # 清除列表缓存
        await clear_dictionary_list_cache(request.app.state.redis)
        
        return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个数据字典！")
    except Exception as e:
        logger.error(f"批量删除数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"批量删除失败：{str(e)}")


@dictionaryAPI.put("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新数据字典")
@dictionaryAPI.post("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新数据字典")
@Log(title="更新数据字典", operation_type=OperationType.UPDATE)
@Auth(permission_list=["dictionary:btn:update", "PUT,POST:/dictionary/update/*"])
async def update_dictionary(
        request: Request,
        params: UpdateDictionaryParams,
        id: str = Path(..., description="数据字典ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """更新数据字典"""
    try:
        record = await SystemDictionary.get_or_none(id=id, is_del=False)
        if not record:
            return ResponseUtil.error(msg="更新失败，数据字典不存在！")
        
        # 更新字段
        update_data = params.dict(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await record.save()
        
        # 清除缓存
        await delete_dictionary_cache(request.app.state.redis, id)
        await clear_dictionary_list_cache(request.app.state.redis)
        
        return ResponseUtil.success(msg="更新成功！")
    except Exception as e:
        logger.error(f"更新数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"更新失败：{str(e)}")


@dictionaryAPI.get("/info/{id}", response_class=JSONResponse, response_model=GetDictionaryInfoResponse, summary="获取数据字典信息")
@Log(title="获取数据字典信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionary:btn:info", "GET:/dictionary/info/*"])
async def get_dictionary_info(
        request: Request,
        id: str = Path(..., description="数据字典ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取数据字典信息（带缓存）"""
    try:
        # 尝试从缓存获取
        cached_data = await get_dictionary_from_cache(request.app.state.redis, id)
        if cached_data:
            return ResponseUtil.success(data=cached_data)
        
        # 从数据库查询
        record = await SystemDictionary.get_or_none(id=id, is_del=False)
        if record:
            data = {
                "id": str(record.id),
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "dict_name": record.dict_name,
                "dict_code": record.dict_code,
                "dict_type": record.dict_type,
                "status": record.status,
                "sort": record.sort,
                "remark": record.remark,
            }
            # 设置缓存
            await set_dictionary_to_cache(request.app.state.redis, id, data)
            return ResponseUtil.success(data=data)
        else:
            return ResponseUtil.error(msg="数据字典不存在！")
    except Exception as e:
        logger.error(f"获取数据字典信息失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典信息失败：{str(e)}")


@dictionaryAPI.get("/list", response_class=JSONResponse, response_model=GetDictionaryListResponse, summary="获取数据字典列表")
@Log(title="获取数据字典列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionary:btn:list", "GET:/dictionary/list"])
async def get_dictionary_list(
        request: Request,
        page: int = Query(default=1, description="当前页码"),
        pageSize: int = Query(default=10, description="每页数量"),
        dict_name: Optional[str] = Query(default=None, description="字典名称"),
        dict_code: Optional[str] = Query(default=None, description="字典编码"),
        dict_type: Optional[str] = Query(default=None, description="字典类型"),
        remark: Optional[str] = Query(default=None, description="备注"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取数据字典列表（带缓存）"""
    try:
        # 构建缓存键
        cache_params = f"{page}:{pageSize}:{dict_name or ''}:{dict_code or ''}:{dict_type or ''}:{remark or ''}"
        cache_key = f'{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:list:{cache_params}'
        
        # 尝试从缓存获取
        cached_data = await get_dictionary_list_from_cache(request.app.state.redis, cache_key)
        if cached_data:
            return ResponseUtil.success(data=cached_data)
        
        # 构建过滤条件
        filter_args = {"is_del": False}
        
        # 添加搜索条件
        if dict_name:
            filter_args["dict_name__contains"] = dict_name
        if dict_code:
            filter_args["dict_code__contains"] = dict_code
        if dict_type:
            filter_args["dict_type__contains"] = dict_type
        if remark:
            filter_args["remark__contains"] = remark
        
        # 查询总数
        total = await SystemDictionary.filter(**filter_args).count()
        
        # 分页查询
        records = await SystemDictionary.filter(**filter_args).offset((page - 1) * pageSize).limit(pageSize).all()
        
        # 转换数据格式
        result = []
        for record in records:
            data = {
                "id": str(record.id),
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "dict_name": record.dict_name,
                "dict_code": record.dict_code,
                "dict_type": record.dict_type,
                "status": record.status,
                "sort": record.sort,
                "remark": record.remark,
            }
            result.append(data)
        
        response_data = {
            "result": result,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
        
        # 设置缓存
        await set_dictionary_list_to_cache(request.app.state.redis, cache_key, response_data)
        
        return ResponseUtil.success(data=response_data)
    except Exception as e:
        logger.error(f"获取数据字典列表失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典列表失败：{str(e)}")


@dictionaryAPI.get("/code/{code}", response_class=JSONResponse, summary="根据编码获取字典项列表")
@Log(title="根据编码获取字典项", operation_type=OperationType.SELECT)
async def get_dictionary_by_code(
        request: Request,
        code: str = Path(..., description="字典编码"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """根据字典编码获取字典项列表（带缓存，常用接口）"""
    try:
        # 先查询字典
        dictionary = await SystemDictionary.get_or_none(dict_code=code, is_del=False)
        if not dictionary:
            return ResponseUtil.error(msg="字典不存在！")
        
        # 尝试从缓存获取字典项
        cached_items = await get_dictionary_items_from_cache(request.app.state.redis, str(dictionary.id))
        if cached_items:
            return ResponseUtil.success(data=cached_items)
        
        # 从数据库查询字典项
        items = await SystemDictionaryItem.filter(
            dictionary_id=dictionary.id,
            is_del=False,
            status=1
        ).order_by('sort', '-created_at').all()
        
        # 转换数据格式
        result = []
        for item in items:
            data = {
                "id": str(item.id),
                "label": item.label,
                "value": item.value,
                "status": item.status,
                "sort": item.sort,
                "tag_color": item.tag_color,
                "remark": item.remark,
            }
            result.append(data)
        
        # 设置缓存
        await set_dictionary_items_to_cache(request.app.state.redis, str(dictionary.id), result)
        
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f"根据编码获取字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取字典项失败：{str(e)}")


# ==================== 数据字典项 API ====================

@dictionaryAPI.post("/item/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增数据字典项")
@Log(title="新增数据字典项", operation_type=OperationType.INSERT)
@Auth(permission_list=["dictionaryitem:btn:add", "POST:/dictionary/item/add"])
async def add_dictionary_item(
        request: Request,
        params: AddDictionaryItemParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """新增数据字典项"""
    try:
        # 检查字典是否存在
        dictionary = await SystemDictionary.get_or_none(id=params.dictionary_id, is_del=False)
        if not dictionary:
            return ResponseUtil.error(msg="添加失败，所属字典不存在！")
        
        # 创建记录（将 dictionary_id 替换为 dictionary 对象）
        data = params.dict(exclude_unset=True)
        data['dictionary_id'] = dictionary
        result = await SystemDictionaryItem.create(**data)
        if result:
            # 清除字典项缓存
            await clear_dictionary_items_cache(request.app.state.redis, params.dictionary_id)
            return ResponseUtil.success(msg="添加成功！")
        else:
            return ResponseUtil.error(msg="添加失败！")
    except Exception as e:
        logger.error(f"新增数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"添加失败：{str(e)}")


@dictionaryAPI.delete("/item/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除数据字典项")
@dictionaryAPI.post("/item/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除数据字典项")
@Log(title="删除数据字典项", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionaryitem:btn:delete", "DELETE,POST:/dictionary/item/delete/*"])
async def delete_dictionary_item(
        request: Request,
        id: str = Path(..., description="数据字典项ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """删除数据字典项"""
    try:
        record = await SystemDictionaryItem.get_or_none(id=id, is_del=False)
        if not record:
            return ResponseUtil.error(msg="删除失败，数据字典项不存在！")
        
        dict_id = str(record.dictionary_id_id)
        
        # 软删除
        record.is_del = True
        await record.save()
        
        # 清除缓存
        await clear_dictionary_items_cache(request.app.state.redis, dict_id)
        
        return ResponseUtil.success(msg="删除成功！")
    except Exception as e:
        logger.error(f"删除数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"删除失败：{str(e)}")


@dictionaryAPI.delete("/item/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除数据字典项")
@dictionaryAPI.post("/item/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除数据字典项")
@Log(title="批量删除数据字典项", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionaryitem:btn:delete", "DELETE,POST:/dictionary/item/deleteList"])
async def delete_dictionary_item_list(
        request: Request,
        params: DeleteListParams,
        current_user: dict = Depends(AuthController.get_current_user)
):
    """批量删除数据字典项"""
    try:
        deleted_count = 0
        dict_ids = set()
        for record_id in set(params.ids):
            record = await SystemDictionaryItem.get_or_none(id=record_id, is_del=False)
            if record:
                dict_ids.add(str(record.dictionary_id_id))
                record.is_del = True
                await record.save()
                deleted_count += 1
        
        # 清除缓存
        for dict_id in dict_ids:
            await clear_dictionary_items_cache(request.app.state.redis, dict_id)
        
        return ResponseUtil.success(msg=f"删除成功，共删除 {deleted_count} 个数据字典项！")
    except Exception as e:
        logger.error(f"批量删除数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"批量删除失败：{str(e)}")


@dictionaryAPI.put("/item/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新数据字典项")
@dictionaryAPI.post("/item/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="更新数据字典项")
@Log(title="更新数据字典项", operation_type=OperationType.UPDATE)
@Auth(permission_list=["dictionaryitem:btn:update", "PUT,POST:/dictionary/item/update/*"])
async def update_dictionary_item(
        request: Request,
        params: UpdateDictionaryItemParams,
        id: str = Path(..., description="数据字典项ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """更新数据字典项"""
    try:
        record = await SystemDictionaryItem.get_or_none(id=id, is_del=False)
        if not record:
            return ResponseUtil.error(msg="更新失败，数据字典项不存在！")
        
        dict_id = str(record.dictionary_id_id)
        
        # 更新字段
        update_data = params.dict(exclude_unset=True, exclude_none=True)
        
        # 如果更新了 dictionary_id，需要转换为对象
        if 'dictionary_id' in update_data and update_data['dictionary_id']:
            dictionary = await SystemDictionary.get_or_none(id=update_data['dictionary_id'], is_del=False)
            if not dictionary:
                return ResponseUtil.error(msg="更新失败，所属字典不存在！")
            update_data['dictionary_id'] = dictionary
            dict_id = str(dictionary.id)  # 更新缓存清除的字典ID
        
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await record.save()
        
        # 清除缓存
        await clear_dictionary_items_cache(request.app.state.redis, dict_id)
        
        return ResponseUtil.success(msg="更新成功！")
    except Exception as e:
        logger.error(f"更新数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"更新失败：{str(e)}")


@dictionaryAPI.get("/item/info/{id}", response_class=JSONResponse, response_model=GetDictionaryItemInfoResponse, summary="获取数据字典项信息")
@Log(title="获取数据字典项信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionaryitem:btn:info", "GET:/dictionary/item/info/*"])
async def get_dictionary_item_info(
        request: Request,
        id: str = Path(..., description="数据字典项ID"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取数据字典项信息"""
    try:
        record = await SystemDictionaryItem.get_or_none(id=id, is_del=False).prefetch_related('dictionary_id')
        if record:
            data = {
                "id": str(record.id),
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "dictionary_id": str(record.dictionary_id_id) if record.dictionary_id_id else None,
                "label": record.label,
                "value": record.value,
                "status": record.status,
                "sort": record.sort,
                "tag_color": record.tag_color,
                "remark": record.remark,
            }
            return ResponseUtil.success(data=data)
        else:
            return ResponseUtil.error(msg="数据字典项不存在！")
    except Exception as e:
        logger.error(f"获取数据字典项信息失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典项信息失败：{str(e)}")


@dictionaryAPI.get("/item/list", response_class=JSONResponse, response_model=GetDictionaryItemListResponse, summary="获取数据字典项列表")
@Log(title="获取数据字典项列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionaryitem:btn:list", "GET:/dictionary/item/list"])
async def get_dictionary_item_list(
        request: Request,
        page: int = Query(default=1, description="当前页码"),
        pageSize: int = Query(default=10, description="每页数量"),
        dictionary_id: Optional[str] = Query(default=None, description="所属字典ID"),
        label: Optional[str] = Query(default=None, description="字典项标签"),
        value: Optional[str] = Query(default=None, description="字典项值"),
        tag_color: Optional[str] = Query(default=None, description="标签颜色"),
        remark: Optional[str] = Query(default=None, description="备注"),
        current_user: dict = Depends(AuthController.get_current_user)
):
    """获取数据字典项列表"""
    try:
        # 构建过滤条件
        filter_args = {"is_del": False}
        
        # 添加搜索条件
        if dictionary_id:
            filter_args["dictionary_id"] = dictionary_id
        if label:
            filter_args["label__contains"] = label
        if value:
            filter_args["value__contains"] = value
        if tag_color:
            filter_args["tag_color__contains"] = tag_color
        if remark:
            filter_args["remark__contains"] = remark
        
        # 查询总数
        total = await SystemDictionaryItem.filter(**filter_args).count()
        
        # 分页查询（预加载外键关系）
        records = await SystemDictionaryItem.filter(**filter_args).prefetch_related('dictionary_id').offset((page - 1) * pageSize).limit(pageSize).all()
        
        # 转换数据格式
        result = []
        for record in records:
            data = {
                "id": str(record.id),
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                "dictionary_id": str(record.dictionary_id_id) if record.dictionary_id_id else None,
                "label": record.label,
                "value": record.value,
                "status": record.status,
                "sort": record.sort,
                "tag_color": record.tag_color,
                "remark": record.remark,
            }
            result.append(data)
        
        return ResponseUtil.success(data={
            "result": result,
            "total": total,
            "page": page,
            "pageSize": pageSize
        })
    except Exception as e:
        logger.error(f"获取数据字典项列表失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典项列表失败：{str(e)}")
