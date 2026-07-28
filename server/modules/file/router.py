# _*_ coding : UTF-8 _*_
# @Time : 2025/12/30
# @Author : sonder
# @File : file.py
# @Comment : 文件管理API

from typing import Optional, List
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Path as PathParam,
    Request,
    Query,
    UploadFile,
    File,
)
from fastapi.responses import JSONResponse, FileResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from modules.file.model import get_file_type
from core.common import BaseResponse, DeleteListParams
from modules.file.service import FileService
from utils.response import ResponseUtil
from utils.storage import StorageFactory
from utils.log import logger

fileAPI = APIRouter(prefix="/file")
fileAccessAPI = APIRouter()


@fileAccessAPI.get(
    "/files/{path:path}", response_class=FileResponse, summary="访问本地文件"
)
async def get_local_file(request: Request, path: str):
    dynamic_config = request.app.state.dynamic_config
    base_path = await dynamic_config.get("upload_local_path", "uploads")
    file_path = Path(base_path) / path
    if not file_path.exists():
        return JSONResponse(
            status_code=404, content={"success": False, "msg": "文件不存在"}
        )
    return FileResponse(file_path)


authFileAPI = APIRouter(
    prefix="/file",
    dependencies=[Depends(AuthController.get_current_user)],
)


@authFileAPI.get(
    "/list",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取文件列表",
)
@Log(title="获取文件列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list"])
async def get_file_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    name: Optional[str] = Query(default=None, description="文件名"),
    file_type: Optional[str] = Query(default=None, description="文件类型"),
    folder: Optional[str] = Query(default=None, description="文件夹"),
    storage_type: Optional[str] = Query(default=None, description="存储类型"),
):
    filter_args = {}
    if name:
        filter_args["name__contains"] = name
    if file_type:
        filter_args["file_type"] = file_type
    if folder is not None:
        filter_args["folder"] = folder
    if storage_type:
        filter_args["storage_type"] = storage_type

    files, total = await FileService.get_file_list(page, pageSize, filter_args)
    return ResponseUtil.success(
        data={"total": total, "result": files, "page": page, "pageSize": pageSize}
    )


@authFileAPI.post(
    "/upload",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="上传文件",
)
@Log(title="上传文件", operation_type=OperationType.INSERT)
@Auth(permission_list=["file:btn:upload"])
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="上传的文件"),
    folder: str = Query(default="", description="文件夹路径"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    dynamic_config = request.app.state.dynamic_config

    valid, msg = await FileService.validate_upload(file, dynamic_config)
    if not valid:
        return ResponseUtil.error(msg=msg)

    try:
        storage = await StorageFactory.create(dynamic_config)
        storage_type = await dynamic_config.get("upload_storage_type", "local")
        result = await storage.upload(file, folder)

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        file_record = await FileService.create_file_record(
            {
                "name": file.filename,
                "key": result["key"],
                "url": result["url"],
                "size": result["size"],
                "file_type": get_file_type(file.filename),
                "mime_type": file.content_type,
                "extension": ext,
                "hash": result.get("hash"),
                "storage_type": storage_type,
                "folder": folder,
                "uploader_id": current_user.get("id"),
                "uploader_name": current_user.get("username"),
            }
        )

        return ResponseUtil.success(
            msg="上传成功",
            data={
                "id": file_record.id,
                "name": file_record.name,
                "url": file_record.url,
                "key": file_record.key,
                "size": file_record.size,
                "file_type": file_record.file_type,
            },
        )
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return ResponseUtil.error(msg=f"上传失败: {str(e)}")


@authFileAPI.post(
    "/upload/batch",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量上传文件",
)
@Log(title="批量上传文件", operation_type=OperationType.INSERT)
@Auth(permission_list=["file:btn:upload"])
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(..., description="上传的文件列表"),
    folder: str = Query(default="", description="文件夹路径"),
    current_user: dict = Depends(AuthController.get_current_user),
):
    dynamic_config = request.app.state.dynamic_config
    storage = await StorageFactory.create(dynamic_config)
    storage_type = await dynamic_config.get("upload_storage_type", "local")

    results = []
    errors = []

    for file in files:
        try:
            valid, msg = await FileService.validate_upload(file, dynamic_config)
            if not valid:
                errors.append({"name": file.filename, "error": msg})
                continue

            result = await storage.upload(file, folder)
            ext = (
                file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            )

            file_record = await FileService.create_file_record(
                {
                    "name": file.filename,
                    "key": result["key"],
                    "url": result["url"],
                    "size": result["size"],
                    "file_type": get_file_type(file.filename),
                    "mime_type": file.content_type,
                    "extension": ext,
                    "hash": result.get("hash"),
                    "storage_type": storage_type,
                    "folder": folder,
                    "uploader_id": current_user.get("id"),
                    "uploader_name": current_user.get("username"),
                }
            )

            results.append(
                {
                    "id": file_record.id,
                    "name": file_record.name,
                    "url": file_record.url,
                    "size": file_record.size,
                }
            )
        except Exception as e:
            errors.append({"name": file.filename, "error": str(e)})

    return ResponseUtil.success(
        msg=f"上传完成，成功{len(results)}个，失败{len(errors)}个",
        data={
            "success": results,
            "errors": errors,
        },
    )


@authFileAPI.delete(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除文件",
)
@authFileAPI.post(
    "/delete/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="删除文件",
)
@Log(title="删除文件", operation_type=OperationType.DELETE)
@Auth(permission_list=["file:btn:delete"])
async def delete_file(request: Request, id: str = PathParam(description="文件ID")):
    success, msg = await FileService.delete_file(id, request.app.state.dynamic_config)
    return ResponseUtil.success(msg=msg) if success else ResponseUtil.error(msg=msg)


@authFileAPI.delete(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除文件",
)
@authFileAPI.post(
    "/deleteList",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="批量删除文件",
)
@Log(title="批量删除文件", operation_type=OperationType.DELETE)
@Auth(permission_list=["file:btn:delete"])
async def delete_file_list(request: Request, params: DeleteListParams):
    count, msg = await FileService.batch_delete_files(
        params.ids, request.app.state.dynamic_config
    )
    return ResponseUtil.success(msg=msg)


@authFileAPI.get(
    "/info/{id}",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取文件信息",
)
@Log(title="获取文件信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:info"])
async def get_file_info(request: Request, id: str = PathParam(description="文件ID")):
    data = await FileService.get_file_info(id)
    if data:
        return ResponseUtil.success(data=data)
    return ResponseUtil.error(msg="文件不存在")


@authFileAPI.get(
    "/statistics",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取文件统计",
)
@Log(title="获取文件统计", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list"])
async def get_file_statistics(request: Request):
    data = await FileService.get_file_statistics()
    return ResponseUtil.success(data=data)


@authFileAPI.get(
    "/storage-config",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取存储配置",
)
@Log(title="获取存储配置", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list"])
async def get_storage_config(request: Request):
    data = await FileService.get_storage_config(request.app.state.dynamic_config)
    return ResponseUtil.success(data=data)
