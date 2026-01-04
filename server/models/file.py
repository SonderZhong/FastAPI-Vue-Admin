# _*_ coding : UTF-8 _*_
# @Time : 2025/12/30
# @Author : sonder
# @File : file.py
# @Comment : 文件管理模型

from tortoise import fields
from models.common import BaseModel


class FileType:
    """文件类型常量"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    OTHER = "other"


# 文件扩展名与类型映射
FILE_TYPE_MAP = {
    # 图片
    "jpg": FileType.IMAGE, "jpeg": FileType.IMAGE, "png": FileType.IMAGE,
    "gif": FileType.IMAGE, "bmp": FileType.IMAGE, "webp": FileType.IMAGE,
    "svg": FileType.IMAGE, "ico": FileType.IMAGE,
    # 文档
    "doc": FileType.DOCUMENT, "docx": FileType.DOCUMENT,
    "xls": FileType.DOCUMENT, "xlsx": FileType.DOCUMENT,
    "ppt": FileType.DOCUMENT, "pptx": FileType.DOCUMENT,
    "pdf": FileType.DOCUMENT, "txt": FileType.DOCUMENT,
    "md": FileType.DOCUMENT, "csv": FileType.DOCUMENT,
    # 视频
    "mp4": FileType.VIDEO, "avi": FileType.VIDEO, "mov": FileType.VIDEO,
    "wmv": FileType.VIDEO, "flv": FileType.VIDEO, "mkv": FileType.VIDEO,
    # 音频
    "mp3": FileType.AUDIO, "wav": FileType.AUDIO, "flac": FileType.AUDIO,
    "aac": FileType.AUDIO, "ogg": FileType.AUDIO,
    # 压缩包
    "zip": FileType.ARCHIVE, "rar": FileType.ARCHIVE, "7z": FileType.ARCHIVE,
    "tar": FileType.ARCHIVE, "gz": FileType.ARCHIVE,
}


def get_file_type(filename: str) -> str:
    """根据文件名获取文件类型"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return FILE_TYPE_MAP.get(ext, FileType.OTHER)


class SystemFile(BaseModel):
    """
    系统文件模型
    """
    name = fields.CharField(
        max_length=255,
        description="原始文件名",
        source_field="name"
    )
    key = fields.CharField(
        max_length=500,
        description="存储key",
        source_field="storage_key"
    )
    url = fields.CharField(
        max_length=1000,
        description="访问URL",
        source_field="url"
    )
    size = fields.BigIntField(
        default=0,
        description="文件大小(字节)",
        source_field="size"
    )
    file_type = fields.CharField(
        max_length=20,
        default=FileType.OTHER,
        description="文件类型",
        source_field="file_type"
    )
    mime_type = fields.CharField(
        max_length=100,
        null=True,
        description="MIME类型",
        source_field="mime_type"
    )
    extension = fields.CharField(
        max_length=20,
        null=True,
        description="文件扩展名",
        source_field="extension"
    )
    hash = fields.CharField(
        max_length=64,
        null=True,
        description="文件MD5",
        source_field="hash"
    )
    storage_type = fields.CharField(
        max_length=20,
        default="local",
        description="存储类型",
        source_field="storage_type"
    )
    folder = fields.CharField(
        max_length=255,
        default="",
        description="所属文件夹",
        source_field="folder"
    )
    uploader_id = fields.CharField(
        max_length=36,
        null=True,
        description="上传者ID",
        source_field="uploader_id"
    )
    uploader_name = fields.CharField(
        max_length=50,
        null=True,
        description="上传者名称",
        source_field="uploader_name"
    )
    remark = fields.TextField(
        null=True,
        description="备注",
        source_field="remark"
    )

    class Meta:
        table = "system_file"
        table_description = "系统文件表"
