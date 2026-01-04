# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:52
# @UpdateTime : 2025/08/04 01:52
# @Author : sonder
# @File : auth.py
# @Software : PyCharm
# @Comment : 本程序
import json
import uuid
from datetime import timedelta, datetime
from typing import Optional

from fastapi import APIRouter, Request, Depends
from starlette.responses import JSONResponse
from tortoise.expressions import Q

from annotation.auth import CustomOAuth2PasswordRequestForm, AuthController
from annotation.log import Log, OperationType
from models import (
    SystemUser,
    SystemDepartment,
    SystemUserRole,
    SystemLoginLog,
    SystemPermission,
)
from schemas.common import BaseResponse
from schemas.auth import (
    GetCaptchaResponse,
    LoginResponse,
    LoginParams,
    GetEmailCodeParams,
)
from schemas.user import RegisterUserParams, GetUserInfoResponse
from utils.captcha import CaptchaUtil
from utils.get_redis import RedisKeyConfig
from utils.log import logger
from utils.mail import Email
from utils.password import PasswordUtil
from utils.response import ResponseUtil
from annotation.log import _request_meta
from utils.geoip import get_ip_location_info
from utils.config import config
from utils.notification import NotificationService

authAPI = APIRouter(prefix="/auth")


def get_login_meta(request: Request) -> dict:
    """获取登录请求的元数据，包括地理位置"""
    meta = _request_meta(request)
    # 添加地理位置信息
    meta["location"] = (
        get_ip_location_info(meta["ip"])
        if config.app().ip_location_enabled
        else "内网IP"
    )
    return meta


@authAPI.get(
    "/captcha",
    response_class=JSONResponse,
    response_model=GetCaptchaResponse,
    summary="获取验证码",
)
async def get_captcha(request: Request):
    captcha_enabled = (
        True
        if await request.app.state.redis.get(
            f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_enabled"
        )
        == "true"
        else False
    )
    register_enabled = (
        True
        if await request.app.state.redis.get(
            f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_register_enabled"
        )
        == "true"
        else False
    )
    if captcha_enabled:
        captcha_type = (
            await request.app.state.redis.get(
                f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_type"
            )
            if await request.app.state.redis.get(
                f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_type"
            )
            else "0"  # 默认使用算术题验证码
        )
        captcha_result = await CaptchaUtil.create_captcha(captcha_type)
        session_id = str(uuid.uuid4())
        captcha = captcha_result[0]
        result = captcha_result[-1]
        await request.app.state.redis.set(
            f"{RedisKeyConfig.CAPTCHA_CODES.key}:{session_id}",
            result,
            ex=timedelta(minutes=2),
        )
        logger.info(f"编号为{session_id}的会话获取图片验证码成功")

        return ResponseUtil.success(
            data={
                "uuid": session_id,
                "captcha": captcha,
                "captcha_enabled": captcha_enabled,
                "register_enabled": register_enabled,
                "captcha_type": captcha_type,  # 返回验证码类型：0=算术题，1=字母数字
            }
        )
    else:
        return ResponseUtil.success(
            data={
                "uuid": None,
                "captcha": None,
                "captcha_enabled": captcha_enabled,
                "register_enabled": register_enabled,
                "captcha_type": "0",  # 即使未启用也返回默认类型
            }
        )


