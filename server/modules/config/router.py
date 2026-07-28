# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:53
# @Author : sonder
# @File : config.py
# @Comment : 本程序

from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, Path, Request, Query, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse, DeleteListParams
from modules.config.schema import (
    AddConfigParams,
    GetConfigInfoResponse,
    GetConfigListResponse,
)
from modules.config.service import ConfigService
from utils.response import ResponseUtil

configAPI = APIRouter(
    prefix="/config",
    dependencies=[Depends(AuthController.get_current_user)],
)


class UpdateGroupConfigParams(BaseModel):
    configs: List[Dict[str, str]]


@configAPI.get(
    "/groups",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取所有配置分组",
)
@Log(title="获取配置分组", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list"])
async def get_config_groups(request: Request):
    dynamic_config = request.app.state.dynamic_config
    groups = await dynamic_config.get_all_groups()
    return ResponseUtil.success(data=groups)


@configAPI.get(
    "/group/{group}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取分组配置",
)
@Log(title="获取分组配置", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list"])
async def get_group_configs(
    request: Request, group: str = Path(description="配置分组")
):
    from modules import SystemConfig

    configs = await SystemConfig.filter(group=group, is_del=False).values(
        "id", "key", "name", "value", "type", "remark"
    )
    return ResponseUtil.success(data=configs)


@configAPI.put(
    "/group/{group}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量更新分组配置",
)
@configAPI.post(
    "/group/{group}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量更新分组配置",
)
@Log(title="批量更新分组配置", operation_type=OperationType.UPDATE)
@Auth(permission_list=["config:btn:update"])
async def update_group_configs(
    request: Request,
    params: UpdateGroupConfigParams,
    group: str = Path(description="配置分组"),
):
    dynamic_config = request.app.state.dynamic_config
    await ConfigService.batch_update_group_configs(
        group, params.configs, dynamic_config
    )
    return ResponseUtil.success(msg="配置更新成功")


@configAPI.post(
    "/refresh",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="刷新配置缓存",
)
@Log(title="刷新配置缓存", operation_type=OperationType.OTHER)
@Auth(permission_list=["config:btn:update"])
async def refresh_config_cache(request: Request):
    dynamic_config = request.app.state.dynamic_config
    await dynamic_config.refresh_from_db()
    return ResponseUtil.success(msg="配置缓存已刷新")


@configAPI.post(
    "/add", response_class=JSONResponse, response_model=BaseResponse, summary="新增配置"
)
@Log(title="新增配置", operation_type=OperationType.INSERT)
@Auth(permission_list=["config:btn:add"])
async def add_config(request: Request, params: AddConfigParams):
    success, msg = await ConfigService.create_config(params.dict(exclude_unset=True))
    if success:
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.load_all_to_redis()
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@configAPI.delete(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除配置",
)
@configAPI.post(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除配置",
)
@Log(title="删除配置", operation_type=OperationType.DELETE)
@Auth(permission_list=["config:btn:delete"])
async def delete_config(request: Request, id: str = Path(description="配置ID")):
    from modules import SystemConfig

    config = await SystemConfig.get_or_none(id=id, is_del=False)
    if config:
        config.is_del = True
        await config.save()
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.refresh_from_db()
        return ResponseUtil.success(msg="删除成功")
    return ResponseUtil.error(msg="配置不存在")


@configAPI.delete(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除配置",
)
@configAPI.post(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除配置",
)
@Log(title="批量删除配置", operation_type=OperationType.DELETE)
@Auth(permission_list=["config:btn:delete"])
async def delete_config_list(request: Request, params: DeleteListParams):
    await ConfigService.batch_delete_config(params.ids)
    dynamic_config = request.app.state.dynamic_config
    await dynamic_config.refresh_from_db()
    return ResponseUtil.success(msg="删除成功")


@configAPI.put(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="修改配置",
)
@configAPI.post(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="修改配置",
)
@Log(title="修改配置", operation_type=OperationType.UPDATE)
@Auth(permission_list=["config:btn:update"])
async def update_config(
    request: Request, params: AddConfigParams, id: str = Path(description="配置ID")
):
    success, msg = await ConfigService.update_config(
        id, params.dict(exclude_unset=True)
    )
    if success:
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.refresh_from_db()
        return ResponseUtil.success(msg=msg)
    return ResponseUtil.error(msg=msg)


@configAPI.get(
    "/info/{id}",
    response_class=JSONResponse,
    response_model=GetConfigInfoResponse,
    summary="获取配置信息",
)
@Log(title="获取配置信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:info"])
async def get_config_info(request: Request, id: str = Path(description="配置ID")):
    data = await ConfigService.get_config_info(id)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="配置不存在")


@configAPI.get(
    "/list",
    response_class=JSONResponse,
    response_model=GetConfigListResponse,
    summary="获取配置列表",
)
@Log(title="获取配置列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["config:btn:list"])
async def get_config_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    key: Optional[str] = Query(default=None, description="配置键名"),
    name: Optional[str] = Query(default=None, description="配置名称"),
    group: Optional[str] = Query(default=None, description="配置分组"),
    type: Optional[str] = Query(default=None, description="系统内置"),
):
    filter_args = {
        f"{k}__contains": v
        for k, v in {
            "name": name,
            "key": key,
        }.items()
        if v is not None
    }
    if group:
        filter_args["group"] = group
    if type is not None:
        filter_args["type"] = type == "true" or type == "1"

    data, total = await ConfigService.get_config_list(page, pageSize, filter_args)
    return ResponseUtil.success(
        data={
            "total": total,
            "result": data,
            "page": page,
            "pageSize": pageSize,
        }
    )


# ==================== 导入导出 API ====================


@configAPI.get("/export", response_class=JSONResponse, summary="导出配置数据")
@Log(title="导出配置数据", operation_type=OperationType.EXPORT)
@Auth(permission_list=["config:btn:export"])
async def export_config(
    request: Request,
    name: Optional[str] = Query(default=None, description="配置名称"),
    key: Optional[str] = Query(default=None, description="配置键名"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse

    filter_args = {}
    if name:
        filter_args["name__contains"] = name
    if key:
        filter_args["key__contains"] = key

    excel_file = await ConfigService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=config.xlsx"},
    )


@configAPI.get(
    "/export/template", response_class=JSONResponse, summary="下载配置导入模板"
)
@Log(title="下载配置导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=["config:btn:import"])
async def download_config_template(request: Request):
    from fastapi.responses import StreamingResponse

    template_file = ConfigService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=config_template.xlsx"},
    )


@configAPI.post(
    "/import",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="导入配置数据",
)
@Log(title="导入配置数据", operation_type=OperationType.IMPORT)
@Auth(permission_list=["config:btn:import"])
async def import_config(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    content = await file.read()
    success_count, fail_count, errors = await ConfigService.import_from_excel(
        content, current_user_id=current_user.get("id")
    )
    if success_count > 0:
        dynamic_config = request.app.state.dynamic_config
        await dynamic_config.load_all_to_redis()
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(
        msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors}
    )
