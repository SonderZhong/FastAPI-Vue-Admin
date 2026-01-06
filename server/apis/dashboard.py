# _*_ coding : UTF-8 _*_
# @Time : 2025/10/21
# @Author : sonder
# @File : dashboard.py
# @Comment : 工作台数据统计API

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from tortoise.functions import Count

from annotation.auth import AuthController
from annotation.log import Log, OperationType
from models import SystemLoginLog, SystemOperationLog, UserNotification
from models.notification import NotificationStatus
from schemas.common import BaseResponse
from utils.response import ResponseUtil

dashboardAPI = APIRouter(prefix="/dashboard")


@dashboardAPI.get("/statistics", response_class=JSONResponse, response_model=BaseResponse, summary="获取工作台统计数据")
@Log(title="获取工作台统计数据", operation_type=OperationType.SELECT)
# @Auth(permission_list=["dashboard:btn:statistics", "GET:/dashboard/statistics"])
async def get_dashboard_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    获取工作台统计数据
    根据用户身份返回不同范围的统计信息
    """
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    sub_departments = current_user.get("sub_departments", [])
    
    # 获取今天的开始和结束时间
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 获取用户通知统计
    unread_notifications = await UserNotification.filter(
        user_id=user_id,
        is_read=False,
        notification__is_del=False,
        notification__status=NotificationStatus.PUBLISHED
    ).count()
    
    total_notifications = await UserNotification.filter(
        user_id=user_id,
        notification__is_del=False,
        notification__status=NotificationStatus.PUBLISHED
    ).count()
    
    # 根据用户身份获取统计数据
    if user_type in [0, 1]:
        # 超级管理员和管理员：查看所有数据
        today_logins = await SystemLoginLog.filter(
            is_del=False,
            created_at__range=[today_start, today_end],
            status=1  # 成功登录
        ).count()
        
        today_operations = await SystemOperationLog.filter(
            is_del=False,
            created_at__range=[today_start, today_end]
        ).count()
        
    elif user_type == 2:
        # 部门管理员：查看本部门及下属部门数据
        today_logins = await SystemLoginLog.filter(
            is_del=False,
            user_id__department__id__in=sub_departments,
            created_at__range=[today_start, today_end],
            status=1
        ).count()
        
        today_operations = await SystemOperationLog.filter(
            is_del=False,
            operator__department__id__in=sub_departments,
            created_at__range=[today_start, today_end]
        ).count()
        
    else:
        # 普通用户：只查看个人数据
        today_logins = await SystemLoginLog.filter(
            is_del=False,
            user_id=user_id,
            created_at__range=[today_start, today_end],
            status=1
        ).count()
        
        today_operations = await SystemOperationLog.filter(
            is_del=False,
            operator_id=user_id,
            created_at__range=[today_start, today_end]
        ).count()

    
    return ResponseUtil.success(data={
        "unreadNotifications": unread_notifications,
        "totalNotifications": total_notifications,
        "todayLogins": today_logins,
        "todayOperations": today_operations
    })


@dashboardAPI.get("/login-statistics", response_class=JSONResponse, response_model=BaseResponse, summary="获取登录统计数据")
@Log(title="获取登录统计数据", operation_type=OperationType.SELECT)
# @Auth(permission_list=["dashboard:btn:statistics", "GET:/dashboard/login-statistics"])
async def get_login_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    获取登录统计数据
    - 操作系统分布
    - 浏览器分布
    - 登录地区分布
    """
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    sub_departments = current_user.get("sub_departments", [])
    
    # 根据用户权限过滤数据
    if user_type in [0, 1]:
        # 超级管理员和管理员：查看所有数据
        login_logs = SystemLoginLog.filter(is_del=False, status=1)
    elif user_type == 2:
        # 部门管理员：查看本部门及下属部门数据
        login_logs = SystemLoginLog.filter(
            is_del=False,
            status=1,
            user_id__department__id__in=sub_departments
        )
    else:
        # 普通用户：只查看个人数据
        login_logs = SystemLoginLog.filter(
            is_del=False,
            status=1,
            user_id=user_id
        )
    
    # 统计操作系统分布
    os_stats = await login_logs.annotate(count=Count('id')).group_by('os').values('os', 'count')
    os_distribution = []
    for stat in os_stats:
        if stat['os']:
            os_distribution.append({
                "name": stat['os'],
                "value": stat['count']
            })
    
    # 统计浏览器分布
    browser_stats = await login_logs.annotate(count=Count('id')).group_by('browser').values('browser', 'count')
    browser_distribution = []
    for stat in browser_stats:
        if stat['browser']:
            browser_distribution.append({
                "name": stat['browser'],
                "value": stat['count']
            })
    
    # 统计登录地区分布（取前10）
    location_stats = await login_logs.annotate(count=Count('id')).group_by('login_location').values('login_location', 'count')
    location_distribution = []
    for stat in location_stats:
        if stat['login_location']:
            location_distribution.append({
                "name": stat['login_location'],
                "value": stat['count']
            })
    # 按数量排序，取前10
    location_distribution.sort(key=lambda x: x['value'], reverse=True)
    location_distribution = location_distribution[:10]
    
    return ResponseUtil.success(data={
        "osDistribution": os_distribution,
        "browserDistribution": browser_distribution,
        "locationDistribution": location_distribution
    })