@authAPI.post("/login", response_class=JSONResponse, summary="登录")
@Log(operation_type=OperationType.GRANT, title="登录", log_type="login")
async def login(request: Request, params: CustomOAuth2PasswordRequestForm = Depends()):
    user = LoginParams(
        username=params.username,
        password=params.password,
        loginDays=params.login_days,
        code=params.code,
        uuid=params.uuid,
    )
    captcha_enabled = (
        True
        if await request.app.state.redis.get(
            f"{RedisKeyConfig.SYSTEM_CONFIG.key}:account_captcha_enabled"
        )
        == "true"
        else False
    )
    # 判断请求是否来自于api文档，如果是返回指定格式的结果，用于修复api文档认证成功后token显示undefined的bug
    request_from_swagger = (
        request.headers.get("referer").endswith("docs")
        if request.headers.get("referer")
        else False
    )
    request_from_redoc = (
        request.headers.get("referer").endswith("redoc")
        if request.headers.get("referer")
        else False
    )

    # 验证码校验，如果开启验证码校验，则进行验证码校验，如果关闭则跳过验证码校验. 如果请求来自api文档，则跳过验证码校验
    if captcha_enabled and not request_from_redoc and not request_from_swagger:
        result = await CaptchaUtil.verify_code(
            request, code=user.code, session_id=user.uuid
        )
        if not result["status"]:
            return ResponseUtil.error(msg=result["msg"])
    if user := await SystemUser.get_or_none(
        Q(username=params.username)
        | Q(email=params.username)
        | Q(phone=params.username),
        is_del=False,
    ):
        if await PasswordUtil.verify_password(
            plain_password=params.password, hashed_password=user.password
        ):
            userInfo = await AuthController.get_user_info(user.id)
            logger.info(f"用户{user.username}登录成功")
            session_id = uuid.uuid4().__str__()
            
            # 记录登录日志
            request_meta = get_login_meta(request)
            await SystemLoginLog.create(
                user_id=user,
                login_ip=request_meta["ip"],
                login_location=request_meta["location"],
                browser=request_meta["browser"],
                os=request_meta["os"],
                status=1,  # 登录成功
                session_id=session_id
            )
            # JWT Token中只存储不变的用户标识信息
            token_data = {
                "id": user.id.__str__(),
                "username": user.username,
                "session_id": session_id,
            }
            accessToken = await AuthController.create_token(
                data=token_data,
                expires_delta=timedelta(minutes=params.login_days * 24 * 60),
            )
            expiresTime = (
                datetime.now() + timedelta(minutes=params.login_days * 24 * 60)
            ).timestamp()
            refreshToken = await AuthController.create_token(
                data=token_data,
                expires_delta=timedelta(minutes=(params.login_days * 24 + 2) * 60),
            )
            await request.app.state.redis.set(
                f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}",
                accessToken,
                ex=timedelta(minutes=params.login_days * 24 * 60),
            )
            # 将完整的用户信息存储到Redis中，包括动态权限信息

            userInfoStr = json.dumps(userInfo, ensure_ascii=False, default=str)
            await request.app.state.redis.set(
                f"{RedisKeyConfig.USER_INFO.key}:{user.id.__str__()}",
                userInfoStr,
                ex=timedelta(
                    minutes=params.login_days * 24 * 60
                ),  # 与Token同样的过期时间
            )
            
            # 发送登录通知
            notification_service = NotificationService(request.app.state.redis)
            await notification_service.send_login_notification(
                user_id=user.id.__str__(),
                username=user.username,
                login_ip=request_meta["ip"],
                login_location=request_meta["location"],
                browser=request_meta["browser"],
                os=request_meta["os"]
            )
            
            if request_from_swagger or request_from_redoc:
                return {
                    "access_token": accessToken,
                    "token_type": "Bearer",
                    "expires_in": expiresTime * 60,
                }
            else:
                return ResponseUtil.success(
                    data={"accessToken": accessToken, "refreshToken": refreshToken}
                )
        else:
            # 记录登录失败日志
            request_meta = get_login_meta(request)
            await SystemLoginLog.create(
                user_id=user,
                login_ip=request_meta["ip"],
                login_location=request_meta["location"],
                browser=request_meta["browser"],
                os=request_meta["os"],
                status=0,  # 登录失败
                session_id=None
            )
            return ResponseUtil.error(msg="用户或密码错误！")
    else:
        # 记录登录失败日志（用户不存在的情况）
        request_meta = get_login_meta(request)
        await SystemLoginLog.create(
            user_id=None,
            login_ip=request_meta["ip"],
            login_location=request_meta["location"],
            browser=request_meta["browser"],
            os=request_meta["os"],
            status=0,  # 登录失败
            session_id=None
        )
        return ResponseUtil.error(msg="用户或密码错误！")


