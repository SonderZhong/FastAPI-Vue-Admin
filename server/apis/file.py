# _*_ coding : UTF-8 _*_
# @Time : 2025/12/30
# @Author : sonder
# @File : file.py
# @Comment : 文件管理API

from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, Path as PathParam, Request, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from models.file import SystemFile, get_file_type
from schemas.common import BaseResponse, DeleteListParams
from utils.response import ResponseUtil
from utils.storage import StorageFactory
from utils.log import logger

fileAPI = APIRouter(prefix="/file")

# 文件访问路由（无前缀，用于静态文件访问）
fileAccessAPI = APIRouter()


# ==================== 公开接口（文件访问） ====================

@fileAccessAPI.get("/files/{path:path}", response_class=FileResponse, summary="访问本地文件")
async def get_local_file(request: Request, path: str):
    """访问本地存储的文件"""
    dynamic_config = request.app.state.dynamic_config
    base_path = await dynamic_config.get("upload_local_path", "uploads")
    file_path = Path(base_path) / path
    
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"success": False, "msg": "文件不存在"})
    
    return FileResponse(file_path)


# ==================== 需要认证的接口 ====================

authFileAPI = APIRouter(
    prefix="/file",
    dependencies=[Depends(AuthController.get_current_user)],
)


class FileSearchParams(BaseModel):
    """文件搜索参数"""
    page: int = 1
    pageSize: int = 20
    name: Optional[str] = None
    file_type: Optional[str] = None
    folder: Optional[str] = None
    storage_type: Optional[str] = None


