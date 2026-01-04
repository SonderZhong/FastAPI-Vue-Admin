# _*_ coding : UTF-8 _*_
# @Time : 2025/10/22 00:00
# @UpdateTime : 2025/10/22 00:00
# @Author : sonder
# @File : file.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict
from pydantic_validation_decorator import Xss, NotBlank, Size

from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class FileInfo(DataBaseModel):
    """
    文件信息模型
    """

    model_config = ConfigDict()
    name: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    absolute_path: str = Field(..., description="绝对路径")
    relative_path: str = Field(..., description="相对路径")
    file_url: Optional[str] = Field(default=None, description="文件访问URL")
    uploader_id: Optional[str] = Field(default=None, description="上传人员ID")
    uploader_name: Optional[str] = Field(default=None, description="上传人员名称")
    file_category: str = Field(default="other", description="文件分类")


class GetFileInfoResponse(BaseResponse):
    """
    获取文件详情响应
    """

    data: FileInfo = Field(default=None, description="文件信息")


class UploadFileResponse(BaseResponse):
    """
    文件上传响应模型
    """

    data: dict = Field(default=None, description="文件信息")


class GetFileListResult(ListQueryResult):
    """
    获取文件列表结果模型
    """

    result: List[FileInfo] = Field(default=[], description="文件列表")


class GetFileListResponse(BaseResponse):
    """
    获取文件列表响应模型
    """

    data: GetFileListResult = Field(default=None, description="响应数据")


class UploadAvatarResponse(BaseResponse):
    """
    上传头像响应模型
    """

    data: dict = Field(default=None, description="头像信息，包含file_url等字段")