@authAPI.post(
    "/register",
    response_class=JSONResponse,
    response_model=LoginResponse,
    summary="用户注册",
)
async def register(request: Request, params: RegisterUserParams):
    async def _create_user(
        params: RegisterUserParams,
        department: Optional[SystemDepartment],
    ) -> Optional[SystemUser]:
        """真正执行数据库写入，成功返回用户对象，否则返回 None。"""
        hashed_pwd = await PasswordUtil.get_password_hash(
            input_password=params.password
        )
        return await SystemUser.create(
            username=params.username,
            password=hashed_pwd,
            nickname=params.nickname,
            phone=params.phone,
            email=params.email,
            gender=params.gender,
            department=department,
            status=params.status,
        )

    redis = request.app.state.redis
    key = f"{RedisKeyConfig.SYSTEM_CONFIG.key}"

    # 并行读取 4 个配置
    (
        captcha_enabled,
        register_enabled,
        default_dept_id,
        default_role_id,
    ) = await redis.mget(
        f"{key}:account_captcha_enabled",
        f"{key}:account_register_enabled",
        f"{key}:default_department_id",
        f"{key}:default_role_id",
    )
    captcha_enabled = captcha_enabled == "true"
    register_enabled = register_enabled == "true"

    if not register_enabled:
        return ResponseUtil.error(msg="注册功能已关闭！")

    # 验证码校验
    if captcha_enabled:
        result = await Email.verify_code(
            request, username=params.username, mail=params.email, code=params.code
        )
        if not result["status"]:
            return ResponseUtil.error(msg=result["msg"])

    # 重名校验
    if await SystemUser.get_or_none(username=params.username, is_del=False):
        return ResponseUtil.error(msg="注册失败，用户已存在！")

    # 确定部门
    dept_id = params.department_id or default_dept_id
    department: Optional[SystemDepartment] = None
    if dept_id and (
        department := await SystemDepartment.get_or_none(id=dept_id, is_del=False)
    ):
        pass  # 已找到部门
    # 如果 dept_id 为空或部门不存在，department 保持 None

    # 统一创建用户
    user = await _create_user(params, department)
    if not user:
        return ResponseUtil.error(msg="注册失败！")

    # 绑定默认角色
    if default_role_id:
        await SystemUserRole.create(user_id=user.id, role_id=default_role_id)

    return ResponseUtil.success(msg="注册成功！")


@authAPI.post(
    "/code",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取邮件验证码",
)
async def get_code(request: Request, params: GetEmailCodeParams):
    result = await Email.send_email(
        request, username=params.username, title=params.title, mail=params.mail
    )
    if result:
        return ResponseUtil.success(msg="验证码发送成功！")
    return ResponseUtil.error(msg="验证码发送失败！")


