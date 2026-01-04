# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:42
# @UpdateTime : 2025/12/26
# @Author : sonder
# @File : auth.py
# @Software : PyCharm
# @Comment : 认证与权限控制
from datetime import timedelta, datetime
from functools import wraps
from typing import Union, Optional
import json

from fastapi import Form, HTTPException, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, ExpiredSignatureError
from jose.exceptions import JWEInvalidAuth, JWEError

from exceptions.exception import AuthException, PermissionException
from models import (
    SystemUser,
)
from utils.casbin import CasbinEnforcer, DataScope
from utils.config import config
from utils.get_redis import RedisKeyConfig
from utils.log import logger
from utils.response import HttpStatusConstant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    """
    自定义 OAuth2 密码模式请求表单
    扩展支持验证码、会话标识和登录有效期参数
    """

    def __init__(
        self,
        grant_type: str = Form(
            default="password",
            regex="password",
            description="授权类型，固定为 'password'",
        ),
        username: str = Form(
            ..., min_length=3, max_length=50, description="用户账号（3-50个字符）"
        ),
        password: str = Form(..., min_length=6, description="用户密码（至少6个字符）"),
        scope: str = Form(default="", description="权限范围，多个用空格分隔"),
        client_id: Optional[str] = Form(default=None, description="客户端ID（可选）"),
        client_secret: Optional[str] = Form(
            default=None, description="客户端密钥（可选）"
        ),
        login_days: Optional[int] = Form(
            default=1,
            ge=1,  # 最小1天
            le=30,  # 最大30天
            description="登录有效期（1-30天）",
        ),
        code: Optional[str] = Form(
            default=None, min_length=1, max_length=10, description="验证码（1-10个字符，支持算术题和字母数字）"
        ),
        uuid: Optional[str] = Form(
            default=None,
            min_length=16,
            max_length=36,
            description="验证码会话UUID（16-36个字符）",
        ),
    ):
        # 调用父类初始化（处理标准参数）
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )

        # 验证 grant_type 必须为 password（增强安全性）
        if grant_type != "password":
            raise HTTPException(
                status_code=HttpStatusConstant.BAD_REQUEST,
                detail="仅支持 'password' 授权类型",
            )

        # 绑定扩展参数
        self.login_days = login_days  # 统一使用小写蛇形命名（符合PEP8）
        self.code = code
        self.uuid = uuid


