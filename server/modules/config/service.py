# _*_ coding : UTF-8 _*_

from typing import Any, Dict, List, Optional, Tuple

from core.common import BaseService
from modules.config.model import SystemConfig, ConfigGroup


class ConfigService(BaseService):
    model = SystemConfig
    excel_sheet_name = "系统配置"
    excel_columns = {
        "name": "配置名称",
        "key": "配置键名",
        "value": "配置值",
        "group": "配置分组",
        "type": "系统内置",
        "remark": "备注",
    }

    @classmethod
    async def create_config(cls, params: dict) -> Tuple[bool, str]:
        if await cls.model.get_or_none(key=params.get("key"), is_del=False):
            return False, "配置键名已存在"

        await cls.model.create(
            name=params["name"],
            key=params["key"],
            value=params["value"],
            group=params.get("group", ConfigGroup.SYSTEM),
            remark=params.get("remark"),
            type=params.get("type", False),
        )
        return True, "新增成功"

    @classmethod
    async def update_config(cls, config_id: str, params: dict) -> Tuple[bool, str]:
        config = await cls.model.get_or_none(id=config_id, is_del=False)
        if not config:
            return False, "配置不存在"

        config.name = params.get("name", config.name)
        config.key = params.get("key", config.key)
        config.value = params.get("value", config.value)
        config.remark = params.get("remark", config.remark)
        config.type = params.get("type", config.type)
        if params.get("group"):
            config.group = params["group"]
        await config.save()
        return True, "修改成功"

    @classmethod
    async def batch_delete_config(cls, ids: List[str]):
        await cls.model.filter(id__in=list(set(ids)), is_del=False).update(is_del=True)

    @classmethod
    async def get_config_info(cls, config_id: str) -> Optional[dict]:
        config = await cls.model.get_or_none(id=config_id, is_del=False)
        if not config:
            return None
        return {
            "id": config.id,
            "name": config.name,
            "key": config.key,
            "value": config.value,
            "remark": config.remark,
            "type": config.type,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    @classmethod
    async def get_config_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
    ):
        filter_args = {}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args, is_del=False).count()
        data = await cls.model.filter(**filter_args, is_del=False).offset(
            (page - 1) * page_size
        ).limit(page_size).values(
            id="id",
            name="name",
            key="key",
            value="value",
            group="group",
            remark="remark",
            type="type",
            created_at="created_at",
            updated_at="updated_at",
        )
        return data, total

    @classmethod
    async def batch_update_group_configs(cls, group: str, configs: List[dict], dynamic_config):
        for cfg in configs:
            key = cfg.get("key")
            value = cfg.get("value")
            if key and value is not None:
                await dynamic_config.set(key, str(value))
