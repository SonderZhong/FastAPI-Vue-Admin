# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:54
# @UpdateTime : 2025/08/04 01:54
# @Author : sonder
# @File : auth.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_snake
from pydantic_validation_decorator import Network, Size

from schemas.common import BaseResponse


class GetCaptchaResult(BaseModel):
    """
    获取验证码结果模型
    """
    model_config = ConfigDict(alias_generator=to_snake)
    uuid: Optional[str] = Field(default=None, description="验证码UUID")
    captcha: Optional[str] = Field(default=None, description="验证码图片")
    captcha_enabled: Optional[bool] = Field(default=False, description="是否开启验证码")


class GetCaptchaResponse(BaseResponse):
    """
    获取验证码响应模型
    """
    data: GetCaptchaResult = Field(default=None, description="响应数据")


class LoginParams(BaseModel):
    """
    登录请求模型
    """
    model_config = ConfigDict(alias_generator=to_snake)
    username: str = Field(default="", description="用户名")
    password: str = Field(default="", description="密码")
    loginDays: Optional[int] = Field(default=1, description="登录天数")
    code: Optional[str] = Field(default="", description="验证码")
    uuid: Optional[str] = Field(default="", description="验证码UUID")


class LoginResult(BaseModel):
    """
    登录结果模型
    """
    model_config = ConfigDict(alias_generator=to_snake)
    accessToken: str = Field(default="", description="访问令牌")
    refreshToken: str = Field(default="", description="刷新令牌")
    expiresTime: int = Field(default=0, description="令牌过期时间戳")


class LoginResponse(BaseResponse):
    """
    登录响应模型
    """
    data: LoginResult = Field(default=None, description="响应数据")


class GetEmailCodeParams(BaseModel):
    """
    获取邮箱验证码请求模型
    """
    model_config = ConfigDict()
    username: str = Field(default="", description="用户名")
    title: str = Field(default="注册", description="邮件类型")
    mail: str = Field(default="", description="邮箱地址")

    @Network(field_name='mail', field_type='EmailStr', message='邮箱格式不正确')
    @Size(field_name='mail', min_length=0, max_length=50, message='邮箱长度不能超过50个字符')
    def get_email(self):
        return self.mail

