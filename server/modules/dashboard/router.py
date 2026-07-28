# _*_ coding : UTF-8 _*_
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from annotation.auth import AuthController
from annotation.log import Log, OperationType
from core.common import BaseResponse
from modules.dashboard.service import DashboardService
from utils.response import ResponseUtil

dashboardAPI = APIRouter(prefix="/dashboard")


@dashboardAPI.get(
    "/statistics",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取工作台统计卡片数据",
)
@Log(title="获取工作台统计卡片数据", operation_type=OperationType.SELECT)
async def get_dashboard_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await DashboardService.get_dashboard_statistics(current_user)
    return ResponseUtil.success(data=data)


@dashboardAPI.get(
    "/login-statistics",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取登录统计数据",
)
@Log(title="获取登录统计数据", operation_type=OperationType.SELECT)
async def get_login_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await DashboardService.get_login_statistics(current_user)
    return ResponseUtil.success(data=data)


@dashboardAPI.get(
    "/login-trend",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取登录趋势数据",
)
@Log(title="获取登录趋势数据", operation_type=OperationType.SELECT)
async def get_login_trend(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await DashboardService.get_login_trend(current_user)
    return ResponseUtil.success(data=data)


@dashboardAPI.get(
    "/operation-statistics",
    response_class=JSONResponse,
    response_model=BaseResponse,
    summary="获取操作统计数据",
)
@Log(title="获取操作统计数据", operation_type=OperationType.SELECT)
async def get_operation_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user),
):
    data = await DashboardService.get_operation_statistics(current_user)
    return ResponseUtil.success(data=data)
