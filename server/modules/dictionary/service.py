# _*_ coding : UTF-8 _*_

import json
from typing import Any, Dict, List, Optional, Tuple

from core.common import BaseService
from modules.dictionary.item_model import SystemDictionaryItem
from modules.dictionary.model import SystemDictionary
from utils.get_redis import RedisKeyConfig


DEFAULT_DICTIONARIES: list[dict[str, Any]] = [
    {
        "dict_name": "通用状态",
        "dict_code": "common_status",
        "status": 1,
        "sort": 1,
        "remark": "通用启用/禁用状态",
        "items": [
            {"label": "启用", "value": "1", "status": 1, "sort": 1, "tag_color": "#67C23A"},
            {"label": "禁用", "value": "0", "status": 1, "sort": 2, "tag_color": "#909399"},
        ],
    },
    {
        "dict_name": "用户性别",
        "dict_code": "user_gender",
        "status": 1,
        "sort": 2,
        "remark": "用户性别选项",
        "items": [
            {"label": "女", "value": "0", "status": 1, "sort": 1, "tag_color": "#F56C6C"},
            {"label": "男", "value": "1", "status": 1, "sort": 2, "tag_color": "#409EFF"},
            {"label": "未知", "value": "2", "status": 1, "sort": 3, "tag_color": "#909399"},
        ],
    },
    {
        "dict_name": "通知类型",
        "dict_code": "notification_type",
        "status": 1,
        "sort": 3,
        "remark": "系统通知类型",
        "items": [
            {"label": "登录通知", "value": "0", "status": 1, "sort": 1, "tag_color": "#909399"},
            {"label": "全局公告", "value": "1", "status": 1, "sort": 2, "tag_color": "#E6A23C"},
            {"label": "系统消息", "value": "2", "status": 1, "sort": 3, "tag_color": "#67C23A"},
        ],
    },
    {
        "dict_name": "通知状态",
        "dict_code": "notification_status",
        "status": 1,
        "sort": 4,
        "remark": "通知发布状态",
        "items": [
            {"label": "草稿", "value": "0", "status": 1, "sort": 1, "tag_color": "#909399"},
            {"label": "已发布", "value": "1", "status": 1, "sort": 2, "tag_color": "#67C23A"},
            {"label": "已撤回", "value": "2", "status": 1, "sort": 3, "tag_color": "#E6A23C"},
        ],
    },
    {
        "dict_name": "通知范围",
        "dict_code": "notification_scope",
        "status": 1,
        "sort": 5,
        "remark": "通知发送范围",
        "items": [
            {"label": "全部用户", "value": "0", "status": 1, "sort": 1, "tag_color": "#409EFF"},
            {"label": "指定部门", "value": "1", "status": 1, "sort": 2, "tag_color": "#E6A23C"},
            {"label": "指定用户", "value": "2", "status": 1, "sort": 3, "tag_color": "#67C23A"},
        ],
    },
    {
        "dict_name": "通知优先级",
        "dict_code": "notification_priority",
        "status": 1,
        "sort": 6,
        "remark": "通知优先级",
        "items": [
            {"label": "普通", "value": "0", "status": 1, "sort": 1, "tag_color": "#909399"},
            {"label": "重要", "value": "1", "status": 1, "sort": 2, "tag_color": "#E6A23C"},
            {"label": "紧急", "value": "2", "status": 1, "sort": 3, "tag_color": "#F56C6C"},
        ],
    },
]


