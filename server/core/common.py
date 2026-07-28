# _*_ coding : UTF-8 _*_
# @Time : 2026/07/02 21:40
# @UpdateTime : 2026/07/02 21:40
# @Author : SonderZhong
# @File : common.py
# @Software : VSCode
# @Comment : 本程序用于


from io import BytesIO
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from pydantic import BaseModel, ConfigDict, Field
from tortoise import fields, models
from tortoise.transactions import in_transaction

from utils.excel import ExcelHandler


class DbBaseModel(models.Model):
    """数据库模型公共字段。"""

    id = fields.BigIntField(
        pk=True, autoincrement=True, description="主键", source_field="id"
    )
    is_del = fields.BooleanField(
        default=False, description="删除标识", source_field="is_del"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True, null=True, description="创建时间", source_field="created_at"
    )
    updated_at = fields.DatetimeField(
        auto_now=True, null=True, description="更新时间", source_field="updated_at"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = ("is_del",)


class BaseResponse(BaseModel):
    """统一响应模型。"""

    model_config = ConfigDict()

    code: int = Field(default=200, description="响应码")
    msg: str = Field(default="操作成功", description="响应信息")
    data: Any = Field(default=None, description="响应数据")
    success: bool = Field(default=True, description="是否成功")
    time: str = Field(default="", description="响应时间")


class ListQueryResult(BaseModel):
    """分页查询结果。"""

    model_config = ConfigDict()

    result: List[Any] = Field(default=[], description="列表数据")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    pageSize: int = Field(default=10, description="每页数量")


class DeleteListParams(BaseModel):
    """批量删除参数。"""

    model_config = ConfigDict()

    ids: List[Any] = Field(default=[], description="删除ID列表")


class DataBaseModel(BaseModel):
    """响应中的数据库公共字段。"""

    model_config = ConfigDict()

    id: Optional[Any] = Field(default=None, description="主键")
    is_del: bool = Field(default=False, description="删除标识")
    created_at: Optional[Any] = Field(default=None, description="创建时间")
    updated_at: Optional[Any] = Field(default=None, description="更新时间")


T = TypeVar("T", bound=DbBaseModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseService(Generic[T, CreateSchema, UpdateSchema]):
    """通用服务基类，提供 CRUD、批量操作和 Excel 导入导出。"""

    model: ClassVar[Type[T]]
    RESOURCE_TYPE: ClassVar[Optional[str]] = None
    RESOURCE_DISPLAY_NAME: ClassVar[Optional[str]] = None
    excel_columns: ClassVar[Dict[str, str]] = {}
    excel_sheet_name: ClassVar[str] = "数据"
    FIELD_METADATA: ClassVar[Dict[str, Dict[str, Any]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, "model", None) is not None and cls.RESOURCE_TYPE is None:
            table_name = getattr(cls.model._meta, "db_table", None)
            cls.RESOURCE_TYPE = table_name or cls.model.__name__

    @classmethod
    def _dump_schema(cls, data: Any, *, exclude_unset: bool = False) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=exclude_unset)
        if isinstance(data, dict):
            return dict(data)
        raise TypeError("data must be a pydantic model or dict")

    @classmethod
    async def create(
        cls, data: CreateSchema | Dict[str, Any], current_user_id: Optional[str] = None
    ) -> T:
        obj_data = cls._dump_schema(data)
        if current_user_id and hasattr(cls.model, "creator_id"):
            obj_data["creator_id"] = current_user_id
        return await cls.model.create(**obj_data)

    @classmethod
    async def get_by_id(cls, record_id: Any) -> Optional[T]:
        return await cls.model.filter(id=record_id, is_del=False).first()

    @classmethod
    async def get_list(
        cls,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
    ) -> Tuple[List[T], int]:
        query = cls.model.filter(is_del=False)
        if filters:
            query = query.filter(**filters)
        total = await query.count()
        query = query.order_by(*(order_by or ["-created_at"]))
        items = await query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @classmethod
    async def update(
        cls,
        record_id: Any,
        data: UpdateSchema | Dict[str, Any],
        current_user_id: Optional[str] = None,
    ) -> Optional[T]:
        db_obj = await cls.get_by_id(record_id)
        if not db_obj:
            return None
        update_data = cls._dump_schema(data, exclude_unset=True)
        if current_user_id and hasattr(db_obj, "modifier_id"):
            update_data["modifier_id"] = current_user_id
        await db_obj.update_from_dict(update_data).save()
        return db_obj

    @classmethod
    async def delete(cls, record_id: Any, hard: bool = False) -> bool:
        db_obj = await cls.get_by_id(record_id)
        if not db_obj:
            return False
        if hard:
            await db_obj.delete()
        else:
            db_obj.is_del = True
            await db_obj.save()
        return True

    @classmethod
    async def batch_delete(cls, ids: List[Any], hard: bool = False) -> Tuple[int, int]:
        if not ids:
            return 0, 0
        existing_ids = set(
            await cls.model.filter(id__in=ids, is_del=False).values_list(
                "id", flat=True
            )
        )
        if hard:
            await cls.model.filter(id__in=list(existing_ids)).delete()
        else:
            await cls.model.filter(id__in=list(existing_ids)).update(is_del=True)
        return len(existing_ids), len(ids) - len(existing_ids)

    @classmethod
    async def batch_update(
        cls,
        ids: List[Any],
        update_data: Dict[str, Any],
        current_user_id: Optional[str] = None,
    ) -> Tuple[int, int]:
        if not ids:
            return 0, 0
        if current_user_id and hasattr(cls.model, "modifier_id"):
            update_data["modifier_id"] = current_user_id
        existing_count = await cls.model.filter(id__in=ids, is_del=False).count()
        if existing_count:
            await cls.model.filter(id__in=ids, is_del=False).update(**update_data)
        return existing_count, len(ids) - existing_count

    @classmethod
    async def check_unique(
        cls, field: str, value: Any, exclude_id: Optional[Any] = None
    ) -> bool:
        query = cls.model.filter(**{field: value}, is_del=False)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return not await query.exists()

    @classmethod
    async def get_by_field(cls, field: str, value: Any) -> Optional[T]:
        return await cls.model.filter(**{field: value}, is_del=False).first()

    @classmethod
    async def exists(cls, filters: Dict[str, Any]) -> bool:
        return await cls.model.filter(**filters, is_del=False).exists()

    @classmethod
    async def get_all(
        cls,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[T]:
        query = cls.model.filter(is_del=False)
        if filters:
            query = query.filter(**filters)
        return await query.order_by(*(order_by or ["-created_at"])).all()

    @classmethod
    async def export_to_excel(
        cls,
        filters: Optional[Dict[str, Any]] = None,
        data_converter: Optional[Callable[[T], Dict[str, Any]]] = None,
    ) -> BytesIO:

        items = await cls.get_all(filters=filters, order_by=["-created_at"])
        data = (
            [data_converter(item) for item in items]
            if data_converter
            else [cls._to_excel_row(item) for item in items]
        )
        return ExcelHandler.export_to_excel(
            data, cls.excel_columns, cls.excel_sheet_name
        )

    @classmethod
    async def import_from_excel(
        cls,
        file_content: bytes,
        row_processor: Optional[
            Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
        ] = None,
        current_user_id: Optional[str] = None,
    ) -> Tuple[int, int, List[str]]:

        rows = ExcelHandler.import_from_excel(file_content, cls.excel_columns)
        success_count = 0
        fail_count = 0
        errors: List[str] = []
        async with in_transaction() as conn:
            for index, row in enumerate(rows, start=2):
                try:
                    data = row_processor(row) if row_processor else row
                    if data is None:
                        fail_count += 1
                        errors.append(f"第{index}行: 数据处理失败")
                        continue
                    if current_user_id and hasattr(cls.model, "creator_id"):
                        data["creator_id"] = current_user_id
                    await cls.model.create(**data, using_db=conn)
                    success_count += 1
                except Exception as exc:
                    fail_count += 1
                    errors.append(f"第{index}行: {exc}")
        return success_count, fail_count, errors

    @classmethod
    def get_import_template(cls) -> BytesIO:

        return ExcelHandler.generate_template(cls.excel_columns, cls.excel_sheet_name)

    @classmethod
    async def export_to_excel_by_ids(
        cls,
        ids: List[Any],
        data_converter: Optional[Callable[[T], Dict[str, Any]]] = None,
    ) -> BytesIO:

        items = (
            await cls.model.filter(id__in=ids, is_del=False)
            .order_by("-created_at")
            .all()
            if ids
            else []
        )
        data = (
            [data_converter(item) for item in items]
            if data_converter
            else [cls._to_excel_row(item) for item in items]
        )
        return ExcelHandler.export_to_excel(
            data, cls.excel_columns, cls.excel_sheet_name
        )

    @classmethod
    def _to_excel_row(cls, item: T) -> Dict[str, Any]:
        row: Dict[str, Any] = {}
        for field in cls.excel_columns.keys():
            value = getattr(item, field, "")
            if hasattr(value, "strftime"):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            row[field] = value
        return row