@authFileAPI.get("/list", response_class=JSONResponse, response_model=BaseResponse, summary="获取文件列表")
@Log(title="获取文件列表", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list", "GET:/file/list"])
async def get_file_list(
    request: Request,
    page: int = Query(default=1, description="当前页码"),
    pageSize: int = Query(default=20, description="每页数量"),
    name: Optional[str] = Query(default=None, description="文件名"),
    file_type: Optional[str] = Query(default=None, description="文件类型"),
    folder: Optional[str] = Query(default=None, description="文件夹"),
    storage_type: Optional[str] = Query(default=None, description="存储类型"),
):
    """获取文件列表"""
    filter_args = {"is_del": False}
    
    if name:
        filter_args["name__contains"] = name
    if file_type:
        filter_args["file_type"] = file_type
    if folder is not None:
        filter_args["folder"] = folder
    if storage_type:
        filter_args["storage_type"] = storage_type
    
    total = await SystemFile.filter(**filter_args).count()
    files = await SystemFile.filter(**filter_args).order_by("-created_at").offset(
        (page - 1) * pageSize
    ).limit(pageSize).values(
        "id", "name", "key", "url", "size", "file_type", "mime_type",
        "extension", "hash", "storage_type", "folder", "uploader_id",
        "uploader_name", "remark", "created_at", "updated_at"
    )
    
    return ResponseUtil.success(data={
        "total": total,
        "result": files,
        "page": page,
        "pageSize": pageSize
    })


@authFileAPI.post("/upload", response_class=JSONResponse, response_model=BaseResponse, summary="上传文件")
@Log(title="上传文件", operation_type=OperationType.INSERT)
@Auth(permission_list=["file:btn:upload", "POST:/file/upload"])
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="上传的文件"),
    folder: str = Query(default="", description="文件夹路径"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """上传文件"""
    dynamic_config = request.app.state.dynamic_config
    
    # 检查文件大小
    max_size = await dynamic_config.get_int("upload_max_size", 100)
    content = await file.read()
    await file.seek(0)  # 重置文件指针
    
    if len(content) > max_size * 1024 * 1024:
        return ResponseUtil.error(msg=f"文件大小超过限制（最大{max_size}MB）")
    
    # 检查文件扩展名
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_extensions = await dynamic_config.get_list("upload_allowed_extensions")
    if allowed_extensions and ext not in allowed_extensions:
        return ResponseUtil.error(msg=f"不支持的文件类型: {ext}")
    
    try:
        # 获取存储服务
        storage = await StorageFactory.create(dynamic_config)
        storage_type = await dynamic_config.get("upload_storage_type", "local")
        
        # 上传文件
        result = await storage.upload(file, folder)
        
        # 保存文件记录
        file_record = await SystemFile.create(
            name=file.filename,
            key=result["key"],
            url=result["url"],
            size=result["size"],
            file_type=get_file_type(file.filename),
            mime_type=file.content_type,
            extension=ext,
            hash=result.get("hash"),
            storage_type=storage_type,
            folder=folder,
            uploader_id=current_user.get("id"),
            uploader_name=current_user.get("username")
        )
        
        return ResponseUtil.success(msg="上传成功", data={
            "id": file_record.id,
            "name": file_record.name,
            "url": file_record.url,
            "key": file_record.key,
            "size": file_record.size,
            "file_type": file_record.file_type
        })
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return ResponseUtil.error(msg=f"上传失败: {str(e)}")


@authFileAPI.post("/upload/batch", response_class=JSONResponse, response_model=BaseResponse, summary="批量上传文件")
@Log(title="批量上传文件", operation_type=OperationType.INSERT)
@Auth(permission_list=["file:btn:upload", "POST:/file/upload/batch"])
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(..., description="上传的文件列表"),
    folder: str = Query(default="", description="文件夹路径"),
    current_user: dict = Depends(AuthController.get_current_user)
):
    """批量上传文件"""
    dynamic_config = request.app.state.dynamic_config
    storage = await StorageFactory.create(dynamic_config)
    storage_type = await dynamic_config.get("upload_storage_type", "local")
    max_size = await dynamic_config.get_int("upload_max_size", 100)
    allowed_extensions = await dynamic_config.get_list("upload_allowed_extensions")
    
    results = []
    errors = []
    
    for file in files:
        try:
            # 检查文件大小
            content = await file.read()
            await file.seek(0)
            
            if len(content) > max_size * 1024 * 1024:
                errors.append({"name": file.filename, "error": f"文件大小超过限制（最大{max_size}MB）"})
                continue
            
            # 检查扩展名
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if allowed_extensions and ext not in allowed_extensions:
                errors.append({"name": file.filename, "error": f"不支持的文件类型: {ext}"})
                continue
            
            # 上传
            result = await storage.upload(file, folder)
            
            # 保存记录
            file_record = await SystemFile.create(
                name=file.filename,
                key=result["key"],
                url=result["url"],
                size=result["size"],
                file_type=get_file_type(file.filename),
                mime_type=file.content_type,
                extension=ext,
                hash=result.get("hash"),
                storage_type=storage_type,
                folder=folder,
                uploader_id=current_user.get("id"),
                uploader_name=current_user.get("username")
            )
            
            results.append({
                "id": file_record.id,
                "name": file_record.name,
                "url": file_record.url,
                "size": file_record.size
            })
        except Exception as e:
            errors.append({"name": file.filename, "error": str(e)})
    
    return ResponseUtil.success(msg=f"上传完成，成功{len(results)}个，失败{len(errors)}个", data={
        "success": results,
        "errors": errors
    })


