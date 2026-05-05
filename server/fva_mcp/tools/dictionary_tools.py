# _*_ coding : UTF-8 _*_
# @Time : 2026/04/30
# @Author : sonder
# @File : dictionary_tools.py
# @Comment : 数据字典管理工具

import json
import uuid
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from tortoise import Tortoise

from models import SystemDictionary, SystemDictionaryItem


def get_db_url() -> str:
    """获取数据库连接 URL"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("配置文件不存在，请先完成系统初始化")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    db = config.get("database", {})
    engine = db.get("engine", "mysql")
    username = db.get("username", "root")
    password = db.get("password", "")
    host = db.get("host", "127.0.0.1")
    port = db.get("port", 3306)
    database = db.get("database", "digital-management")

    if engine == "mysql":
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"postgres://{username}:{password}@{host}:{port}/{database}"


@asynccontextmanager
async def get_db_connection():
    """获取数据库连接上下文"""
    if not Tortoise._inited:
        await Tortoise.init(
            db_url=get_db_url(),
            modules={
                "system": [
                    "models.dictionary",
                ]
            },
        )
    try:
        yield
    finally:
        pass


def register(mcp):
    """注册数据字典工具到 MCP 服务器"""

    # ==================== 数据字典管理工具 ====================

    @mcp.tool()
    async def create_dictionary(
        dict_name: str,
        dict_code: str,
        dict_type: str = "system",
        status: int = 1,
        sort: int = 0,
        remark: Optional[str] = None,
    ) -> str:
        """
        创建数据字典

        Args:
            dict_name: 字典名称
            dict_code: 字典编码（唯一标识）
            dict_type: 字典类型（system/paper/project等）
            status: 状态（1启用，0禁用）
            sort: 排序（数字越小越靠前）
            remark: 备注说明

        Returns:
            创建结果 JSON
        """
        async with get_db_connection():
            # 检查编码是否已存在
            existing = await SystemDictionary.filter(
                dict_code=dict_code, is_del=False
            ).first()
            if existing:
                return json.dumps(
                    {"success": False, "msg": f"字典编码 {dict_code} 已存在"},
                    ensure_ascii=False,
                )

            # 创建字典
            dictionary = await SystemDictionary.create(
                id=str(uuid.uuid4()),
                dict_name=dict_name,
                dict_code=dict_code,
                dict_type=dict_type,
                status=status,
                sort=sort,
                remark=remark,
            )

            return json.dumps(
                {
                    "success": True,
                    "msg": "数据字典创建成功",
                    "data": {
                        "id": str(dictionary.id),
                        "dict_name": dictionary.dict_name,
                        "dict_code": dictionary.dict_code,
                    },
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def list_dictionaries(
        page: int = 1, page_size: int = 50, dict_type: Optional[str] = None
    ) -> str:
        """
        查询数据字典列表

        Args:
            page: 页码，默认1
            page_size: 每页数量，默认50
            dict_type: 字典类型筛选

        Returns:
            字典列表 JSON
        """
        async with get_db_connection():
            filters = {"is_del": False}
            if dict_type:
                filters["dict_type"] = dict_type

            total = await SystemDictionary.filter(**filters).count()
            dictionaries = (
                await SystemDictionary.filter(**filters)
                .order_by("sort", "-created_at")
                .offset((page - 1) * page_size)
                .limit(page_size)
                .values(
                    "id",
                    "dict_name",
                    "dict_code",
                    "dict_type",
                    "status",
                    "sort",
                    "remark",
                    "created_at",
                )
            )

            return json.dumps(
                {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": dictionaries,
                },
                default=str,
                ensure_ascii=False,
            )

    @mcp.tool()
    async def get_dictionary(dict_id: str) -> str:
        """
        获取数据字典详情

        Args:
            dict_id: 字典ID

        Returns:
            字典详情 JSON
        """
        async with get_db_connection():
            dictionary = await SystemDictionary.filter(id=dict_id, is_del=False).first()

            if not dictionary:
                return json.dumps({"error": "数据字典不存在"}, ensure_ascii=False)

            return json.dumps(
                {
                    "id": str(dictionary.id),
                    "dict_name": dictionary.dict_name,
                    "dict_code": dictionary.dict_code,
                    "dict_type": dictionary.dict_type,
                    "status": dictionary.status,
                    "sort": dictionary.sort,
                    "remark": dictionary.remark,
                    "created_at": dictionary.created_at.isoformat()
                    if dictionary.created_at
                    else None,
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def get_dictionary_by_code(dict_code: str) -> str:
        """
        根据编码获取数据字典

        Args:
            dict_code: 字典编码

        Returns:
            字典详情 JSON
        """
        async with get_db_connection():
            dictionary = await SystemDictionary.filter(
                dict_code=dict_code, is_del=False
            ).first()

            if not dictionary:
                return json.dumps(
                    {"error": f"字典编码 {dict_code} 不存在"}, ensure_ascii=False
                )

            return json.dumps(
                {
                    "id": str(dictionary.id),
                    "dict_name": dictionary.dict_name,
                    "dict_code": dictionary.dict_code,
                    "dict_type": dictionary.dict_type,
                    "status": dictionary.status,
                    "sort": dictionary.sort,
                    "remark": dictionary.remark,
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def update_dictionary(
        dict_id: str,
        dict_name: Optional[str] = None,
        dict_type: Optional[str] = None,
        status: Optional[int] = None,
        sort: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> str:
        """
        更新数据字典

        Args:
            dict_id: 字典ID
            dict_name: 字典名称
            dict_type: 字典类型
            status: 状态（1启用，0禁用）
            sort: 排序
            remark: 备注

        Returns:
            操作结果
        """
        async with get_db_connection():
            dictionary = await SystemDictionary.filter(id=dict_id, is_del=False).first()
            if not dictionary:
                return json.dumps(
                    {"success": False, "msg": "数据字典不存在"}, ensure_ascii=False
                )

            if dict_name is not None:
                dictionary.dict_name = dict_name
            if dict_type is not None:
                dictionary.dict_type = dict_type
            if status is not None:
                dictionary.status = status
            if sort is not None:
                dictionary.sort = sort
            if remark is not None:
                dictionary.remark = remark

            await dictionary.save()

            return json.dumps(
                {"success": True, "msg": "数据字典更新成功"}, ensure_ascii=False
            )

    @mcp.tool()
    async def delete_dictionary(dict_id: str) -> str:
        """
        删除数据字典（软删除，同时删除所有字典项）

        Args:
            dict_id: 字典ID

        Returns:
            操作结果
        """
        async with get_db_connection():
            dictionary = await SystemDictionary.filter(id=dict_id, is_del=False).first()
            if not dictionary:
                return json.dumps(
                    {"success": False, "msg": "数据字典不存在"}, ensure_ascii=False
                )

            # 软删除字典
            dictionary.is_del = True
            await dictionary.save()

            # 软删除所有字典项
            await SystemDictionaryItem.filter(
                dictionary_id=dict_id, is_del=False
            ).update(is_del=True)

            return json.dumps(
                {"success": True, "msg": "数据字典删除成功"}, ensure_ascii=False
            )

    # ==================== 数据字典项管理工具 ====================

    @mcp.tool()
    async def create_dictionary_item(
        dictionary_id: str,
        label: str,
        value: str,
        status: int = 1,
        sort: int = 0,
        tag_color: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> str:
        """
        创建数据字典项

        Args:
            dictionary_id: 所属字典ID
            label: 字典项标签（显示文本）
            value: 字典项值（实际值）
            status: 状态（1启用，0禁用）
            sort: 排序（数字越小越靠前）
            tag_color: 标签颜色
            remark: 备注说明

        Returns:
            创建结果 JSON
        """
        async with get_db_connection():
            # 检查字典是否存在
            dictionary = await SystemDictionary.filter(
                id=dictionary_id, is_del=False
            ).first()
            if not dictionary:
                return json.dumps(
                    {"success": False, "msg": "所属字典不存在"}, ensure_ascii=False
                )

            # 创建字典项
            item = await SystemDictionaryItem.create(
                id=str(uuid.uuid4()),
                dictionary_id=dictionary,
                label=label,
                value=value,
                status=status,
                sort=sort,
                tag_color=tag_color,
                remark=remark,
            )

            return json.dumps(
                {
                    "success": True,
                    "msg": "字典项创建成功",
                    "data": {
                        "id": str(item.id),
                        "label": item.label,
                        "value": item.value,
                    },
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def batch_create_dictionary_items(dictionary_id: str, items: str) -> str:
        """
        批量创建数据字典项

        Args:
            dictionary_id: 所属字典ID
            items: JSON格式的字典项列表，格式：[{"label": "标签", "value": "值", "sort": 1}, ...]

        Returns:
            创建结果 JSON
        """
        async with get_db_connection():
            # 检查字典是否存在
            dictionary = await SystemDictionary.filter(
                id=dictionary_id, is_del=False
            ).first()
            if not dictionary:
                return json.dumps(
                    {"success": False, "msg": "所属字典不存在"}, ensure_ascii=False
                )

            # 解析字典项列表
            try:
                items_list = json.loads(items)
            except json.JSONDecodeError:
                return json.dumps(
                    {"success": False, "msg": "items 参数格式错误，应为 JSON 数组"},
                    ensure_ascii=False,
                )

            # 批量创建
            created_count = 0
            for item_data in items_list:
                await SystemDictionaryItem.create(
                    id=str(uuid.uuid4()),
                    dictionary_id=dictionary,
                    label=item_data.get("label"),
                    value=item_data.get("value"),
                    status=item_data.get("status", 1),
                    sort=item_data.get("sort", 0),
                    tag_color=item_data.get("tag_color"),
                    remark=item_data.get("remark"),
                )
                created_count += 1

            return json.dumps(
                {"success": True, "msg": f"成功创建 {created_count} 个字典项"},
                ensure_ascii=False,
            )

    @mcp.tool()
    async def list_dictionary_items(
        dictionary_id: str, status: Optional[int] = None
    ) -> str:
        """
        查询数据字典项列表

        Args:
            dictionary_id: 所属字典ID
            status: 状态筛选（1启用，0禁用）

        Returns:
            字典项列表 JSON
        """
        async with get_db_connection():
            filters = {"dictionary_id": dictionary_id, "is_del": False}
            if status is not None:
                filters["status"] = status

            items = (
                await SystemDictionaryItem.filter(**filters)
                .order_by("sort", "-created_at")
                .values(
                    "id",
                    "label",
                    "value",
                    "status",
                    "sort",
                    "tag_color",
                    "remark",
                    "created_at",
                )
            )

            return json.dumps(
                {"total": len(items), "data": items}, default=str, ensure_ascii=False
            )

    @mcp.tool()
    async def list_dictionary_items_by_code(
        dict_code: str, status: Optional[int] = 1
    ) -> str:
        """
        根据字典编码查询字典项列表（常用接口）

        Args:
            dict_code: 字典编码
            status: 状态筛选（1启用，0禁用，None查询全部）

        Returns:
            字典项列表 JSON
        """
        async with get_db_connection():
            # 先查询字典
            dictionary = await SystemDictionary.filter(
                dict_code=dict_code, is_del=False
            ).first()
            if not dictionary:
                return json.dumps(
                    {"error": f"字典编码 {dict_code} 不存在"}, ensure_ascii=False
                )

            # 查询字典项
            filters = {"dictionary_id": dictionary.id, "is_del": False}
            if status is not None:
                filters["status"] = status

            items = (
                await SystemDictionaryItem.filter(**filters)
                .order_by("sort", "-created_at")
                .values("id", "label", "value", "status", "sort", "tag_color", "remark")
            )

            return json.dumps(
                {
                    "dict_code": dict_code,
                    "dict_name": dictionary.dict_name,
                    "total": len(items),
                    "data": items,
                },
                default=str,
                ensure_ascii=False,
            )

    @mcp.tool()
    async def get_dictionary_item(item_id: str) -> str:
        """
        获取数据字典项详情

        Args:
            item_id: 字典项ID

        Returns:
            字典项详情 JSON
        """
        async with get_db_connection():
            item = await SystemDictionaryItem.filter(id=item_id, is_del=False).first()

            if not item:
                return json.dumps({"error": "字典项不存在"}, ensure_ascii=False)

            return json.dumps(
                {
                    "id": str(item.id),
                    "dictionary_id": str(item.dictionary_id_id),
                    "label": item.label,
                    "value": item.value,
                    "status": item.status,
                    "sort": item.sort,
                    "tag_color": item.tag_color,
                    "remark": item.remark,
                    "created_at": item.created_at.isoformat()
                    if item.created_at
                    else None,
                },
                ensure_ascii=False,
            )

    @mcp.tool()
    async def update_dictionary_item(
        item_id: str,
        label: Optional[str] = None,
        value: Optional[str] = None,
        status: Optional[int] = None,
        sort: Optional[int] = None,
        tag_color: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> str:
        """
        更新数据字典项

        Args:
            item_id: 字典项ID
            label: 字典项标签
            value: 字典项值
            status: 状态（1启用，0禁用）
            sort: 排序
            tag_color: 标签颜色
            remark: 备注

        Returns:
            操作结果
        """
        async with get_db_connection():
            item = await SystemDictionaryItem.filter(id=item_id, is_del=False).first()
            if not item:
                return json.dumps(
                    {"success": False, "msg": "字典项不存在"}, ensure_ascii=False
                )

            if label is not None:
                item.label = label
            if value is not None:
                item.value = value
            if status is not None:
                item.status = status
            if sort is not None:
                item.sort = sort
            if tag_color is not None:
                item.tag_color = tag_color
            if remark is not None:
                item.remark = remark

            await item.save()

            return json.dumps(
                {"success": True, "msg": "字典项更新成功"}, ensure_ascii=False
            )

    @mcp.tool()
    async def delete_dictionary_item(item_id: str) -> str:
        """
        删除数据字典项（软删除）

        Args:
            item_id: 字典项ID

        Returns:
            操作结果
        """
        async with get_db_connection():
            item = await SystemDictionaryItem.filter(id=item_id, is_del=False).first()
            if not item:
                return json.dumps(
                    {"success": False, "msg": "字典项不存在"}, ensure_ascii=False
                )

            item.is_del = True
            await item.save()

            return json.dumps(
                {"success": True, "msg": "字典项删除成功"}, ensure_ascii=False
            )

    # ==================== 批量操作工具 ====================

    @mcp.tool()
    async def create_dictionary_with_items(
        dict_name: str,
        dict_code: str,
        items: str,
        dict_type: str = "system",
        status: int = 1,
        sort: int = 0,
        remark: Optional[str] = None,
    ) -> str:
        """
        创建数据字典并批量添加字典项（一步完成）

        Args:
            dict_name: 字典名称
            dict_code: 字典编码
            items: JSON格式的字典项列表，格式：[{"label": "标签", "value": "值", "sort": 1}, ...]
            dict_type: 字典类型
            status: 状态（1启用，0禁用）
            sort: 排序
            remark: 备注

        Returns:
            创建结果 JSON
        """
        async with get_db_connection():
            # 检查编码是否已存在
            existing = await SystemDictionary.filter(
                dict_code=dict_code, is_del=False
            ).first()
            if existing:
                return json.dumps(
                    {"success": False, "msg": f"字典编码 {dict_code} 已存在"},
                    ensure_ascii=False,
                )

            # 创建字典
            dictionary = await SystemDictionary.create(
                id=str(uuid.uuid4()),
                dict_name=dict_name,
                dict_code=dict_code,
                dict_type=dict_type,
                status=status,
                sort=sort,
                remark=remark,
            )

            # 解析并创建字典项
            try:
                items_list = json.loads(items)
            except json.JSONDecodeError:
                return json.dumps(
                    {"success": False, "msg": "items 参数格式错误，应为 JSON 数组"},
                    ensure_ascii=False,
                )

            created_count = 0
            for item_data in items_list:
                await SystemDictionaryItem.create(
                    id=str(uuid.uuid4()),
                    dictionary_id=dictionary,
                    label=item_data.get("label"),
                    value=item_data.get("value"),
                    status=item_data.get("status", 1),
                    sort=item_data.get("sort", 0),
                    tag_color=item_data.get("tag_color"),
                    remark=item_data.get("remark"),
                )
                created_count += 1

            return json.dumps(
                {
                    "success": True,
                    "msg": f"数据字典创建成功，共添加 {created_count} 个字典项",
                    "data": {
                        "id": str(dictionary.id),
                        "dict_name": dictionary.dict_name,
                        "dict_code": dictionary.dict_code,
                        "items_count": created_count,
                    },
                },
                ensure_ascii=False,
            )
