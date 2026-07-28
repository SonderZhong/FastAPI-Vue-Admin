# _*_ coding : UTF-8 _*_

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.common import BaseResponse, DataBaseModel, ListQueryResult


class PermissionInfo(DataBaseModel):
    """Permission response model."""

    model_config = ConfigDict(populate_by_name=True)

    menu_type: Optional[int] = Field(None, description="0 menu, 1 button, 2 api")
    code: Optional[str] = Field(None, description="Permission code")
    parent_id: Optional[str] = Field(None, description="Parent permission ID")
    name: Optional[str] = Field(None, description="Permission name")
    path: Optional[str] = Field(None, description="Route or permission path")
    title: Optional[str] = Field(None, description="Menu title")
    icon: Optional[str] = Field(None, description="Icon")
    component: Optional[str] = Field(None, description="Component path")
    showBadge: Optional[bool] = Field(None, description="Show badge")
    showTextBadge: Optional[str] = Field(None, description="Badge text")
    isHide: Optional[bool] = Field(None, description="Hide menu")
    isHideTab: Optional[bool] = Field(None, description="Hide tab")
    link: Optional[str] = Field(None, description="External link")
    isIframe: Optional[bool] = Field(None, description="Iframe")
    keepAlive: Optional[bool] = Field(None, description="Keep alive")
    isFirstLevel: Optional[bool] = Field(None, description="First level route")
    fixedTab: Optional[bool] = Field(None, description="Fixed tab")
    activePath: Optional[str] = Field(None, description="Active path")
    isFullPage: Optional[bool] = Field(None, description="Full page")
    order: Optional[int] = Field(999, description="Sort order")
    authTitle: Optional[str] = Field(None, description="Button title")
    authMark: Optional[str] = Field(None, description="Legacy button mark")
    min_user_type: Optional[int] = Field(3, description="Minimum user type")
    api_path: Optional[str] = Field(None, description="API path")
    api_method: Optional[List[str]] = Field(None, description="HTTP methods")
    data_scope: Optional[int] = Field(None, description="Legacy data scope")
    remark: Optional[str] = Field(None, description="Remark")


class GetPermissionInfoResponse(BaseResponse):
    """Permission info response."""

    data: PermissionInfo = Field(None, description="Permission info")


class AddPermissionParams(BaseModel):
    """Create permission params."""

    model_config = ConfigDict()

    menu_type: Optional[int] = Field(None, description="0 menu, 1 button, 2 api")
    code: Optional[str] = Field(None, description="Permission code")
    parent_id: Optional[str] = Field(None, description="Parent permission ID")
    name: Optional[str] = Field(None, description="Permission name")
    path: Optional[str] = Field(None, description="Route or permission path")
    title: Optional[str] = Field(None, description="Menu title")
    icon: Optional[str] = Field(None, description="Icon")
    component: Optional[str] = Field(None, description="Component path")
    showBadge: Optional[bool] = Field(None, description="Show badge")
    showTextBadge: Optional[str] = Field(None, description="Badge text")
    isHide: Optional[bool] = Field(None, description="Hide menu")
    isHideTab: Optional[bool] = Field(None, description="Hide tab")
    link: Optional[str] = Field(None, description="External link")
    isIframe: Optional[bool] = Field(None, description="Iframe")
    keepAlive: Optional[bool] = Field(None, description="Keep alive")
    isFirstLevel: Optional[bool] = Field(None, description="First level route")
    fixedTab: Optional[bool] = Field(None, description="Fixed tab")
    activePath: Optional[str] = Field(None, description="Active path")
    isFullPage: Optional[bool] = Field(None, description="Full page")
    order: Optional[int] = Field(999, description="Sort order")
    authTitle: Optional[str] = Field(None, description="Button title")
    authMark: Optional[str] = Field(None, description="Legacy button mark")
    min_user_type: Optional[int] = Field(3, ge=0, le=3, description="Minimum user type")
    api_path: Optional[str] = Field(None, description="API path")
    api_method: Optional[List[str]] = Field(None, description="HTTP methods")
    data_scope: Optional[int] = Field(None, ge=1, le=4, description="Legacy data scope")
    remark: Optional[str] = Field(None, description="Remark")


class UpdatePermissionParams(AddPermissionParams):
    """Update permission params."""


class GetPermissionListResult(ListQueryResult):
    """Permission list result."""

    result: List[PermissionInfo] = Field(default=[], description="Permission list")


class GetPermissionListResponse(BaseResponse):
    """Permission list response."""

    data: GetPermissionListResult = Field(default=None, description="Response data")