@authFileAPI.delete("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除文件")
@authFileAPI.post("/delete/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="删除文件")
@Log(title="删除文件", operation_type=OperationType.DELETE)
@Auth(permission_list=["file:btn:delete", "DELETE,POST:/file/delete/*"])
async def delete_file(request: Request, id: str = PathParam(description="文件ID")):
    """删除文件"""
    file_record = await SystemFile.get_or_none(id=id, is_del=False)
    if not file_record:
        return ResponseUtil.error(msg="文件不存在")
    
    try:
        dynamic_config = request.app.state.dynamic_config
        storage = await StorageFactory.create(dynamic_config)
        
        # 删除存储中的文件
        await storage.delete(file_record.key)
        
        # 软删除记录
        file_record.is_del = True
        await file_record.save()
        
        return ResponseUtil.success(msg="删除成功")
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return ResponseUtil.error(msg=f"删除失败: {str(e)}")


@authFileAPI.delete("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除文件")
@authFileAPI.post("/deleteList", response_class=JSONResponse, response_model=BaseResponse, summary="批量删除文件")
@Log(title="批量删除文件", operation_type=OperationType.DELETE)
@Auth(permission_list=["file:btn:delete", "DELETE,POST:/file/deleteList"])
async def delete_file_list(request: Request, params: DeleteListParams):
    """批量删除文件"""
    dynamic_config = request.app.state.dynamic_config
    storage = await StorageFactory.create(dynamic_config)
    
    files = await SystemFile.filter(id__in=list(set(params.ids)), is_del=False)
    
    for file_record in files:
        try:
            await storage.delete(file_record.key)
        except Exception as e:
            logger.warning(f"删除存储文件失败: {e}")
    
    await SystemFile.filter(id__in=list(set(params.ids)), is_del=False).update(is_del=True)
    
    return ResponseUtil.success(msg="删除成功")


@authFileAPI.get("/info/{id}", response_class=JSONResponse, response_model=BaseResponse, summary="获取文件信息")
@Log(title="获取文件信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:info", "GET:/file/info/*"])
async def get_file_info(request: Request, id: str = PathParam(description="文件ID")):
    """获取文件详情"""
    file_record = await SystemFile.get_or_none(id=id, is_del=False)
    if not file_record:
        return ResponseUtil.error(msg="文件不存在")
    
    return ResponseUtil.success(data={
        "id": file_record.id,
        "name": file_record.name,
        "key": file_record.key,
        "url": file_record.url,
        "size": file_record.size,
        "file_type": file_record.file_type,
        "mime_type": file_record.mime_type,
        "extension": file_record.extension,
        "hash": file_record.hash,
        "storage_type": file_record.storage_type,
        "folder": file_record.folder,
        "uploader_id": file_record.uploader_id,
        "uploader_name": file_record.uploader_name,
        "remark": file_record.remark,
        "created_at": file_record.created_at,
        "updated_at": file_record.updated_at
    })


@authFileAPI.get("/statistics", response_class=JSONResponse, response_model=BaseResponse, summary="获取文件统计")
@Log(title="获取文件统计", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list", "GET:/file/statistics"])
async def get_file_statistics(request: Request):
    """获取文件统计信息"""
    from tortoise.functions import Count, Sum
    
    # 总文件数和总大小
    total_count = await SystemFile.filter(is_del=False).count()
    total_size_result = await SystemFile.filter(is_del=False).annotate(
        total=Sum("size")
    ).values("total")
    total_size = total_size_result[0]["total"] or 0 if total_size_result else 0
    
    # 按类型统计
    type_stats = await SystemFile.filter(is_del=False).annotate(
        count=Count("id")
    ).group_by("file_type").values("file_type", "count")
    
    # 按存储类型统计
    storage_stats = await SystemFile.filter(is_del=False).annotate(
        count=Count("id")
    ).group_by("storage_type").values("storage_type", "count")
    
    return ResponseUtil.success(data={
        "total_count": total_count,
        "total_size": total_size,
        "type_stats": type_stats,
        "storage_stats": storage_stats
    })


@authFileAPI.get("/storage-config", response_class=JSONResponse, response_model=BaseResponse, summary="获取存储配置")
@Log(title="获取存储配置", operation_type=OperationType.SELECT)
@Auth(permission_list=["file:btn:list", "GET:/file/storage-config"])
async def get_storage_config(request: Request):
    """获取当前存储配置"""
    dynamic_config = request.app.state.dynamic_config
    
    storage_type = await dynamic_config.get("upload_storage_type", "local")
    max_size = await dynamic_config.get_int("upload_max_size", 100)
    allowed_extensions = await dynamic_config.get_list("upload_allowed_extensions")
    
    return ResponseUtil.success(data={
        "storage_type": storage_type,
        "max_size": max_size,
        "allowed_extensions": allowed_extensions
    })
