# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:53
# @UpdateTime : 2025/08/25 02:53
# @Author : sonder
# @File : config.py
# @Software : PyCharm
# @Comment : 本程序

from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, Path, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from models import SystemConfig
from models.config import ConfigGroup
from schemas.common import BaseResponse, DeleteListParams
from schemas.config import AddConfigParams, GetConfigInfoResponse, GetConfigListResponse
from utils.response import ResponseUtil

configAPI = APIRouter(
    prefix="/config",
    dependencies=[Depends(AuthController.get_current_user)],
)


# ==================== 分组配置 API ====================

class UpdateGroupConfigParams(BaseModel):
    """批量更新分组配置参数"""
    configs: List[Dict[str, str]]  # [{key: value}, ...]


@configAPI.get("/groups", response_class=JSONResponse, response_model=BaseResponse, summary="获取所有配置分组")
@Log(title="获取配置分组", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list", "GET:/config/groups"])
async def get_config_groups(request: Request):
    """获取所有配置分组及其配置项"""
    dynamic_config = request.app.state.dynamic_config
    groups = await dynamic_config.get_all_groups()
    return ResponseUtil.success(data=groups)


@configAPI.get("/group/{group}", response_class=JSONResponse, response_model=BaseResponse, summary="获取分组配置")
@Log(title="获取分组配置", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list", "GET:/config/group/*"])
async def get_group_configs(request: Request, group: str = Path(description="配置分组")):
    """获取指定分组的所有配置"""
    configs = await SystemConfig.filter(group=group, is_del=False).values(
        "id", "key", "name", "value", "type", "remark"
    )
    return ResponseUtil.success(data=configs)


@configAPI.put("/group/{group}", response_class=JSONResponse, response_model=BaseResponse, summary="批量更新分组配置")
@configAPI.post("/group/{group}", response_class=JSONResponse, response_model=BaseResponse, summary="批量更新分组配置")
@Log(title="批量更新分组配置", operation_type=OperationType.UPDATE)
@Auth(permission_list=["config:btn:update", "PUT,POST:/config/group/*"])
async def update_group_configs(
    request: Request,
    params: UpdateGroupConfigParams,
    group: str = Path(description="配置分组")
):
    """批量更新指定分组的配置"""
    dynamic_config = request.app.state.dynamic_config
    
    for cfg in params.configs:
        key = cfg.get("key")
        value = cfg.get("value")
        if key and value is not None:
            await dynamic_config.set(key, str(value))
    
    return ResponseUtil.success(msg="配置更新成功")


@configAPI.post("/refresh", response_class=JSONResponse, response_model=BaseResponse, summary="刷新配置缓存")
@Log(title="刷新配置缓存", operation_type=OperationType.OTHER)
@Auth(permission_list=["config:btn:update", "POST:/config/refresh"])
async def refresh_config_cache(request: Request):
    """从数据库刷新所有配置到 Redis"""
    dynamic_config = request.app.state.dynamic_config
    await dynamic_config.refresh_from_db()
    return ResponseUtil.success(msg="配置缓存已刷新")


# ==================== 原有配置 API ====================


@configAPI.post("/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增配置")
@Log(title="新增配置", operation_type=OperationType.INSERT)
@Auth(permission_list=["config:btn:add", "POST:/config/add"])
async def add_config(request: Request, params: AddConfigParams):
    if await SystemConfig.get_or_none(key=params.key, is_del=False):
        return ResponseUtil.error(msg="配置键名已存在")
    config = await SystemConfig.create(
        name=params.name,
        key=params.key,
        value=params.value,
        group=getattr(params, 'group', ConfigGroup.SYSTEM),
        remark=params.remark,
        type=params.type,
    )
    if config:
        # 同步到 Redis
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.load_all_to_redis()
        return ResponseUtil.success(msg="新增成功")
    else:
        return ResponseUtil.error(msg="新增失败")


@configAPI.delete("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除配置")
@configAPI.post("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除配置")
@Log(title="删除配置", operation_type=OperationType.DELETE)
@Auth(permission_list=["config:btn:delete", "DELETE,POST:/config/delete/*"])
async def delete_config(request: Request, id: str = Path(description="配置ID")):
    if config := await SystemConfig.get_or_none(id=id, is_del=False):
        config.is_del = True
        await config.save()
        # 同步到 Redis
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.refresh_from_db()
        return ResponseUtil.success(msg="删除成功")
    else:
        return ResponseUtil.error(msg="配置不存在")


@configAPI.delete("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除配置")
@configAPI.post("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除配置")
@Log(title="批量删除配置", operation_type=OperationType.DELETE)
@Auth(permission_list=["config:btn:delete", "DELETE,POST:/config/deleteList"])
async def delete_config_list(request: Request, params: DeleteListParams):
    await SystemConfig.filter(id__in=list(set(params.ids)), is_del=False).update(is_del=True)
    # 同步到 Redis
    dynamic_config = request.app.state.dynamic_config
    await dynamic_config.refresh_from_db()
    return ResponseUtil.success(msg="删除成功")


@configAPI.put("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="修改配置")
@configAPI.post("/update/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="修改配置")
@Log(title="修改配置", operation_type=OperationType.UPDATE)
@Auth(permission_list=["config:btn:update", "PUT,POST:/config/update/*"])
async def update_config(request: Request, params: AddConfigParams, id: str = Path(description="配置ID")):
    if config := await SystemConfig.get_or_none(id=id, is_del=False):
        config.name = params.name
        config.key = params.key
        config.value = params.value
        config.remark = params.remark
        config.type = params.type
        if hasattr(params, 'group') and params.group:
            config.group = params.group
        await config.save()
        # 同步到 Redis
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.refresh_from_db()
        return ResponseUtil.success(msg="修改成功")
    else:
        return ResponseUtil.error(msg="配置不存在")


@configAPI.get("/info/{id}", response_class=JSONResponse, response_model=GetConfigInfoResponse, summary="获取配置信息")
@Log(title="获取配置信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:info", "GET:/config/info/*"])
async def get_config_info(request: Request, id: str = Path(description="配置ID")):
    if config := await SystemConfig.get_or_none(id=id, is_del=False):
        data = {
            "id": config.id,
            "name": config.name,
            "key": config.key,
            "value": config.value,
            "remark": config.remark,
            "type": config.type,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
        return ResponseUtil.success(data=data)
    else:
        return ResponseUtil.error(msg="配置不存在")


@configAPI.get("/list", response_class=JSONResponse, response_model=GetConfigListResponse, summary="获取配置列表")
@Log(title="获取配置列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list", "GET:/config/list"])
async def get_config_list(request: Request,
                          page: int = Query(default=1, description="当前页码"),
                          pageSize: int = Query(default=10, description="每页数量"),
                          key: Optional[str] = Query(default=None, description="配置键名"),
                          name: Optional[str] = Query(default=None, description="配置名称"),
                          group: Optional[str] = Query(default=None, description="配置分组"),
                          type: Optional[str] = Query(default=None, description="系统内置"),
                          ):
    filterArgs = {
        f'{k}__contains': v for k, v in {
            'name': name,
            'key': key,
        }.items() if v is not None
    }
    if group:
        filterArgs['group'] = group
    if type is not None:
        filterArgs['type'] = type == 'true' or type == '1'
    
    total = await SystemConfig.filter(**filterArgs, is_del=False).count()
    data = await SystemConfig.filter(**filterArgs, is_del=False).offset((page - 1) * pageSize).limit(pageSize).values(
        id="id",
        name="name",
        key="key",
        value="value",
        group="group",
        remark="remark",
        type="type",
        created_at="created_at",
        updated_at="updated_at"
    )
    return ResponseUtil.success(data={
        "total": total,
        "result": data,
        "page": page,
        "pageSize": pageSize,
    })
