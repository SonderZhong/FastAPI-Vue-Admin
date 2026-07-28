# _*_ coding : UTF-8 _*_

from typing import Any, Dict, List, Optional, Tuple

from core.common import BaseService
from modules.file.model import SystemFile
from utils.log import logger


class FileService(BaseService):
    model = SystemFile

    @classmethod
    async def get_file_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
    ):
        filter_args = {"is_del": False}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args).count()
        files = (
            await cls.model.filter(**filter_args)
            .order_by("-created_at")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                "id",
                "name",
                "key",
                "url",
                "size",
                "file_type",
                "mime_type",
                "extension",
                "hash",
                "storage_type",
                "folder",
                "uploader_id",
                "uploader_name",
                "remark",
                "created_at",
                "updated_at",
            )
        )
        return files, total

    @classmethod
    async def create_file_record(cls, file_data: dict) -> SystemFile:
        return await cls.model.create(**file_data)

    @classmethod
    async def delete_file(cls, file_id: str, dynamic_config) -> Tuple[bool, str]:
        file_record = await cls.model.get_or_none(id=file_id, is_del=False)
        if not file_record:
            return False, "文件不存在"

        try:
            from utils.storage import StorageFactory

            storage = await StorageFactory.create(dynamic_config)
            await storage.delete(file_record.key)
            file_record.is_del = True
            await file_record.save()
            return True, "删除成功"
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False, f"删除失败: {str(e)}"

    @classmethod
    async def batch_delete_files(
        cls, ids: List[str], dynamic_config
    ) -> Tuple[int, str]:
        from utils.storage import StorageFactory

        storage = await StorageFactory.create(dynamic_config)

        files = await cls.model.filter(id__in=list(set(ids)), is_del=False)
        for file_record in files:
            try:
                await storage.delete(file_record.key)
            except Exception as e:
                logger.warning(f"删除存储文件失败: {e}")

        await cls.model.filter(id__in=list(set(ids)), is_del=False).update(is_del=True)
        return len(files), "删除成功"

    @classmethod
    async def get_file_info(cls, file_id: str) -> Optional[dict]:
        file_record = await cls.model.get_or_none(id=file_id, is_del=False)
        if not file_record:
            return None
        return {
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
            "updated_at": file_record.updated_at,
        }

    @classmethod
    async def get_file_statistics(cls):
        from tortoise.functions import Count, Sum

        total_count = await cls.model.filter(is_del=False).count()
        total_size_result = (
            await cls.model.filter(is_del=False)
            .annotate(total=Sum("size"))
            .values("total")
        )
        total_size = total_size_result[0]["total"] or 0 if total_size_result else 0

        type_stats = (
            await cls.model.filter(is_del=False)
            .annotate(count=Count("id"))
            .group_by("file_type")
            .values("file_type", "count")
        )

        storage_stats = (
            await cls.model.filter(is_del=False)
            .annotate(count=Count("id"))
            .group_by("storage_type")
            .values("storage_type", "count")
        )

        return {
            "total_count": total_count,
            "total_size": total_size,
            "type_stats": type_stats,
            "storage_stats": storage_stats,
        }

    @staticmethod
    async def get_storage_config(dynamic_config) -> dict:
        storage_type = await dynamic_config.get("upload_storage_type", "local")
        max_size = await dynamic_config.get_int("upload_max_size", 100)
        allowed_extensions = await dynamic_config.get_list("upload_allowed_extensions")
        return {
            "storage_type": storage_type,
            "max_size": max_size,
            "allowed_extensions": allowed_extensions,
        }

    @staticmethod
    async def validate_upload(file, dynamic_config) -> Tuple[bool, str]:
        max_size = await dynamic_config.get_int("upload_max_size", 100)
        content = await file.read()
        await file.seek(0)

        if len(content) > max_size * 1024 * 1024:
            return False, f"文件大小超过限制（最大{max_size}MB）"

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        allowed_extensions = await dynamic_config.get_list("upload_allowed_extensions")
        if allowed_extensions and ext not in allowed_extensions:
            return False, f"不支持的文件类型: {ext}"

        return True, ""