class DictionaryService(BaseService):
    model = SystemDictionary
    excel_sheet_name = "数据字典"
    excel_columns = {
        "dict_name": "字典名称",
        "dict_code": "字典编码",
        "status": "状态",
        "sort": "排序",
        "remark": "备注",
    }

    @staticmethod
    async def get_from_cache(redis, dict_id: str) -> Optional[dict]:
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}"
        cached_data = await redis.get(cache_key)
        return json.loads(cached_data) if cached_data else None

    @staticmethod
    async def set_to_cache(redis, dict_id: str, data: dict, expire: int = 3600):
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}"
        await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)

    @staticmethod
    async def delete_cache(redis, dict_id: str):
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:{dict_id}"
        await redis.delete(cache_key)

    @staticmethod
    async def get_list_from_cache(redis, cache_key: str) -> Optional[dict]:
        cached_data = await redis.get(cache_key)
        return json.loads(cached_data) if cached_data else None

    @staticmethod
    async def set_list_to_cache(redis, cache_key: str, data: dict, expire: int = 90):
        await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)

    @staticmethod
    async def clear_list_cache(redis):
        pattern = f"{RedisKeyConfig.SYSTEMDICTIONARY_INFO.key}:list:*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)

    @staticmethod
    def _to_dict_data(record: SystemDictionary) -> dict:
        return {
            "id": str(record.id),
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "dict_name": record.dict_name,
            "dict_code": record.dict_code,
            "status": record.status,
            "sort": record.sort,
            "remark": record.remark,
        }

    @classmethod
    async def ensure_default_dictionaries(cls, redis=None) -> None:
        exists = await cls.model.filter(is_del=False).exists()
        if exists:
            return

        for dictionary in DEFAULT_DICTIONARIES:
            created = await cls.model.create(
                dict_name=dictionary["dict_name"],
                dict_code=dictionary["dict_code"],
                status=dictionary.get("status", 1),
                sort=dictionary.get("sort", 0),
                remark=dictionary.get("remark"),
            )
            for item in dictionary.get("items", []):
                await SystemDictionaryItem.create(
                    dictionary_id=created,
                    label=item["label"],
                    value=str(item["value"]),
                    status=item.get("status", 1),
                    sort=item.get("sort", 0),
                    tag_color=item.get("tag_color"),
                    remark=item.get("remark"),
                )

        if redis:
            await cls.clear_list_cache(redis)

    @classmethod
    async def create_dictionary(cls, params: dict, redis) -> Tuple[bool, str]:
        existing = await cls.model.get_or_none(dict_code=params.get("dict_code"), is_del=False)
        if existing:
            return False, "添加失败，字典编码已存在！"

        await cls.model.create(**params)
        await cls.clear_list_cache(redis)
        return True, "添加成功！"

    @classmethod
    async def delete_dictionary(cls, dict_id: str, redis) -> Tuple[bool, str]:
        record = await cls.model.get_or_none(id=dict_id, is_del=False)
        if not record:
            return False, "删除失败，数据字典不存在！"

        record.is_del = True
        await record.save()
        await SystemDictionaryItem.filter(dictionary_id=dict_id, is_del=False).update(is_del=True)

        await cls.delete_cache(redis, dict_id)
        await DictionaryItemService.clear_items_cache(redis, dict_id)
        await cls.clear_list_cache(redis)
        return True, "删除成功！"

    @classmethod
    async def batch_delete_dictionary(cls, ids: List[str], redis) -> Tuple[int, str]:
        deleted_count = 0
        for record_id in set(ids):
            record = await cls.model.get_or_none(id=record_id, is_del=False)
            if record:
                record.is_del = True
                await record.save()
                await SystemDictionaryItem.filter(dictionary_id=record_id, is_del=False).update(is_del=True)
                await cls.delete_cache(redis, record_id)
                await DictionaryItemService.clear_items_cache(redis, record_id)
                deleted_count += 1

        await cls.clear_list_cache(redis)
        return deleted_count, f"删除成功，共删除 {deleted_count} 个数据字典！"

    @classmethod
    async def update_dictionary(cls, dict_id: str, update_data: dict, redis) -> Tuple[bool, str]:
        record = await cls.model.get_or_none(id=dict_id, is_del=False)
        if not record:
            return False, "更新失败，数据字典不存在！"

        for field, value in update_data.items():
            setattr(record, field, value)
        await record.save()

        await cls.delete_cache(redis, dict_id)
        await cls.clear_list_cache(redis)
        return True, "更新成功！"

    @classmethod
    async def get_dictionary_info(cls, dict_id: str, redis) -> Optional[dict]:
        cached_data = await cls.get_from_cache(redis, dict_id)
        if cached_data:
            return cached_data

        record = await cls.model.get_or_none(id=dict_id, is_del=False)
        if not record:
            return None

        data = cls._to_dict_data(record)
        await cls.set_to_cache(redis, dict_id, data)
        return data

    @classmethod
    async def get_dictionary_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
        redis=None,
    ) -> Tuple[List[dict], int]:
        await cls.ensure_default_dictionaries(redis=redis)
        filter_args = {"is_del": False}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args).count()
        records = (
            await cls.model.filter(**filter_args)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [cls._to_dict_data(record) for record in records], total

    @classmethod
    async def get_dictionary_by_code(cls, code: str, redis) -> Optional[List[dict]]:
        await cls.ensure_default_dictionaries(redis=redis)
        dictionary = await cls.model.get_or_none(dict_code=code, is_del=False)
        if not dictionary:
            return None
        return await DictionaryItemService.get_items_by_dict_id(str(dictionary.id), redis)


class DictionaryItemService(BaseService):
    model = SystemDictionaryItem
    excel_sheet_name = "数据字典项"
    excel_columns = {
        "label": "字典项标签",
        "value": "字典项值",
        "status": "状态",
        "sort": "排序",
        "tag_color": "标签颜色",
        "remark": "备注",
    }

    @staticmethod
    async def get_items_from_cache(redis, dict_id: str) -> Optional[list]:
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}"
        cached_data = await redis.get(cache_key)
        return json.loads(cached_data) if cached_data else None

    @staticmethod
    async def set_items_to_cache(redis, dict_id: str, data: list, expire: int = 3600):
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}"
        await redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=expire)

    @staticmethod
    async def clear_items_cache(redis, dict_id: str):
        cache_key = f"{RedisKeyConfig.SYSTEMDICTIONARYITEM_INFO.key}:dict:{dict_id}"
        await redis.delete(cache_key)

    @staticmethod
    def _to_item_data(record: SystemDictionaryItem) -> dict:
        return {
            "id": str(record.id),
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "dictionary_id": str(record.dictionary_id_id) if record.dictionary_id_id else None,
            "label": record.label,
            "value": record.value,
            "status": record.status,
            "sort": record.sort,
            "tag_color": record.tag_color,
            "remark": record.remark,
        }

    @staticmethod
    def _to_item_simple(record: SystemDictionaryItem) -> dict:
        return {
            "id": str(record.id),
            "label": record.label,
            "value": record.value,
            "status": record.status,
            "sort": record.sort,
            "tag_color": record.tag_color,
            "remark": record.remark,
        }

    @classmethod
    async def create_item(cls, params: dict, redis) -> Tuple[bool, str]:
        dictionary = await SystemDictionary.get_or_none(id=params.get("dictionary_id"), is_del=False)
        if not dictionary:
            return False, "添加失败，所属字典不存在！"

        data = dict(params)
        data["dictionary_id"] = dictionary
        await cls.model.create(**data)
        await cls.clear_items_cache(redis, str(dictionary.id))
        return True, "添加成功！"

    @classmethod
    async def delete_item(cls, item_id: str, redis) -> Tuple[bool, str]:
        record = await cls.model.get_or_none(id=item_id, is_del=False)
        if not record:
            return False, "删除失败，数据字典项不存在！"

        dict_id = str(record.dictionary_id_id)
        record.is_del = True
        await record.save()
        await cls.clear_items_cache(redis, dict_id)
        return True, "删除成功！"

    @classmethod
    async def batch_delete_item(cls, ids: List[str], redis) -> Tuple[int, str]:
        deleted_count = 0
        dict_ids = set()
        for record_id in set(ids):
            record = await cls.model.get_or_none(id=record_id, is_del=False)
            if record:
                dict_ids.add(str(record.dictionary_id_id))
                record.is_del = True
                await record.save()
                deleted_count += 1

        for dict_id in dict_ids:
            await cls.clear_items_cache(redis, dict_id)
        return deleted_count, f"删除成功，共删除 {deleted_count} 个数据字典项！"

    @classmethod
    async def update_item(cls, item_id: str, update_data: dict, redis) -> Tuple[bool, str]:
        record = await cls.model.get_or_none(id=item_id, is_del=False)
        if not record:
            return False, "更新失败，数据字典项不存在！"

        dict_id = str(record.dictionary_id_id)
        if "dictionary_id" in update_data and update_data["dictionary_id"]:
            dictionary = await SystemDictionary.get_or_none(id=update_data["dictionary_id"], is_del=False)
            if not dictionary:
                return False, "更新失败，所属字典不存在！"
            update_data["dictionary_id"] = dictionary
            dict_id = str(dictionary.id)

        for field, value in update_data.items():
            setattr(record, field, value)
        await record.save()

        await cls.clear_items_cache(redis, dict_id)
        return True, "更新成功！"

    @classmethod
    async def get_item_info(cls, item_id: str) -> Optional[dict]:
        record = await cls.model.get_or_none(id=item_id, is_del=False).prefetch_related("dictionary_id")
        if not record:
            return None
        return cls._to_item_data(record)

    @classmethod
    async def get_item_list(
        cls,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[dict], int]:
        filter_args = {"is_del": False}
        if filters:
            filter_args.update(filters)

        total = await cls.model.filter(**filter_args).count()
        records = (
            await cls.model.filter(**filter_args)
            .prefetch_related("dictionary_id")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [cls._to_item_data(record) for record in records], total

    @classmethod
    async def get_items_by_dict_id(cls, dict_id: str, redis) -> Optional[List[dict]]:
        cached_items = await cls.get_items_from_cache(redis, dict_id)
        if cached_items:
            return cached_items

        items = (
            await cls.model.filter(dictionary_id=dict_id, is_del=False, status=1)
            .order_by("sort", "-created_at")
            .all()
        )
        result = [cls._to_item_simple(item) for item in items]
        await cls.set_items_to_cache(redis, dict_id, result)
        return result
