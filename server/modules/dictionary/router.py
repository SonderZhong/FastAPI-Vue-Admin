# _*_ coding : UTF-8 _*_
# @Time : 2026/04/06 01:08
# @Author : sonder
# @File : dictionary.py
# @Comment : 数据字典管理 API - 包含字典和字典项

from typing import Optional

from fastapi import APIRouter, Request, Depends, Path, Query, File, UploadFile
from starlette.responses import JSONResponse

from core.common import BaseResponse, DeleteListParams
from modules.dictionary.schema import (
    AddDictionaryParams,
    UpdateDictionaryParams,
    GetDictionaryInfoResponse,
    GetDictionaryListResponse,
    AddDictionaryItemParams,
    UpdateDictionaryItemParams,
    GetDictionaryItemInfoResponse,
    GetDictionaryItemListResponse,
)
from modules.dictionary.service import DictionaryService, DictionaryItemService
from utils.get_redis import RedisKeyConfig
from utils.response import ResponseUtil
from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from utils.log import logger

dictionaryAPI = APIRouter(prefix="/dictionary")


# ==================== 数据字典 API ====================


@dictionaryAPI.post(
    "/add",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="新增数据字典",
)
@Log(title="新增数据字典", operation_type=OperationType.INSERT)
@Auth(permission_list=["dictionary:btn:add"])
async def add_dictionary(
    request: Request,
    params: AddDictionaryParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        success, msg = await DictionaryService.create_dictionary(
            params.dict(exclude_unset=True), request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"新增数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"添加失败：{str(e)}")


@dictionaryAPI.delete(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除数据字典",
)
@dictionaryAPI.post(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除数据字典",
)
@Log(title="删除数据字典", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionary:btn:delete"])
async def delete_dictionary(
    request: Request,
    id: str = Path(..., description="数据字典ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        success, msg = await DictionaryService.delete_dictionary(
            id, request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"删除数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"删除失败：{str(e)}")


@dictionaryAPI.delete(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除数据字典",
)
@dictionaryAPI.post(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除数据字典",
)
@Log(title="批量删除数据字典", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionary:btn:delete"])
async def delete_dictionary_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        deleted_count, msg = await DictionaryService.batch_delete_dictionary(
            params.ids, request.app.state.redis
        )
        return ResponseUtil.success(msg=msg)
    except Exception as e:
        logger.error(f"批量删除数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"批量删除失败：{str(e)}")


@dictionaryAPI.put(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="更新数据字典",
)
@dictionaryAPI.post(
    "/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="更新数据字典",
)
@Log(title="更新数据字典", operation_type=OperationType.UPDATE)
@Auth(permission_list=["dictionary:btn:update"])
async def update_dictionary(
    request: Request,
    params: UpdateDictionaryParams,
    id: str = Path(..., description="数据字典ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        update_data = params.dict(exclude_unset=True, exclude_none=True)
        success, msg = await DictionaryService.update_dictionary(
            id, update_data, request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"更新数据字典失败: {str(e)}")
        return ResponseUtil.error(msg=f"更新失败：{str(e)}")


@dictionaryAPI.get(
    "/info/{id}",
    response_class=JSONResponse,
    response_model=GetDictionaryInfoResponse,
    summary="获取数据字典信息",
)
@Log(title="获取数据字典信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionary:btn:info"])
async def get_dictionary_info(
    request: Request,
    id: str = Path(..., description="数据字典ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        data = await DictionaryService.get_dictionary_info(id, request.app.state.redis)
        if data:
            return ResponseUtil.success(data=data)
        return ResponseUtil.error(msg="数据字典不存在！")
    except Exception as e:
        logger.error(f"获取数据字典信息失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典信息失败：{str(e)}")


@dictionaryAPI.get(
    "/list",
    response_class=JSONResponse,
    response_model=GetDictionaryListResponse,
    summary="获取数据字典列表",
)
@Log(title="获取数据字典列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionary:btn:list"])
async def get_dictionary_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    dict_name: Optional[str] = Query(default=None, description="字典名称"),
    dict_code: Optional[str] = Query(default=None, description="字典编码"),
    remark: Optional[str] = Query(default=None, description="备注"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        redis = request.app.state.redis
        cache_params = f"{page}:{pageSize}:{dict_name or ''}:{dict_code or ''}:{remark or ''}"
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:list:{cache_params}"

        cached_data = await DictionaryService.get_list_from_cache(redis, cache_key)
        if cached_data:
            return ResponseUtil.success(data=cached_data)

        filter_args = {}
        if dict_name:
            filter_args["dict_name__contains"] = dict_name
        if dict_code:
            filter_args["dict_code__contains"] = dict_code
        if remark:
            filter_args["remark__contains"] = remark

        result, total = await DictionaryService.get_dictionary_list(
            page, pageSize, filter_args
        )
        response_data = {
            "result": result,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }

        await DictionaryService.set_list_to_cache(redis, cache_key, response_data)
        return ResponseUtil.success(data=response_data)
    except Exception as e:
        logger.error(f"获取数据字典列表失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典列表失败：{str(e)}")


@dictionaryAPI.post(
    "/cache/refresh",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="刷新字典缓存",
)
@Log(title="刷新字典缓存", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionary:btn:cache"])
async def refresh_dictionary_cache(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        redis = request.app.state.redis
        await DictionaryService.clear_list_cache(redis)
        return ResponseUtil.success(msg="字典缓存已刷新！")
    except Exception as e:
        logger.error(f"刷新字典缓存失败: {str(e)}")
        return ResponseUtil.error(msg=f"刷新缓存失败：{str(e)}")


@dictionaryAPI.get(
    "/code/{code}", response_class=JSONResponse, summary="根据编码获取字典项列表"
)
@Log(title="根据编码获取字典项", operation_type=OperationType.SELECT)
async def get_dictionary_by_code(
    request: Request,
    code: str = Path(..., description="字典编码"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        result = await DictionaryService.get_dictionary_by_code(
            code, request.app.state.redis
        )
        if result is None:
            return ResponseUtil.error(msg="字典不存在！")
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f"根据编码获取字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取字典项失败：{str(e)}")


# ==================== 数据字典项 API ====================


@dictionaryAPI.post(
    "/item/add",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="新增数据字典项",
)
@Log(title="新增数据字典项", operation_type=OperationType.INSERT)
@Auth(permission_list=["dictionaryitem:btn:add"])
async def add_dictionary_item(
    request: Request,
    params: AddDictionaryItemParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        success, msg = await DictionaryItemService.create_item(
            params.dict(exclude_unset=True), request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"新增数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"添加失败：{str(e)}")


@dictionaryAPI.delete(
    "/item/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除数据字典项",
)
@dictionaryAPI.post(
    "/item/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除数据字典项",
)
@Log(title="删除数据字典项", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionaryitem:btn:delete"])
async def delete_dictionary_item(
    request: Request,
    id: str = Path(..., description="数据字典项ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        success, msg = await DictionaryItemService.delete_item(
            id, request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"删除数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"删除失败：{str(e)}")


@dictionaryAPI.delete(
    "/item/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除数据字典项",
)
@dictionaryAPI.post(
    "/item/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除数据字典项",
)
@Log(title="批量删除数据字典项", operation_type=OperationType.DELETE)
@Auth(permission_list=["dictionaryitem:btn:delete"])
async def delete_dictionary_item_list(
    request: Request,
    params: DeleteListParams,
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        deleted_count, msg = await DictionaryItemService.batch_delete_item(
            params.ids, request.app.state.redis
        )
        return ResponseUtil.success(msg=msg)
    except Exception as e:
        logger.error(f"批量删除数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"批量删除失败：{str(e)}")


@dictionaryAPI.put(
    "/item/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="更新数据字典项",
)
@dictionaryAPI.post(
    "/item/update/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="更新数据字典项",
)
@Log(title="更新数据字典项", operation_type=OperationType.UPDATE)
@Auth(permission_list=["dictionaryitem:btn:update"])
async def update_dictionary_item(
    request: Request,
    params: UpdateDictionaryItemParams,
    id: str = Path(..., description="数据字典项ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        update_data = params.dict(exclude_unset=True, exclude_none=True)
        success, msg = await DictionaryItemService.update_item(
            id, update_data, request.app.state.redis
        )
        if success:
            return ResponseUtil.success(msg=msg)
        return ResponseUtil.error(msg=msg)
    except Exception as e:
        logger.error(f"更新数据字典项失败: {str(e)}")
        return ResponseUtil.error(msg=f"更新失败：{str(e)}")


@dictionaryAPI.get(
    "/item/info/{id}",
    response_class=JSONResponse,
    response_model=GetDictionaryItemInfoResponse,
    summary="获取数据字典项信息",
)
@Log(title="获取数据字典项信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionaryitem:btn:info"])
async def get_dictionary_item_info(
    request: Request,
    id: str = Path(..., description="数据字典项ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        data = await DictionaryItemService.get_item_info(id)
        if data:
            return ResponseUtil.success(data=data)
        return ResponseUtil.error(msg="数据字典项不存在！")
    except Exception as e:
        logger.error(f"获取数据字典项信息失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典项信息失败：{str(e)}")


@dictionaryAPI.get(
    "/item/list",
    response_class=JSONResponse,
    response_model=GetDictionaryItemListResponse,
    summary="获取数据字典项列表",
)
@Log(title="获取数据字典项列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["dictionaryitem:btn:list"])
async def get_dictionary_item_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=10, description="每页数量"),
    dictionary_id: Optional[str] = Query(default=None, description="所属字典ID"),
    label: Optional[str] = Query(default=None, description="字典项标签"),
    value: Optional[str] = Query(default=None, description="字典项值"),
    tag_color: Optional[str] = Query(default=None, description="标签颜色"),
    remark: Optional[str] = Query(default=None, description="备注"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    try:
        filter_args = {}
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

        result, total = await DictionaryItemService.get_item_list(
            page, pageSize, filter_args
        )
        return ResponseUtil.success(
            data={"result": result, "total": total, "page": page, "pageSize": pageSize}
        )
    except Exception as e:
        logger.error(f"获取数据字典项列表失败: {str(e)}")
        return ResponseUtil.error(msg=f"获取数据字典项列表失败：{str(e)}")


# ==================== 导入导出 API ====================


@dictionaryAPI.get("/export", response_class=JSONResponse, summary="导出数据字典")
@Log(title="导出数据字典", operation_type=OperationType.EXPORT)
@Auth(permission_list=["dictionary:btn:export"])
async def export_dictionary(
    request: Request,
    dict_name: Optional[str] = Query(default=None, description="字典名称"),
    dict_code: Optional[str] = Query(default=None, description="字典编码"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse

    filter_args = {}
    if dict_name:
        filter_args["dict_name__contains"] = dict_name
    if dict_code:
        filter_args["dict_code__contains"] = dict_code

    excel_file = await DictionaryService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dictionary.xlsx"},
    )


@dictionaryAPI.get(
    "/export/template", response_class=JSONResponse, summary="下载数据字典导入模板"
)
@Log(title="下载数据字典导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=["dictionary:btn:import"])
async def download_dictionary_template(request: Request):
    from fastapi.responses import StreamingResponse

    template_file = DictionaryService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=dictionary_template.xlsx"
        },
    )


@dictionaryAPI.post(
    "/import",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="导入数据字典",
)
@Log(title="导入数据字典", operation_type=OperationType.IMPORT)
@Auth(permission_list=["dictionary:btn:import"])
async def import_dictionary(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    content = await file.read()
    success_count, fail_count, errors = await DictionaryService.import_from_excel(
        content, current_user_id=current_user.get("id")
    )
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(
        msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors}
    )


@dictionaryAPI.get(
    "/item/export", response_class=JSONResponse, summary="导出数据字典项"
)
@Log(title="导出数据字典项", operation_type=OperationType.EXPORT)
@Auth(permission_list=["dictionaryitem:btn:export"])
async def export_dictionary_item(
    request: Request,
    dictionary_id: Optional[str] = Query(default=None, description="所属字典ID"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    from fastapi.responses import StreamingResponse

    filter_args = {}
    if dictionary_id:
        filter_args["dictionary_id"] = dictionary_id

    excel_file = await DictionaryItemService.export_to_excel(filters=filter_args)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dictionary_item.xlsx"},
    )


@dictionaryAPI.get(
    "/item/export/template",
    response_class=JSONResponse,
    summary="下载数据字典项导入模板",
)
@Log(title="下载数据字典项导入模板", operation_type=OperationType.EXPORT)
@Auth(permission_list=["dictionaryitem:btn:import"])
async def download_dictionary_item_template(request: Request):
    from fastapi.responses import StreamingResponse

    template_file = DictionaryItemService.get_import_template()
    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=dictionary_item_template.xlsx"
        },
    )


@dictionaryAPI.post(
    "/item/import",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="导入数据字典项",
)
@Log(title="导入数据字典项", operation_type=OperationType.IMPORT)
@Auth(permission_list=["dictionaryitem:btn:import"])
async def import_dictionary_item(
    request: Request,
    file: UploadFile = File(..., description="Excel文件"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    content = await file.read()
    success_count, fail_count, errors = await DictionaryItemService.import_from_excel(
        content, current_user_id=current_user.get("id")
    )
    msg = f"导入完成，成功 {success_count} 条，失败 {fail_count} 条"
    if errors:
        msg += f"。错误信息：{'; '.join(errors[:5])}"
    return ResponseUtil.success(
        msg=msg, data={"success": success_count, "fail": fail_count, "errors": errors}
    )
