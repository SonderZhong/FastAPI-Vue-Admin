# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 02:22
# @UpdateTime : 2025/08/25 02:22
# @Author : sonder
# @File : log.py
# @Software : PyCharm
# @Comment : 本程序
from pydantic import Field, ConfigDict

from schemas.common import BaseResponse, ListQueryResult, DataBaseModel


class LoginLogInfo(DataBaseModel):
    """
    登录日志信息
    """
    model_config = ConfigDict()
    user_id: str = Field(default="", description="用户ID")
    username: str = Field(default="", description="用户名")
    user_nickname: str = Field(default="", description="用户昵称")
    department_id: str = Field(default="", description="部门ID")
    department_name: str = Field(default="", description="部门名称")
    login_ip: str = Field(default="", description="登录IP")
    login_location: str = Field(default="", description="登录地点")
    browser: str = Field(default="", description="登录浏览器")
    os: str = Field(default="", description="登录操作系统")
    status: int = Field(default="", description="登录状态")
    login_time: str = Field(default="", description="登录时间")
    session_id: str = Field(default="", description="会话ID")
    online: bool = Field(default=False, description="是否在线")
    create_time: str = Field(default="", description="创建时间")
    update_time: str = Field(default="", description="更新时间")


class LoginLogResult(ListQueryResult):
    """
    登录日志查询结果
    """
    result: list[LoginLogInfo] = Field(default=[], description="登录日志列表")


class GetLoginLogResponse(BaseResponse):
    """
    获取登录日志响应
    """
    data: LoginLogResult = Field(default=[], description="登录日志查询结果")


class OperationLogInfo(DataBaseModel):
    """
    操作日志信息
    """
    model_config = ConfigDict()
    operation_name: str = Field(default="", description="操作名称")
    operation_type: int = Field(default=1, description="操作类型")
    request_path: str = Field(default="", description="请求路径")
    request_method: str = Field(default="", description="请求方法")
    request_params: str = Field(default="", description="请求参数")
    request_result: str = Field(default="", description="请求结果")
    host: str = Field(default="", description="请求主机")
    location: str = Field(default="", description="请求地址")
    browser: str = Field(default="", description="请求浏览器")
    os: str = Field(default="", description="请求操作系统")
    user_agent: str = Field(default="", description="请求头")
    operator_id: str = Field(default="", description="操作人员ID")
    operator_name: str = Field(default="", description="操作人员名称")
    operator_nickname: str = Field(default="", description="操作人员昵称")
    department_id: str = Field(default="", description="操作人员部门ID")
    department_name: str = Field(default="", description="操作人员部门名称")
    cost_time: float = Field(default=0.0, description="操作耗时")
    status: int = Field(default="", description="操作状态")


class OperationLogResult(ListQueryResult):
    """
    操作日志查询结果
    """
    result: list[OperationLogInfo] = Field(default=[], description="操作日志列表")


class GetOperationLogResponse(BaseResponse):
    """
    获取操作日志响应
    """
    data: OperationLogResult = Field(default=[], description="操作日志查询结果")
