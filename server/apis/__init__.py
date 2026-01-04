# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:41
# @UpdateTime : 2025/08/04 01:41
# @Author : sonder
# @File : __init__.py
# @Software : PyCharm
# @Comment : 本程序
from fastapi import FastAPI

from apis.auth import authAPI
from apis.cache import cacheAPI
from apis.casbin import casbinAPI
from apis.config import configAPI
from apis.dashboard import dashboardAPI
from apis.department import departmentAPI
from apis.doc import docAPI
from apis.file import fileAPI, authFileAPI, fileAccessAPI
from apis.log import logAPI
from apis.notification import notificationAPI, notificationWsAPI
from apis.permission import permissionAPI
from apis.role import roleAPI
from apis.server import serverAPI
from apis.user import userAPI


system_api_list = [
    {
        "api": authAPI,
        "tags": ["用户认证"]
    },
    {
        "api": userAPI,
        "tags": ["用户管理"]
    },
    {
        "api": departmentAPI,
        "tags": ["部门管理"]
    },
    {
        "api": roleAPI,
        "tags": ["角色管理"]
    },
    {
        "api": permissionAPI,
        "tags": ["权限管理"]
    },
    {
        "api": casbinAPI,
        "tags": ["Casbin权限策略"]
    },
    {
        "api": logAPI,
        "tags": ["日志管理"]
    },
    {
        "api": notificationAPI,
        "tags": ["通知管理"]
    },
    {
        "api": notificationWsAPI,
        "tags": ["通知WebSocket"]
    },
    {
        "api": configAPI,
        "tags": ["系统配置"]
    },
    {
        "api": cacheAPI,
        "tags": ["缓存管理"]
    },
    {
        "api": serverAPI,
        "tags": ["服务器信息"]
    },
    {
        "api": dashboardAPI,
        "tags": ["工作台"]
    },
    {
        "api": fileAPI,
        "tags": ["文件管理"]
    },
    {
        "api": authFileAPI,
        "tags": ["文件管理"]
    },
    {
        "api": fileAccessAPI,
        "tags": ["文件访问"]
    },
    {
        "api": docAPI,
        "tags": ["API文档"]
    }
]

api_list = system_api_list


def register_api(app: FastAPI) -> None:
    """
    注册路由
    """
    for api in api_list:
        app.include_router(router=api.get("api"), tags=api.get("tags"))