@authAPI.get(
    "/info",
    response_class=JSONResponse,
    response_model=GetUserInfoResponse,
    summary="获取用户信息",
)
@Log(title="获取用户信息", operation_type=OperationType.SELECT)
async def info(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
 
    return ResponseUtil.success(data=current_user)


@authAPI.get(
    "/routes",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取用户路由",
)
@Log(title="获取用户路由", operation_type=OperationType.SELECT)
async def get_user_routes(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    permission_cache = await request.app.state.redis.get(
        f"{RedisKeyConfig.USER_ROUTES.key}:{current_user['id']}"
    )
    if permission_cache:
        return ResponseUtil.success(data=json.loads(permission_cache))
    uid = current_user.get("id")
    # 获取用户身份等级
    user_type = current_user.get("user_type", 3)
    
    # 使用 Casbin 获取用户的菜单权限
    from utils.casbin import CasbinEnforcer
    user_permissions = await CasbinEnforcer.get_user_permissions(str(uid))
    menu_ids = user_permissions["menus"]
    
    # 获取菜单权限详情，并根据用户身份过滤
    rolePermissions = []
    if menu_ids:
        rolePermissions = await SystemPermission.filter(
            id__in=menu_ids,
            menu_type=0,  # 只获取菜单类型
            min_user_type__gte=user_type,  # 用户身份需满足权限要求
            is_del=False
        ).values(
            id="id",
            created_at="created_at",
            updated_at="updated_at",
            menu_type="menu_type",
            parent_id="parent_id",
            component="component",
            name="name",
            title="title",
            path="path",
            icon="icon",
            showBadge="showBadge",
            showTextBadge="showTextBadge",
            isHide="isHide",
            isHideTab="isHideTab",
            link="link",
            isIframe="isIframe",
            keepAlive="keepAlive",
            isFirstLevel="isFirstLevel",
            fixedTab="fixedTab",
            activePath="activePath",
            isFullPage="isFullPage",
            order="order",
            authTitle="authTitle",
            authMark="authMark",
            min_user_type="min_user_type",
        )
    
    # 获取按钮权限用于 authList
    button_ids = user_permissions["buttons"]
    buttonPermissions = []
    if button_ids:
        buttonPermissions = await SystemPermission.filter(
            id__in=button_ids,
            menu_type=1,  # 按钮类型
            min_user_type__gte=user_type,
            is_del=False
        ).values(
            id="id",
            parent_id="parent_id",
            authTitle="authTitle",
            authMark="authMark",
            min_user_type="min_user_type",
        )

    async def find_node_recursive(node_id: str, data: list) -> dict:
        """
        递归查找节点
        :param node_id: 节点ID
        :param data: 数据
        """
        result = {}
        data = list(filter(lambda x: x.get("menu_type") == 0, data))
        for item in data:
            if item["id"] == node_id:
                children = []
                for child_item in data:
                    if child_item["parent_id"] == node_id:
                        child_node = await find_node_recursive(child_item["id"], data)
                        if child_node:
                            children.append(child_node)
                meta = {
                    k: v
                    for k, v in {
                        "title": item["title"],
                        "order": item["order"],
                        "icon": item["icon"],
                        "showBadge": item["showBadge"],
                        "showTextBadge": item["showTextBadge"],
                        "keepAlive": item["keepAlive"],
                        "isHide": item["isHide"],
                        "isHideTab": item["isHideTab"],
                        "link": item["link"],
                        "isIframe": item["isIframe"],
                        "isFullPage": item["isFullPage"],
                        "fixedTab": item["fixedTab"],
                        "isFirstLevel": item["isFirstLevel"],
                        "minUserType": item.get("min_user_type", 3),
                        "authList": await get_menu_auth_list(
                            item["id"], buttonPermissions, user_type
                        ),
                    }.items()
                    if v is not None
                }
                result = {
                    "name": item["name"],
                    "path": item["path"],
                    "meta": meta,
                    "children": children,
                }
                if item["component"]:
                    result["component"] = (
                        item["component"]
                        .replace(".vue", "")
                        .replace(".ts", "")
                        .replace(".tsx", "")
                        .replace(".js", "")
                        .replace(".jsx", "")
                        .strip()
                    )
                if result["name"] == "":
                    result.pop("name")
                if result["children"] == []:
                    result.pop("children")
                else:
                    result["children"] = sorted(
                        result["children"], key=lambda x: x["meta"]["order"]
                    )
                break
        return result

    async def find_complete_data(data: list) -> list:
        """
        查找完整数据
        :param data: 数据
        """
        complete_data = []
        root_ids = [item["id"] for item in data if not item["parent_id"]]
        for root_id in root_ids:
            complete_data.append(await find_node_recursive(root_id, data))
        return complete_data

    permissions = await find_complete_data(rolePermissions)
    
    # 添加基础公共路由（所有用户都可以访问）
    base_routes = await get_base_public_routes()
    all_routes = base_routes + permissions
    
    await request.app.state.redis.set(
        f"{RedisKeyConfig.USER_ROUTES.key}:{current_user['id']}",
        json.dumps(all_routes,ensure_ascii=False,default=str),
        ex=timedelta(minutes=30),
    )
    return ResponseUtil.success(code=200, data=all_routes)


async def get_base_public_routes() -> list:
    """
    获取基础公共路由（所有用户都可以访问的路由）
    对应前端 src/router/routes/modules/base.ts 中定义的路由
    """
    return [
        {
            "name": "Dashboard",
            "path": "/dashboard",
            "component": "/index/index",
            "meta": {
                "title": "menus.dashboard.title",
                "icon": "&#xe721;",
                "order": 1
            },
            "children": [
                {
                    "name": "Console",
                    "path": "/dashboard/console",
                    "component": "/dashboard/console",
                    "meta": {
                        "title": "menus.dashboard.console",
                        "icon": "&#xe721;",
                        "keepAlive": False,
                        "fixedTab": True
                    }
                }
            ]
        },
        {
            "name": "UserCenter_",
            "path": "/user-center",
            "component": "/index/index",
            "meta": {
                "title": "menus.system.userCenter",
                "icon": "&#xe6bd;",
                "order": 999
            },
            "children": [
                {
                    "name": "UserCenter",
                    "path": "/user-center",
                    "component": "/user-center",
                    "meta": {
                        "title": "menus.system.userCenter",
                        "keepAlive": False,
                        "isHide": True
                    }
                }
            ]
        },
        {
            "name": "PersonalLoginRecord_",
            "path": "/personal-login-record",
            "component": "/index/index",
            "meta": {
                "title": "menus.personalLoginRecord.title",
                "icon": "&#xe6ce;",
                "order": 999
            },
            "children": [
                {
                    "name": "PersonalLoginRecord",
                    "path": "/personal-login-record",
                    "component": "/personal-login-record/index",
                    "meta": {
                        "title": "menus.personalLoginRecord.title",
                        "icon": "&#xe6ce;",
                        "keepAlive": False,
                        "isHide": True
                    }
                }
            ]
        },
        {
            "name": "PersonalOperationRecord_",
            "path": "/personal-operation-record",
            "component": "/index/index",
            "meta": {
                "title": "menus.personalOperationRecord.title",
                "icon": "&#xe6df;",
                "order": 999
            },
            "children": [
                {
                    "name": "PersonalOperationRecord",
                    "path": "/personal-operation-record",
                    "component": "/personal-operation-record/index",
                    "meta": {
                        "title": "menus.personalOperationRecord.title",
                        "icon": "&#xe6df;",
                        "keepAlive": False,
                        "isHide": True
                    }
                }
            ]
        },
        {
            "name": "MyNotification_",
            "path": "/my-notification",
            "component": "/index/index",
            "meta": {
                "title": "menus.myNotification.title",
                "icon": "&#xe6c2;",
                "order": 999
            },
            "children": [
                {
                    "name": "MyNotification",
                    "path": "/my-notification",
                    "component": "/my-notification/index",
                    "meta": {
                        "title": "menus.myNotification.title",
                        "icon": "&#xe6c2;",
                        "keepAlive": False,
                        "isHide": True
                    }
                }
            ]
        }
    ]


async def get_menu_auth_list(menu_id: str, button_permissions: list, user_type: int = 3) -> list:
    """
    获取指定菜单的按钮权限列表（已根据用户身份过滤）
    :param menu_id: 菜单ID
    :param button_permissions: 按钮权限数据（已过滤）
    :param user_type: 用户身份等级
    :return: 按钮权限列表
    """
    auth_list = []
    for perm in button_permissions:
        if str(perm.get("parent_id")) == str(menu_id):
            # 检查用户身份是否满足权限要求
            min_required = perm.get("min_user_type", 3)
            if user_type <= min_required:  # 用户身份等级越低，权限越高
                if perm.get("authTitle") and perm.get("authMark"):
                    auth_list.append({
                        "title": perm["authTitle"], 
                        "authMark": perm["authMark"],
                        "minUserType": min_required
                    })
    return auth_list


@authAPI.post(
    "/logout",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="用户登出",
)
@Log(title="退出登录", operation_type=OperationType.GRANT)
async def logout(request: Request, status: bool = Depends(AuthController.logout)):
    if status:
        return ResponseUtil.success(data="退出成功！")
    return ResponseUtil.error(data="登出失败！")


@authAPI.post(
    "/refreshToken",
    response_class=JSONResponse,
    response_model=LoginResponse,
    summary="刷新token",
)
@Log(title="刷新token", operation_type=OperationType.GRANT)
async def refresh_token(
    request: Request, current_user: dict = Depends(AuthController.get_current_user)
):
    session_id = uuid.uuid4().__str__()
    accessToken = await AuthController.create_token(
        data={
            "user": current_user,
            "id": current_user.get("id"),
            "session_id": session_id,
        },
        expires_delta=timedelta(minutes=2 * 24 * 60),
    )
    expiresTime = (datetime.now() + timedelta(minutes=2 * 24 * 60)).timestamp()
    refreshToken = await AuthController.create_token(
        data={
            "user": current_user,
            "id": current_user.get("id"),
            "session_id": session_id,
        },
        expires_delta=timedelta(minutes=(4 * 24 + 2) * 60),
    )
    return ResponseUtil.success(
        data={
            "accessToken": accessToken,
            "refreshToken": refreshToken,
            "expiresTime": expiresTime,
        }
    )
