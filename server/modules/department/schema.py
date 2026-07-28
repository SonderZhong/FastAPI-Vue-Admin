# _*_ coding : UTF-8 _*_

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.common import BaseResponse, DataBaseModel, ListQueryResult


class DepartmentInfo(DataBaseModel):
    """Department response model."""

    model_config = ConfigDict()

    tenant_id: Optional[str] = Field(default=None, description="Tenant ID")
    code: Optional[str] = Field(default=None, max_length=100, description="Department code")
    ancestor_path: Optional[str] = Field(default=None, description="Ancestor path")
    name: str = Field(..., max_length=50, description="Department name")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="Parent department ID")
    sort: int = Field(default=0, description="Sort order")
    phone: Optional[str] = Field(default=None, max_length=30, description="Department phone")
    principal: Optional[str] = Field(default=None, max_length=64, description="Department principal")
    email: Optional[str] = Field(default=None, max_length=128, description="Department email")
    status: int = Field(default=1, description="Status")
    remark: Optional[str] = Field(default=None, max_length=255, description="Remark")


class AddDepartmentParams(BaseModel):
    """Create department params."""

    model_config = ConfigDict()

    tenant_id: Optional[str] = Field(default=None, description="Tenant ID")
    name: str = Field(..., max_length=50, description="Department name")
    code: Optional[str] = Field(default=None, max_length=100, description="Department code")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="Parent department ID")
    sort: int = Field(default=0, description="Sort order")
    phone: Optional[str] = Field(default=None, max_length=30, description="Department phone")
    principal: Optional[str] = Field(default=None, max_length=64, description="Department principal")
    email: Optional[str] = Field(default=None, max_length=128, description="Department email")
    status: int = Field(default=1, description="Status")
    remark: Optional[str] = Field(default=None, max_length=255, description="Remark")

    @field_validator("tenant_id", "parent_id", mode="before")
    @classmethod
    def normalize_ids(cls, value):
        if value in (None, ""):
            return None
        return str(value)


class UpdateDepartmentParams(BaseModel):
    """Update department params."""

    model_config = ConfigDict()

    name: Optional[str] = Field(default=None, max_length=50, description="Department name")
    code: Optional[str] = Field(default=None, max_length=100, description="Department code")
    parent_id: Optional[str] = Field(default=None, max_length=50, description="Parent department ID")
    sort: Optional[int] = Field(default=None, description="Sort order")
    phone: Optional[str] = Field(default=None, max_length=30, description="Department phone")
    principal: Optional[str] = Field(default=None, max_length=64, description="Department principal")
    email: Optional[str] = Field(default=None, max_length=128, description="Department email")
    status: Optional[int] = Field(default=None, description="Status")
    remark: Optional[str] = Field(default=None, max_length=255, description="Remark")

    @field_validator("parent_id", mode="before")
    @classmethod
    def normalize_parent_id(cls, value):
        if value in (None, ""):
            return None
        return str(value)


class GetDepartmentListResult(ListQueryResult):
    """Department list result."""

    result: List[DepartmentInfo] = Field(default=[], description="Department list")


class GetDepartmentInfoResponse(BaseResponse):
    """Department info response."""

    data: DepartmentInfo = Field(default=None, description="Department info")


class GetDepartmentListResponse(BaseResponse):
    """Department list response."""

    data: GetDepartmentListResult = Field(default=None, description="Response data")
