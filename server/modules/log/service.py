# _*_ coding : UTF-8 _*_

from datetime import datetime
from typing import Any, Dict, Optional

from core.common import BaseService
from modules.log.model import SystemLoginLog, SystemOperationLog
from utils.get_redis import RedisKeyConfig


class LoginLogService(BaseService):
    model = SystemLoginLog

    @staticmethod
    async def get_online_session_ids(redis) -> list:
        access_token_keys = await redis.keys(f"{RedisKeyConfig.ACCESS_TOKEN.key}:*")
        if not access_token_keys:
            return []

        session_ids = []
        from jose import jwt
        from utils.config import config

        for key in access_token_keys:
            token = await redis.get(key)
            if token:
                try:
                    payload = jwt.decode(
                        token,
                        config.jwt().secret_key,
                        algorithms=[config.jwt().algorithm],
                    )
                    session_id = payload.get("session_id")
                    if session_id:
                        session_ids.append(session_id)
                except Exception:
                    pass
        return session_ids

    @staticmethod
    def _apply_user_type_filter(
        filter_args: dict,
        user_type: int,
        user_id: str,
        sub_departments: list,
        department_id: Optional[str] = None,
        is_operator: bool = False,
    ):
        if user_type in [0, 1]:
            if department_id:
                filter_args["department_id"] = department_id
            elif sub_departments:
                filter_args["department_id__in"] = sub_departments
        elif user_type == 2:
            if department_id:
                filter_args["department_id"] = department_id
            elif sub_departments:
                filter_args["department_id__in"] = sub_departments
            else:
                return False
        else:
            field = "operator_id" if is_operator else "user_id"
            filter_args[field] = user_id
        return True

    @classmethod
    async def get_login_log_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
        department_id: Optional[str] = None,
        online_session_ids: Optional[list] = None,
    ):
        filter_args = {}
        if filters:
            filter_args.update(filters)

        if not cls._apply_user_type_filter(
            filter_args, user_type, user_id, sub_departments or [], department_id
        ):
            return [], 0

        total = await cls.model.filter(**filter_args, user__is_del=False, is_del=False).count()
        result = (
            await cls.model.filter(**filter_args, user__is_del=False, is_del=False)
            .order_by("-created_at")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                id="id",
                user_id="user_id",
                username="user__username",
                user_nickname="user__nickname",
                department_id="department_id",
                department_name="department__name",
                login_ip="login_ip",
                login_location="login_location",
                browser="browser",
                os="os",
                status="status",
                session_id="session_id",
                created_at="created_at",
                updated_at="updated_at",
            )
        )

        if online_session_ids is not None:
            for log in result:
                log["online"] = log["session_id"] in online_session_ids

        return result, total

    @classmethod
    async def force_logout(
        cls,
        session_id: str,
        redis,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        log = None
        if user_type in [0, 1, 2] and sub_departments:
            log = await cls.model.get_or_none(
                department_id__in=sub_departments,
                session_id=session_id,
                is_del=False,
            )
        else:
            log = await cls.model.get_or_none(
                user_id=user_id, session_id=session_id, is_del=False
            )

        if log:
            if await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"):
                await redis.delete(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}")
                return True, "强退成功！"
        return False, "会话不存在！"

    @classmethod
    async def batch_force_logout(
        cls,
        session_ids: list,
        redis,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        for sid in session_ids:
            if user_type in [0, 1, 2] and sub_departments:
                log = await cls.model.get_or_none(
                    department_id__in=sub_departments,
                    session_id=sid,
                    is_del=False,
                )
            else:
                log = await cls.model.get_or_none(
                    user_id=user_id, session_id=sid, is_del=False
                )

            if log and await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{sid}"):
                await redis.delete(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{sid}")
        return True, "批量强退成功！"

    @classmethod
    async def delete_login_log(
        cls,
        log_id: str,
        redis,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        log = None
        if user_type in [0, 1, 2] and sub_departments:
            log = await cls.model.get_or_none(
                id=log_id, department_id__in=sub_departments, is_del=False
            )
        else:
            log = await cls.model.get_or_none(id=log_id, user_id=user_id, is_del=False)

        if log:
            log.is_del = True
            await log.save()
            if await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"):
                await redis.delete(
                    f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
                )
            return True, "删除成功"
        return False, "删除失败,登录日志不存在！"

    @classmethod
    async def batch_delete_login_log(
        cls,
        log_ids: list,
        redis,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        for log_id in set(log_ids):
            if user_type in [0, 1, 2] and sub_departments:
                log = await cls.model.get_or_none(
                    id=log_id, department_id__in=sub_departments, is_del=False
                )
            else:
                log = await cls.model.get_or_none(
                    id=log_id, user_id=user_id, is_del=False
                )

            if log:
                log.is_del = True
                await log.save()
                if await redis.get(
                    f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
                ):
                    await redis.delete(
                        f"{RedisKeyConfig.ACCESS_TOKEN.key}:{log.session_id}"
                    )
        return True, "删除成功"

    @classmethod
    async def get_personal_login_log(
        cls,
        page: int,
        page_size: int,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ):
        filter_args = {"user_id": user_id}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args, user__is_del=False, is_del=False).count()
        result = (
            await cls.model.filter(**filter_args, user__is_del=False, is_del=False)
            .order_by("-created_at")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                id="id",
                user_id="user_id",
                username="user__username",
                user_nickname="user__nickname",
                department_id="department_id",
                department_name="department__name",
                login_ip="login_ip",
                login_location="login_location",
                browser="browser",
                os="os",
                status="status",
                session_id="session_id",
                created_at="created_at",
                updated_at="updated_at",
            )
        )

        return result, total

    @classmethod
    async def personal_force_logout(cls, session_id: str, user_id: str, redis):
        if await cls.model.get_or_none(
            user_id=user_id, session_id=session_id, is_del=False
        ):
            if await redis.get(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}"):
                await redis.delete(f"{RedisKeyConfig.ACCESS_TOKEN.key}:{session_id}")
                return True, "强退成功！"
            return False, "强退失败,会话不存在！"
        return False, "强退失败,登录日志不存在！"


class OperationLogService(BaseService):
    model = SystemOperationLog

    @classmethod
    async def get_operation_log_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
        department_id: Optional[str] = None,
    ):
        filter_args = {}
        if filters:
            filter_args.update(filters)

        has_data = LoginLogService._apply_user_type_filter(
            filter_args,
            user_type,
            user_id,
            sub_departments or [],
            department_id,
            is_operator=True,
        )
        if not has_data:
            return [], 0

        total = await cls.model.filter(
            **filter_args, operator__is_del=False, is_del=False
        ).count()
        result = (
            await cls.model.filter(**filter_args, operator__is_del=False, is_del=False)
            .order_by("-created_at")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                id="id",
                created_at="created_at",
                updated_at="updated_at",
                operation_name="operation_name",
                operation_type="operation_type",
                request_path="request_path",
                request_method="request_method",
                request_params="request_params",
                response_result="response_result",
                host="host",
                location="location",
                browser="browser",
                os="os",
                user_agent="user_agent",
                operator_id="operator_id",
                operator_name="operator__username",
                operator_nickname="operator__nickname",
                department_id="department_id",
                department_name="department__name",
                status="status",
                cost_time="cost_time",
            )
        )
        return result, total

    @classmethod
    async def delete_operation_log(
        cls,
        log_id: str,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        log = None
        if user_type in [0, 1, 2] and sub_departments:
            log = await cls.model.get_or_none(
                id=log_id, department_id__in=sub_departments, is_del=False
            )
        else:
            log = await cls.model.get_or_none(
                id=log_id, operator_id=user_id, is_del=False
            )

        if log:
            log.is_del = True
            await log.save()
            return True, "删除成功"
        return False, "删除失败,操作日志不存在！"

    @classmethod
    async def batch_delete_operation_log(
        cls,
        log_ids: list,
        user_type: int = 3,
        user_id: Optional[str] = None,
        sub_departments: Optional[list] = None,
    ):
        if user_type in [0, 1, 2] and sub_departments:
            await cls.model.filter(
                id__in=list(set(log_ids)),
                department_id__in=sub_departments,
                is_del=False,
            ).update(is_del=True)
        else:
            await cls.model.filter(
                id__in=list(set(log_ids)),
                operator_id=user_id,
                is_del=False,
            ).update(is_del=True)
        return True, "删除成功"

    @classmethod
    async def get_personal_operation_log(
        cls,
        page: int,
        page_size: int,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ):
        filter_args = {"operator_id": user_id}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(
            **filter_args, operator__is_del=False, is_del=False
        ).count()
        result = (
            await cls.model.filter(**filter_args, operator__is_del=False, is_del=False)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by("-created_at")
            .values(
                id="id",
                created_at="created_at",
                updated_at="updated_at",
                operation_name="operation_name",
                operation_type="operation_type",
                request_path="request_path",
                request_method="request_method",
                request_params="request_params",
                response_result="response_result",
                host="host",
                location="location",
                browser="browser",
                os="os",
                user_agent="user_agent",
                operator_id="operator_id",
                operator_name="operator__username",
                operator_nickname="operator__nickname",
                department_id="department_id",
                department_name="department__name",
                status="status",
                cost_time="cost_time",
            )
        )

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await cls.model.filter(
            operator_id=user_id,
            is_del=False,
            operator__is_del=False,
            created_at__gte=today_start,
        ).count()

        return result, total, today_count