class Auth:
    """
    权限装饰器
    支持两种权限格式：
    1. 按钮权限：如 "permission:btn:add"
    2. API权限：如 "POST:/user/add" 或 "GET,POST:/user/*"
    
    权限校验逻辑：有其中一个权限就放行
    """

    def __init__(self, permission_list: list):
        """
        权限装饰器
        :param permission_list: 权限列表，支持按钮权限和API权限混合
        """
        self.permission_list = permission_list

    def __call__(self, func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 获取上下文信息
            token = request.headers.get("Authorization")
            current_user = await AuthController.get_current_user(request, token)
            
            # 获取用户的按钮权限标识
            permission_marks = set(current_user.get("permission_marks", []))
            # 获取用户的API权限列表 (格式: ["GET:/user/*", "POST:/role/add"])
            user_apis = current_user.get("apis", [])
            
            # 遍历所需权限，有一个满足即可
            for required_perm in self.permission_list:
                # 检查是否是API权限格式 (method:path)
                if ":" in required_perm and "/" in required_perm:
                    # API权限格式: "GET:/user/add" 或 "GET,POST:/user/*"
                    if self._check_api_permission(required_perm, user_apis):
                        return await func(request, *args, **kwargs)
                else:
                    # 按钮权限格式: "permission:btn:add"
                    if required_perm in permission_marks:
                        return await func(request, *args, **kwargs)
            
            # 如果用户没有任何所需权限，返回错误信息
            raise PermissionException(message="该用户无此接口权限！")

        return wrapper
    
    def _check_api_permission(self, required_perm: str, user_apis: list) -> bool:
        """
        检查API权限
        :param required_perm: 所需权限，格式如 "GET:/user/add" 或 "GET,POST:/user/*"
        :param user_apis: 用户拥有的API权限列表
        :return: 是否有权限
        """
        
        # 解析所需权限
        parts = required_perm.split(":", 1)
        if len(parts) != 2:
            return False
        
        required_methods = [m.strip().upper() for m in parts[0].split(",")]
        required_path = parts[1]
        
        for user_api in user_apis:
            # 解析用户API权限
            api_parts = user_api.split(":", 1)
            if len(api_parts) != 2:
                continue
            
            user_methods = [m.strip().upper() for m in api_parts[0].split(",")]
            user_path = api_parts[1]
            
            # 检查方法是否匹配（有交集即可）
            if not set(required_methods) & set(user_methods):
                continue
            
            # 检查路径是否匹配（支持通配符 *）
            if self._match_path(required_path, user_path):
                return True
        
        return False
    
    def _match_path(self, required_path: str, user_path: str) -> bool:
        """
        路径匹配，支持通配符
        :param required_path: 所需路径
        :param user_path: 用户拥有的路径（可能包含通配符 *）
        :return: 是否匹配
        """
        import re
        
        # 精确匹配
        if required_path == user_path:
            return True
        
        # 通配符匹配：将 * 转换为正则表达式
        if "*" in user_path:
            # 转义特殊字符，将 * 替换为 .*
            pattern = re.escape(user_path).replace(r"\*", ".*")
            pattern = f"^{pattern}$"
            if re.match(pattern, required_path):
                return True
        
        return False


class DataPermission:
    """
    数据权限装饰器 - 基于 Casbin
    自动注入数据权限范围到请求中
    """
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization")
            current_user = await AuthController.get_current_user(request, token)
            user_id = current_user.get("id")
            
            # 获取数据权限范围
            data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
            
            # 注入到 request.state
            request.state.data_scope = data_scope
            request.state.accessible_dept_ids = data_scope["department_ids"]
            
            return await func(request, *args, **kwargs)
        
        return wrapper


async def hasAuth(request: Request, permission: str) -> bool:
    """
    判断是有拥有某项权限
    """
    token = request.headers.get("Authorization")  # 直接使用 request 对象
    current_user = await AuthController.get_current_user(request, token)
    permissions = current_user.get("permission_ids",[])
    if permission in permissions:
        return True
    else:
        return False


async def hasAdmin(request: Request, department_id: str) -> bool:
    """
    判断是否有管理员权限
    """
    permissions = []
    if ids := await request.app.state.redis.get(
        f"{RedisKeyConfig.SYSTEM_CONFIG.key}:permission_departments"
    ):
        permissions = eval(ids)
    if department_id in permissions:
        return True
    else:
        return False


def getUserTypePermissions(user_type: int) -> dict:
    """
    获取用户身份对应的权限范围
    :param user_type: 用户身份标识（0超级管理员，1管理员，2部门管理员，3普通用户）
    :return: 权限范围字典
    """
    permissions = {
        0: {  # 超级管理员
            "name": "超级管理员",
            "can_manage_all": True,
            "can_manage_system": True,
            "can_manage_departments": True,
            "can_manage_users": True,
            "can_assign_roles": True,
            "can_view_all_data": True,
            "description": "拥有系统最高权限，可管理所有资源和配置"
        },
        1: {  # 管理员
            "name": "管理员",
            "can_manage_all": False,
            "can_manage_system": True,
            "can_manage_departments": True,
            "can_manage_users": True,
            "can_assign_roles": True,
            "can_view_all_data": True,
            "description": "可管理系统配置、部门和用户，但无法修改超级管理员"
        },
        2: {  # 部门管理员
            "name": "部门管理员",
            "can_manage_all": False,
            "can_manage_system": False,
            "can_manage_departments": False,
            "can_manage_users": True,
            "can_assign_roles": False,
            "can_view_all_data": False,
            "description": "可管理所属部门及下属部门的用户和数据"
        },
        3: {  # 普通用户
            "name": "普通用户",
            "can_manage_all": False,
            "can_manage_system": False,
            "can_manage_departments": False,
            "can_manage_users": False,
            "can_assign_roles": False,
            "can_view_all_data": False,
            "description": "只能查看和操作自己的数据"
        }
    }
    return permissions.get(user_type, permissions[3])


async def canManageUser(current_user: dict, target_user_id: str) -> bool:
    """
    判断当前用户是否可以管理目标用户（使用 Casbin）
    :param current_user: 当前用户信息
    :param target_user_id: 目标用户ID
    :return: 是否有权限
    """
    current_user_id = current_user.get("id")
    if not current_user_id:
        return False
    
    # 使用 Casbin 检查数据权限
    return await CasbinEnforcer.can_access_user_data(
        operator_id=str(current_user_id),
        target_user_id=str(target_user_id)
    )


async def filterUsersByType(current_user: dict, query_filters: dict) -> dict:
    """
    根据用户身份过滤查询条件（使用 Casbin）
    :param current_user: 当前用户信息
    :param query_filters: 原始查询条件
    :return: 过滤后的查询条件
    """
    user_id = current_user.get("id")
    if not user_id:
        query_filters["id"] = None  # 无权限
        return query_filters
    
    # 获取数据权限范围
    scope = await CasbinEnforcer.get_data_scope(str(user_id))
    
    # 全部数据权限
    if scope["scope"] == DataScope.ALL:
        return query_filters
    
    # 仅本人数据
    if scope["scope"] == DataScope.SELF_ONLY:
        query_filters["id"] = user_id
        return query_filters
    
    # 部门及下属部门数据
    if scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
        if scope["department_ids"]:
            query_filters["department_id__in"] = list(scope["department_ids"])
        else:
            query_filters["id"] = None  # 无部门，无权限
        return query_filters
    
    # 默认只能查看自己
    query_filters["id"] = user_id
    return query_filters


class AuthController:
    """
    用户认证控制器
    """

    @classmethod
    async def create_token(
        cls, data: dict, expires_delta: Union[timedelta, None] = None
    ) -> str:
        """
        创建token
        :param data: 存储数据
        :param expires_delta: 过期时间
        :return: token
        """
        to_copy = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=config.jwt().expire_minutes)
        to_copy.update({"exp": expire})
        return jwt.encode(
            claims=to_copy,
            key=config.jwt().secret_key,
            algorithm=config.jwt().algorithm,
        )

    @classmethod
    async def get_current_user(
        cls, request: Request = Request, token: str = Depends(oauth2_scheme)
    ):
        """
        获取当前用户
        :param request:
        :param token:
        :return:
        """
        try:
            if token.startswith("Bearer"):
                token = token.split(" ")[1]
            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )
            user_id: str = payload.get("id", "")
            session_id: str = payload.get("session_id", "")
            if not user_id:
                logger.warning("用户token不合法")
                raise AuthException(data="", message="用户token不合法")
            if not await SystemUser.get_or_none(id=user_id):
                logger.warning("用户不存在")
                raise AuthException(data="", message="用户不存在")
        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            logger.warning("用户token已失效，请重新登录")
            raise AuthException(data="", message="用户token已失效，请重新登录")
        userInfo = await request.app.state.redis.get(
            f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
        )
        if userInfo:
            try:
                userInfo = json.loads(userInfo)
            except (json.JSONDecodeError, ValueError):
                # 如果JSON解析失败，清除缓存并重新获取
                await request.app.state.redis.delete(
                    f"{RedisKeyConfig.USER_INFO.key}:{user_id}"
                )
                userInfo = None

        if not userInfo:
            # 重新获取用户信息（包括最新的下属部门和权限）
            userInfo = await cls.get_user_info(user_id=user_id)
            # 缓存用户信息，时间设置为30分钟
            await request.app.state.redis.set(
                f"{RedisKeyConfig.USER_INFO.key}:{user_id}",
                json.dumps(jsonable_encoder(userInfo), ensure_ascii=False, default=str),
                ex=timedelta(minutes=30),
            )
        if not userInfo:
            logger.warning("用户token不合法")
            raise AuthException(data="", message="用户token不合法")
        redis_token = await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
        )
        if not redis_token:
            logger.warning("用户token已失效，请重新登录")
            raise AuthException(data="", message="用户token已失效，请重新登录")
        return userInfo

    @classmethod
    async def get_user_info(cls, user_id: str) -> dict:
        """
        获取用户信息（使用 Casbin 获取权限）
        :param user_id:
        :return:
        """
        user_info = await SystemUser.get_or_none(id=user_id, is_del=False).values(
            id="id",
            username="username",
            nickname="nickname",
            avatar="avatar",
            gender="gender",
            phone="phone",
            email="email",
            status="status",
            user_type="user_type",
            department_id="department__id",
            department_name="department__name",
            created_at="created_at",
            updated_at="updated_at",
        )
        
        if not user_info:
            return None
        
        # 使用 Casbin 获取用户的所有权限
        user_permissions = await CasbinEnforcer.get_user_permissions(str(user_id))
        
        # 获取数据权限范围
        data_scope = await CasbinEnforcer.get_data_scope(str(user_id))
        subDepartments = list(data_scope["department_ids"])
        
        # 获取按钮权限的 authMark
        from models import SystemPermission
        button_ids = user_permissions["buttons"]
        permission_marks = []
        
        if button_ids:
            permissions = await SystemPermission.filter(
                id__in=button_ids,
                is_del=False
            ).values("id", "authMark")
            permission_marks = [p["authMark"] for p in permissions if p["authMark"]]
        
        return {
            **user_info,
            **{
                "sub_departments": subDepartments,
                "permission_ids": button_ids,
                "permission_marks": permission_marks,
                "data_scope": data_scope["scope"],
                "casbin_roles": user_permissions["roles"],
                "menus": user_permissions["menus"],
                "buttons": user_permissions["buttons"],
                "apis": user_permissions["apis"],
            },
        }

    @classmethod
    async def logout(
        cls, request: Request = Request, token: str = Depends(oauth2_scheme)
    ) -> bool:
        """
        登出
        """
        try:
            if token.startswith("Bearer"):
                token = token.split(" ")[1]
            payload = jwt.decode(
                token=token,
                key=config.jwt().secret_key,
                algorithms=[config.jwt().algorithm],
            )
            session_id: str = payload.get("session_id", "")
        except (JWEInvalidAuth, ExpiredSignatureError, JWEError):
            logger.warning("用户token已失效，请重新登录")
            raise AuthException(data="", message="用户token已失效，请重新登录")
        redis_token = await request.app.state.redis.get(
            f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
        )
        if redis_token == token:
            await request.app.state.redis.delete(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"
            )
            return True
        return False
