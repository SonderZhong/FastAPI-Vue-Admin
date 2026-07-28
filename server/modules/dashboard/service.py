# _*_ coding : UTF-8 _*_
from __future__ import annotations

from asyncio import gather
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from modules.log.model import SystemLoginLog, SystemOperationLog
from modules.notification.model import NotificationStatus, UserNotification
from utils.permission import UserType


class DashboardService:
    """工作台统计服务。"""

    @staticmethod
    def _day_range(days: int = 7) -> tuple[datetime, datetime]:
        now = datetime.now()
        start = datetime.combine((now - timedelta(days=days - 1)).date(), datetime.min.time())
        end = datetime.combine(now.date(), datetime.max.time())
        return start, end

    @staticmethod
    def _today_range() -> tuple[datetime, datetime]:
        now = datetime.now()
        start = datetime.combine(now.date(), datetime.min.time())
        end = datetime.combine(now.date(), datetime.max.time())
        return start, end

    @staticmethod
    def _build_access_filter(current_user: dict, operator_field: str) -> dict[str, Any]:
        user_type = current_user.get("user_type", UserType.NORMAL_USER)
        user_id = str(current_user.get("id", ""))
        tenant_id = current_user.get("tenant_id")
        department_id = current_user.get("department_id")
        sub_departments = [str(item) for item in (current_user.get("sub_departments") or [])]

        filters: dict[str, Any] = {"is_del": False}
        if tenant_id:
            filters["tenant_id"] = tenant_id

        if user_type in (UserType.SUPER_ADMIN, UserType.TENANT_ADMIN):
            return filters

        if user_type == UserType.DEPT_ADMIN:
            if department_id:
                dept_ids = {str(department_id), *sub_departments}
                filters["department_id__in"] = list(dept_ids)
            else:
                filters[operator_field] = user_id
            return filters

        filters[operator_field] = user_id
        return filters

    @staticmethod
    def _format_distribution(
        counter: Counter[str], *, limit: int = 8, empty_label: str = "未知"
    ) -> list[dict[str, Any]]:
        return [
            {"name": name or empty_label, "value": value}
            for name, value in counter.most_common(limit)
        ]

    @staticmethod
    def _safe_rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)

    @classmethod
    async def get_dashboard_statistics(cls, current_user: dict) -> dict[str, Any]:
        user_id = str(current_user.get("id"))
        today_start, today_end = cls._today_range()
        week_start, week_end = cls._day_range(7)

        (
            unread_notifications,
            total_notifications,
            today_logins,
            week_logins,
            today_operations,
            week_operations,
        ) = await gather(
            UserNotification.filter(
                user_id=user_id,
                is_read=False,
                is_del=False,
                notification__is_del=False,
                notification__status=NotificationStatus.PUBLISHED,
            ).count(),
            UserNotification.filter(
                user_id=user_id,
                is_del=False,
                notification__is_del=False,
                notification__status=NotificationStatus.PUBLISHED,
            ).count(),
            SystemLoginLog.filter(
                user_id=user_id,
                is_del=False,
                status=1,
                created_at__range=[today_start, today_end],
            ).count(),
            SystemLoginLog.filter(
                user_id=user_id,
                is_del=False,
                status=1,
                created_at__range=[week_start, week_end],
            ).count(),
            SystemOperationLog.filter(
                operator_id=user_id,
                is_del=False,
                created_at__range=[today_start, today_end],
            ).count(),
            SystemOperationLog.filter(
                operator_id=user_id,
                is_del=False,
                created_at__range=[week_start, week_end],
            ).count(),
        )

        read_notifications = max(total_notifications - unread_notifications, 0)
        return {
            "unreadNotifications": unread_notifications,
            "totalNotifications": total_notifications,
            "todayLogins": today_logins,
            "todayOperations": today_operations,
            "weekLogins": week_logins,
            "weekOperations": week_operations,
            "notificationReadRate": cls._safe_rate(read_notifications, total_notifications),
        }

    @classmethod
    async def get_login_statistics(cls, current_user: dict) -> dict[str, Any]:
        start, end = cls._day_range(7)
        filters = cls._build_access_filter(current_user, "user_id")
        filters.update({"created_at__range": [start, end], "status": 1})

        rows = await SystemLoginLog.filter(**filters).values("os", "browser", "login_location")

        os_counter: Counter[str] = Counter()
        browser_counter: Counter[str] = Counter()
        location_counter: Counter[str] = Counter()

        for row in rows:
            os_counter[row.get("os") or "未知系统"] += 1
            browser_counter[row.get("browser") or "未知浏览器"] += 1
            raw_location = (row.get("login_location") or "").strip()
            location = raw_location.split(" ")[0] if raw_location else "未知地区"
            location_counter[location] += 1

        return {
            "osDistribution": cls._format_distribution(os_counter, empty_label="未知系统"),
            "browserDistribution": cls._format_distribution(
                browser_counter, empty_label="未知浏览器"
            ),
            "locationDistribution": cls._format_distribution(
                location_counter, empty_label="未知地区"
            ),
        }

    @classmethod
    async def get_login_trend(cls, current_user: dict) -> dict[str, Any]:
        start, end = cls._day_range(7)
        filters = cls._build_access_filter(current_user, "user_id")
        filters.update({"created_at__range": [start, end], "status": 1})

        rows = await SystemLoginLog.filter(**filters).values("created_at", "login_location")

        date_keys = [start.date() + timedelta(days=index) for index in range(7)]
        date_labels = [item.strftime("%Y-%m-%d") for item in date_keys]
        total_counter = {label: 0 for label in date_labels}
        location_counters: dict[str, dict[str, int]] = defaultdict(
            lambda: {label: 0 for label in date_labels}
        )

        for row in rows:
            created_at = row.get("created_at")
            if not created_at:
                continue
            date_label = created_at.strftime("%Y-%m-%d")
            if date_label not in total_counter:
                continue
            total_counter[date_label] += 1
            raw_location = (row.get("login_location") or "").strip()
            location = raw_location.split(" ")[0] if raw_location else "未知地区"
            location_counters[location][date_label] += 1

        location_totals = sorted(
            ((name, sum(day_counts.values())) for name, day_counts in location_counters.items()),
            key=lambda item: item[1],
            reverse=True,
        )[:4]

        location_series = [
            {"name": name, "data": [location_counters[name][label] for label in date_labels]}
            for name, _ in location_totals
        ]

        return {
            "dates": date_labels,
            "loginCounts": [total_counter[label] for label in date_labels],
            "locationSeries": location_series,
        }

    @classmethod
    async def get_operation_statistics(cls, current_user: dict) -> dict[str, Any]:
        start, end = cls._day_range(7)
        filters = cls._build_access_filter(current_user, "operator_id")
        filters.update({"created_at__range": [start, end]})

        rows = await SystemOperationLog.filter(**filters).values(
            "created_at", "operation_type", "request_path", "operation_name"
        )

        # 兼容历史操作日志：早期数据未写入 tenant_id，导致租户过滤后统计为空。
        if (
            not rows
            and filters.get("tenant_id")
            and (
                filters.get("operator_id")
                or filters.get("department_id__in")
                or filters.get("department_id")
            )
        ):
            fallback_filters = dict(filters)
            fallback_filters.pop("tenant_id", None)
            rows = await SystemOperationLog.filter(**fallback_filters).values(
                "created_at", "operation_type", "request_path", "operation_name"
            )

        type_mapping = {
            0: "其他",
            1: "新增",
            2: "修改",
            3: "删除",
            4: "查询",
            5: "导入",
            6: "导出",
            7: "授权",
            8: "强退",
            9: "生成",
            10: "清空",
        }

        def normalize_module(row: dict[str, Any]) -> str:
            request_path = (row.get("request_path") or "").strip("/")
            if request_path:
                parts = request_path.split("/")
                first = parts[0]
                if first and first != "api":
                    return first
                if len(parts) > 1:
                    return parts[1]
            operation_name = row.get("operation_name") or ""
            return operation_name[:8] if operation_name else "未知模块"

        date_keys = [start.date() + timedelta(days=index) for index in range(7)]
        date_labels = [item.strftime("%Y-%m-%d") for item in date_keys]
        daily_counter = {label: 0 for label in date_labels}
        type_counter: Counter[str] = Counter()
        module_counter: Counter[str] = Counter()

        for row in rows:
            created_at = row.get("created_at")
            if created_at:
                label = created_at.strftime("%Y-%m-%d")
                if label in daily_counter:
                    daily_counter[label] += 1

            type_name = type_mapping.get(row.get("operation_type"), "其他")
            type_counter[type_name] += 1
            module_counter[normalize_module(row)] += 1

        return {
            "dates": date_labels,
            "typeDistribution": cls._format_distribution(type_counter, empty_label="其他"),
            "dailyTrend": [daily_counter[label] for label in date_labels],
            "moduleDistribution": cls._format_distribution(
                module_counter, empty_label="未知模块"
            ),
        }
