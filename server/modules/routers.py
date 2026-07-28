# _*_ coding : UTF-8 _*_

from fastapi import FastAPI

from modules.auth.router import authAPI
from modules.cache.router import cacheAPI
from modules.config.router import configAPI
from modules.dashboard.router import dashboardAPI
from modules.department.router import departmentAPI
from modules.dictionary.router import dictionaryAPI
from modules.doc.router import docAPI
from modules.file.router import authFileAPI, fileAccessAPI, fileAPI
from modules.log.router import logAPI
from modules.notification.router import notificationAPI, notificationWsAPI
from modules.permission.router import permissionAPI
from modules.role.router import roleAPI
from modules.server_info.router import serverAPI
from modules.tenant.router import tenantAPI
from modules.user.router import userAPI

api_list = [
    {"api": authAPI, "tags": ["用户认证"]},
    {"api": dashboardAPI, "tags": ["工作台"]},
    {"api": userAPI, "tags": ["用户管理"]},
    {"api": departmentAPI, "tags": ["部门管理"]},
    {"api": roleAPI, "tags": ["角色管理"]},
    {"api": permissionAPI, "tags": ["权限管理"]},
    {"api": logAPI, "tags": ["日志管理"]},
    {"api": notificationAPI, "tags": ["通知管理"]},
    {"api": notificationWsAPI, "tags": ["通知WebSocket"]},
    {"api": configAPI, "tags": ["系统配置"]},
    {"api": cacheAPI, "tags": ["缓存管理"]},
    {"api": serverAPI, "tags": ["服务器信息"]},
    {"api": tenantAPI, "tags": ["租户管理"]},
    {"api": fileAPI, "tags": ["文件管理"]},
    {"api": authFileAPI, "tags": ["文件管理"]},
    {"api": fileAccessAPI, "tags": ["文件访问"]},
    {"api": docAPI, "tags": ["API文档"]},
    {"api": dictionaryAPI, "tags": ["数据字典"]},
]


def register_api(app: FastAPI) -> None:
    """所有接口直接挂载，前端通过 /api 代理转发"""
    for item in api_list:
        app.include_router(router=item["api"], tags=item["tags"])