@dashboardAPI.get("/login-trend", response_class=JSONResponse, response_model=BaseResponse, summary="获取登录趋势数据")
@Log(title="获取登录趋势数据", operation_type=OperationType.SELECT)
# @Auth(permission_list=["dashboard:btn:statistics", "GET:/dashboard/login-trend"])
async def get_login_trend(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    获取近7天登录趋势数据
    - 每日登录次数
    - 每日登录地区分布
    - 每日操作统计
    """
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    sub_departments = current_user.get("sub_departments", [])
    
    # 计算近7天的日期范围
    today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    seven_days_ago = today - timedelta(days=6)
    seven_days_ago = seven_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 根据用户权限过滤数据
    if user_type in [0, 1]:
        # 超级管理员和管理员：查看所有数据
        login_logs = SystemLoginLog.filter(
            is_del=False,
            status=1,
            created_at__range=[seven_days_ago, today]
        )
    elif user_type == 2:
        # 部门管理员：查看本部门及下属部门数据
        login_logs = SystemLoginLog.filter(
            is_del=False,
            status=1,
            user_id__department__id__in=sub_departments,
            created_at__range=[seven_days_ago, today]
        )
    else:
        # 普通用户：只查看个人数据
        login_logs = SystemLoginLog.filter(
            is_del=False,
            status=1,
            user_id=user_id,
            created_at__range=[seven_days_ago, today]
        )
    
    # 获取所有登录记录
    all_logs = await login_logs.all()
    
    # 初始化7天的数据结构
    date_dict = {}
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        date_dict[date_str] = {
            "date": date_str,
            "count": 0,
            "locations": {}
        }
    
    # 统计每天的登录次数和地区分布
    for log in all_logs:
        date_str = log.created_at.strftime('%Y-%m-%d')
        if date_str in date_dict:
            date_dict[date_str]["count"] += 1
            location = log.login_location or "未知"
            if location in date_dict[date_str]["locations"]:
                date_dict[date_str]["locations"][location] += 1
            else:
                date_dict[date_str]["locations"][location] = 1
    
    # 转换为列表格式
    dates = []
    login_counts = []
    location_trend = {}
    
    for date_str in sorted(date_dict.keys()):
        data = date_dict[date_str]
        dates.append(date_str)
        login_counts.append(data["count"])
        
        # 收集每个地区的趋势
        for location, count in data["locations"].items():
            if location not in location_trend:
                location_trend[location] = [0] * 7
            day_index = dates.index(date_str)
            location_trend[location][day_index] = count
    
    # 只取前5个活跃地区
    top_locations = sorted(location_trend.items(), key=lambda x: sum(x[1]), reverse=True)[:5]
    location_series = []
    for location, values in top_locations:
        location_series.append({
            "name": location,
            "data": values
        })
    
    return ResponseUtil.success(data={
        "dates": dates,
        "loginCounts": login_counts,
        "locationSeries": location_series
    })


@dashboardAPI.get("/operation-statistics", response_class=JSONResponse, response_model=BaseResponse, summary="获取操作统计数据")
@Log(title="获取操作统计数据", operation_type=OperationType.SELECT)
# @Auth(permission_list=["dashboard:btn:statistics", "GET:/dashboard/operation-statistics"])
async def get_operation_statistics(
    request: Request,
    current_user: dict = Depends(AuthController.get_current_user)
):
    """
    获取操作统计数据
    - 操作类型分布
    - 模块分布
    - 近7天操作趋势
    """
    user_type = current_user.get("user_type", 3)
    user_id = current_user.get("id")
    sub_departments = current_user.get("sub_departments", [])
    
    # 计算近7天的日期范围
    today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    seven_days_ago = today - timedelta(days=6)
    seven_days_ago = seven_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 根据用户权限过滤数据
    if user_type in [0, 1]:
        # 超级管理员和管理员：查看所有数据
        operation_logs = SystemOperationLog.filter(
            is_del=False,
            created_at__range=[seven_days_ago, today]
        )
    elif user_type == 2:
        # 部门管理员：查看本部门及下属部门数据
        operation_logs = SystemOperationLog.filter(
            is_del=False,
            operator__department__id__in=sub_departments,
            created_at__range=[seven_days_ago, today]
        )
    else:
        # 普通用户：只查看个人数据
        operation_logs = SystemOperationLog.filter(
            is_del=False,
            operator_id=user_id,
            created_at__range=[seven_days_ago, today]
        )
    
    # 统计操作类型分布
    type_stats = await operation_logs.annotate(count=Count('id')).group_by('operation_type').values('operation_type', 'count')
    type_distribution = []
    # 与 OperationType 枚举对应: OTHER=0, INSERT=1, DELETE=2, UPDATE=3, SELECT=4, IMPORT=5, EXPORT=6, GRANT=7
    type_names = {
        0: "其他",
        1: "新增",
        2: "删除",
        3: "修改",
        4: "查询",
        5: "导入",
        6: "导出",
        7: "授权"
    }
    for stat in type_stats:
        if stat['operation_type'] is not None:
            type_distribution.append({
                "name": type_names.get(stat['operation_type'], f"类型{stat['operation_type']}"),
                "value": stat['count']
            })
    
    # 统计模块分布
    module_stats = await operation_logs.annotate(count=Count('id')).group_by('operation_name').values('operation_name', 'count')
    module_distribution = []
    for stat in module_stats:
        if stat['operation_name']:
            module_distribution.append({
                "name": stat['operation_name'],
                "value": stat['count']
            })
    # 按数量排序，取前10
    module_distribution.sort(key=lambda x: x['value'], reverse=True)
    module_distribution = module_distribution[:10]
    
    # 获取所有操作记录用于计算每日趋势
    all_logs = await operation_logs.all()
    
    # 初始化7天的数据结构
    date_dict = {}
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        date_dict[date_str] = 0
    
    # 统计每天的操作次数
    for log in all_logs:
        date_str = log.created_at.strftime('%Y-%m-%d')
        if date_str in date_dict:
            date_dict[date_str] += 1
    
    # 转换为列表格式
    dates = sorted(date_dict.keys())
    daily_trend = [date_dict[d] for d in dates]
    
    return ResponseUtil.success(data={
        "dates": dates,
        "typeDistribution": type_distribution,
        "dailyTrend": daily_trend,
        "moduleDistribution": module_distribution
    })
