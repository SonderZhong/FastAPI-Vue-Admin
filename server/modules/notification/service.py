# _*_ coding : UTF-8 _*_

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tortoise.models import Q

from core.common import BaseService
from modules import SystemUser
from modules.notification.model import (
    SystemNotification, UserNotification,
    NotificationScope, NotificationStatus,
)
from utils.permission import DepartmentHelper, UserType


class NotificationService(BaseService):
    model = SystemNotification

    # ==================== 权限检查 ====================

    @staticmethod
    def can_view_notification(
        notification: SystemNotification,
        user_type: int,
        user_id: str,
        department_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ) -> bool:
        if user_type <= UserType.TENANT_ADMIN:
            return True
        if str(notification.creator_id) == user_id:
            return True
        if notification.scope == NotificationScope.ALL:
            return True

        dept_ids = set()
        if department_id:
            dept_ids.add(department_id)
        if sub_departments:
            dept_ids.update(sub_departments)

        if notification.scope == NotificationScope.DEPARTMENT:
            n_scope_ids = notification.scope_ids or []
            if any(str(dept_id) in [str(s) for s in n_scope_ids] for dept_id in dept_ids):
                return True
        return False

    # ==================== 目标用户解析 ====================

    @staticmethod
    async def _get_target_users(notification: SystemNotification) -> List[str]:
        if notification.scope == NotificationScope.ALL:
            users = await SystemUser.filter(is_del=False, status=1).values_list("id", flat=True)
            return [str(u) for u in users]

        elif notification.scope == NotificationScope.DEPARTMENT:
            all_dept_ids = set()
            for dept_id in notification.scope_ids:
                child_ids = await DepartmentHelper.get_child_department_ids(dept_id)
                all_dept_ids.update(child_ids)
            users = await SystemUser.filter(
                is_del=False, status=1, department_id__in=list(all_dept_ids)
            ).values_list("id", flat=True)
            return [str(u) for u in users]

        elif notification.scope == NotificationScope.USER:
            return notification.scope_ids

        return []

    # ==================== 业务方法 ====================

    @classmethod
    async def create_notification(cls, params: dict, user_type: int, user_id: str, sub_departments: Optional[list] = None) -> Tuple[bool, str]:
        if user_type == UserType.NORMAL_USER:
            return False, "普通用户无权创建通知"

        if user_type == UserType.DEPT_ADMIN:
            if params.get("scope") == NotificationScope.ALL:
                return False, "部门管理员无权创建全局通知"
            if params.get("scope") == NotificationScope.DEPARTMENT:
                for dept_id in (params.get("scope_ids") or []):
                    if dept_id not in (sub_departments or []):
                        return False, "无权向该部门发送通知"

        expire_time = None
        if params.get("expire_time"):
            try:
                expire_time = datetime.fromisoformat(params["expire_time"].replace("Z", "+00:00"))
            except Exception:
                pass

        notification = await cls.model.create(
            title=params["title"],
            content=params["content"],
            type=params.get("type", 2),
            scope=params.get("scope", 0),
            scope_ids=params.get("scope_ids"),
            priority=params.get("priority", 0),
            expire_time=expire_time,
            status=NotificationStatus.DRAFT,
            creator_id=user_id,
        )
        return True, str(notification.id)

    @classmethod
    async def update_notification(cls, notification_id: str, update_data: dict, user_type: int, user_id: str, sub_departments: Optional[list] = None) -> Tuple[bool, str]:
        notification = await cls.model.get_or_none(id=notification_id, is_del=False)
        if not notification:
            return False, "通知不存在"

        if notification.status != NotificationStatus.DRAFT:
            return False, "只有草稿状态的通知可以编辑"

        if user_type >= UserType.DEPT_ADMIN:
            if str(notification.creator_id) != user_id:
                return False, "无权编辑此通知"

        if update_data.get("expire_time"):
            try:
                update_data["expire_time"] = datetime.fromisoformat(
                    update_data["expire_time"].replace("Z", "+00:00")
                )
            except ValueError:
                del update_data["expire_time"]

        if update_data:
            await notification.update_from_dict(update_data)
            await notification.save()
        return True, "更新成功"

    @classmethod
    async def publish_notification(cls, notification_id: str, redis) -> Tuple[bool, str, dict]:
        notification = await cls.model.get_or_none(id=notification_id, is_del=False)
        if not notification:
            return False, "通知不存在", {}

        if notification.status != NotificationStatus.DRAFT:
            return False, "只有草稿状态的通知可以发布", {}

        target_user_ids = await cls._get_target_users(notification)
        if not target_user_ids:
            return False, "没有符合条件的目标用户", {}

        notification.status = NotificationStatus.PUBLISHED
        notification.publish_time = datetime.now()
        await notification.save()

        for uid in target_user_ids:
            await UserNotification.get_or_create(
                notification_id=notification.id,
                user_id=uid,
            )

        from utils.notification import NotificationService as PushService
        push_service = PushService(redis)
        creator = await SystemUser.get_or_none(id=notification.creator_id)
        creator_name = creator.nickname if creator else "系统"

        result = await push_service.push_notification(
            notification_id=str(notification.id),
            title=notification.title,
            content=notification.content,
            notification_type=notification.type,
            priority=notification.priority,
            target_user_ids=target_user_ids,
            creator_name=creator_name,
        )

        return True, "发布成功", {
            "total_users": len(target_user_ids),
            "online_count": result["online_count"],
            "offline_count": result["offline_count"],
        }

    @classmethod
    async def revoke_notification(cls, notification_id: str, user_type: int, user_id: str) -> Tuple[bool, str]:
        notification = await cls.model.get_or_none(id=notification_id, is_del=False)
        if not notification:
            return False, "通知不存在"

        if notification.status != NotificationStatus.PUBLISHED:
            return False, "只有已发布的通知可以撤回"

        if user_type >= UserType.DEPT_ADMIN:
            if str(notification.creator_id) != user_id:
                return False, "无权撤回此通知"

        notification.status = NotificationStatus.REVOKED
        await notification.save()
        return True, "撤回成功"

    @classmethod
    async def delete_notification(cls, notification_id: str, user_type: int, user_id: str) -> Tuple[bool, str]:
        notification = await cls.model.get_or_none(id=notification_id, is_del=False)
        if not notification:
            return False, "通知不存在"

        if user_type >= UserType.DEPT_ADMIN:
            if str(notification.creator_id) != user_id:
                return False, "无权删除此通知"

        notification.is_del = True
        await notification.save()
        return True, "删除成功"

    @classmethod
    async def get_notification_list(
        cls,
        page: int,
        page_size: int,
        user_type: int,
        user_id: str,
        department_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        base_filter = Q(is_del=False)
        if filters:
            if filters.get("type") is not None:
                base_filter &= Q(type=filters["type"])
            if filters.get("status") is not None:
                base_filter &= Q(status=filters["status"])
            if filters.get("title"):
                base_filter &= Q(title__icontains=filters["title"])

        if user_type <= UserType.TENANT_ADMIN:
            pass
        elif user_type == UserType.DEPT_ADMIN:
            dept_ids = set()
            if department_id:
                dept_ids.add(department_id)
            if sub_departments:
                dept_ids.update(sub_departments)

            scope_filter = Q(creator_id=user_id) | Q(scope=NotificationScope.ALL)
            base_filter &= scope_filter
        else:
            base_filter &= Q(creator_id=user_id)

        if user_type == UserType.DEPT_ADMIN:
            dept_ids = set()
            if department_id:
                dept_ids.add(department_id)
            if sub_departments:
                dept_ids.update(sub_departments)

            managed_user_ids = set()
            if dept_ids:
                users_in_depts = await SystemUser.filter(
                    is_del=False,
                    department_id__in=list(dept_ids),
                ).values_list("id", flat=True)
                managed_user_ids = set(str(u) for u in users_in_depts)

            type_val = filters.get("type") if filters else None
            status_val = filters.get("status") if filters else None
            title_val = filters.get("title") if filters else None

            all_notifications = await cls.model.filter(
                Q(is_del=False) &
                (Q(type=type_val) if type_val is not None else Q()) &
                (Q(status=status_val) if status_val is not None else Q()) &
                (Q(title__icontains=title_val) if title_val else Q())
            ).order_by("-created_at").prefetch_related("creator").values(
                "id", "title", "content", "type", "scope", "scope_ids",
                "status", "priority", "publish_time", "expire_time",
                "created_at", "updated_at",
                creator_id="creator_id",
                creator_name="creator__nickname",
            )

            filtered_result = []
            for n in all_notifications:
                if str(n.get("creator_id")) == user_id:
                    filtered_result.append(n)
                    continue
                if n.get("scope") == NotificationScope.ALL:
                    filtered_result.append(n)
                    continue
                if n.get("scope") == NotificationScope.DEPARTMENT:
                    n_scope_ids = n.get("scope_ids") or []
                    if any(str(dept_id) in [str(s) for s in n_scope_ids] for dept_id in dept_ids):
                        filtered_result.append(n)
                    continue
                if n.get("scope") == NotificationScope.USER:
                    n_scope_ids = n.get("scope_ids") or []
                    if any(str(s) in managed_user_ids for s in n_scope_ids):
                        filtered_result.append(n)
                    continue

            total = len(filtered_result)
            result = filtered_result[(page - 1) * page_size: page * page_size]
        else:
            total = await cls.model.filter(base_filter).count()
            result = await cls.model.filter(base_filter).order_by("-created_at").offset(
                (page - 1) * page_size
            ).limit(page_size).prefetch_related("creator").values(
                "id", "title", "content", "type", "scope", "scope_ids",
                "status", "priority", "publish_time", "expire_time",
                "created_at", "updated_at",
                creator_id="creator_id",
                creator_name="creator__nickname",
            )

        return result, total

    @classmethod
    async def get_notification_info(cls, notification_id: str, user_type: int, user_id: str, department_id: Optional[str] = None, sub_departments: Optional[list] = None):
        notification = await cls.model.get_or_none(id=notification_id, is_del=False).prefetch_related("creator")
        if not notification:
            return None, "通知不存在"

        if not cls.can_view_notification(notification, user_type, user_id, department_id, sub_departments):
            return None, "无权查看此通知"

        total_count = await UserNotification.filter(notification_id=notification_id).count()
        read_count = await UserNotification.filter(notification_id=notification_id, is_read=True).count()

        data = {
            "id": str(notification.id),
            "title": notification.title,
            "content": notification.content,
            "type": notification.type,
            "scope": notification.scope,
            "scope_ids": notification.scope_ids,
            "status": notification.status,
            "priority": notification.priority,
            "publish_time": notification.publish_time,
            "expire_time": notification.expire_time,
            "created_at": notification.created_at,
            "updated_at": notification.updated_at,
            "creator_id": str(notification.creator_id) if notification.creator_id else None,
            "creator_name": notification.creator.nickname if notification.creator else None,
            "statistics": {
                "total": total_count,
                "read": read_count,
                "unread": total_count - read_count,
            },
        }
        return data, None


class UserNotificationService(BaseService):
    model = UserNotification

    @classmethod
    async def get_my_notifications(
        cls,
        page: int,
        page_size: int,
        user_id: str,
        is_read: Optional[bool] = None,
        type: Optional[int] = None,
    ):
        base_filter = Q(user_id=user_id) & Q(notification__is_del=False) & Q(notification__status=NotificationStatus.PUBLISHED)

        if is_read is not None:
            base_filter &= Q(is_read=is_read)
        if type is not None:
            base_filter &= Q(notification__type=type)

        expire_filter = Q(notification__expire_time__isnull=True) | Q(notification__expire_time__gt=datetime.now())
        final_filter = base_filter & expire_filter

        total = await cls.model.filter(final_filter).count()
        result = await cls.model.filter(final_filter).order_by(
            "-created_at"
        ).offset((page - 1) * page_size).limit(page_size).prefetch_related(
            "notification", "notification__creator"
        ).values(
            "id", "is_read", "read_time", "created_at",
            notification_id="notification_id",
            title="notification__title",
            content="notification__content",
            notification_type="notification__type",
            priority="notification__priority",
            publish_time="notification__publish_time",
            creator_name="notification__creator__nickname",
        )

        return result, total

    @classmethod
    async def mark_read(cls, user_notification_id: str, user_id: str, redis) -> Tuple[bool, str]:
        user_notification = await cls.model.get_or_none(id=user_notification_id, user_id=user_id)
        if not user_notification:
            return False, "通知不存在"

        if not user_notification.is_read:
            user_notification.is_read = True
            user_notification.read_time = datetime.now()
            await user_notification.save()

            from utils.notification import NotificationService as PushService
            push_service = PushService(redis)
            await push_service.decrement_unread_count(user_id)

        return True, "已标记为已读"

    @classmethod
    async def mark_all_read(cls, user_id: str, redis) -> Tuple[bool, str]:
        count = await cls.model.filter(
            user_id=user_id, is_read=False,
        ).update(is_read=True, read_time=datetime.now())

        from utils.notification import NotificationService as PushService
        push_service = PushService(redis)
        await push_service.reset_unread_count(user_id)

        return True, f"已将 {count} 条通知标记为已读"

    @classmethod
    async def get_unread_count(cls, user_id: str, redis) -> int:
        count = await cls.model.filter(
            user_id=user_id,
            is_read=False,
            notification__is_del=False,
            notification__status=NotificationStatus.PUBLISHED,
        ).count()

        from utils.notification import NotificationService as PushService
        push_service = PushService(redis)
        if count > 0:
            await redis.set(f"{push_service.UNREAD_COUNT_KEY}:{user_id}", count)
        else:
            await redis.delete(f"{push_service.UNREAD_COUNT_KEY}:{user_id}")

        return count
