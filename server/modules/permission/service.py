from core.common import BaseService
from modules.permission.model import PermissionType, SystemPermission
from modules.role.model import SystemRolePermission


class PermissionService(BaseService):
    model = SystemPermission
    VALUE_FIELDS = (
        "id",
        "created_at",
        "updated_at",
        "menu_type",
        "code",
        "parent_id",
        "component",
        "name",
        "title",
        "path",
        "icon",
        "showBadge",
        "showTextBadge",
        "isHide",
        "isHideTab",
        "link",
        "isIframe",
        "keepAlive",
        "isFirstLevel",
        "fixedTab",
        "activePath",
        "isFullPage",
        "order",
        "api_path",
        "api_method",
        "remark",
    )

    @classmethod
    def normalize_payload(cls, payload: dict) -> dict:
        menu_type = payload.get("menu_type")
        api_method = payload.get("api_method")
        if isinstance(api_method, str):
            api_method = [api_method]
        if isinstance(api_method, list):
            payload["api_method"] = [str(method).upper() for method in api_method if method]

        auth_title = payload.pop("authTitle", None)
        auth_mark = payload.pop("authMark", None)
        payload.pop("min_user_type", None)
        payload.pop("data_scope", None)

        if auth_title and not payload.get("title"):
            payload["title"] = auth_title

        if not payload.get("code"):
            if menu_type == PermissionType.BUTTON and auth_mark:
                payload["code"] = auth_mark
            elif menu_type == PermissionType.API and payload.get("api_path"):
                methods = ",".join(payload.get("api_method") or ["*"])
                payload["code"] = f"{methods}:{payload['api_path']}"
            elif payload.get("name"):
                payload["code"] = payload["name"]
        return payload

    @classmethod
    async def delete_permission_recursive(cls, permission_id: str):
        permission = await cls.model.get_or_none(id=permission_id, is_del=False)
        if not permission:
            return True

        await SystemRolePermission.filter(permission_id=permission.id, is_del=False).update(is_del=True)
        children = await cls.model.filter(parent_id=permission_id, is_del=False).all()
        for child in children:
            await cls.delete_permission_recursive(str(child.id))
        await cls.model.filter(id=permission_id, is_del=False).update(is_del=True)
        return True

    @classmethod
    async def create_permission(cls, payload: dict):
        return await cls.create(cls.normalize_payload(payload))

    @classmethod
    async def update_permission(cls, permission: SystemPermission, payload: dict):
        payload = cls.normalize_payload(payload)
        await permission.update_from_dict(payload)
        await permission.save()
        return permission

    @classmethod
    async def get_permission_tree(cls, user_type: int):
        permissions = await cls.model.filter(
            is_del=False,
        ).order_by("order", "created_at").values(*cls.VALUE_FIELDS)

        def build_tree(parent_id=None):
            tree = []
            for permission in permissions:
                permission_parent_id = permission.get("parent_id")
                if parent_id is None:
                    matched = permission_parent_id is None
                else:
                    matched = str(permission_parent_id) == str(parent_id)

                if matched:
                    item = dict(permission)
                    children = build_tree(permission.get("id"))
                    if children:
                        item["children"] = children
                    tree.append(item)
            return tree

        return build_tree(), permissions

    @classmethod
    async def get_menu_buttons(cls, parent_id: str, user_type: int):
        return await cls.model.filter(
            parent_id=parent_id,
            menu_type=PermissionType.BUTTON,
            is_del=False,
        ).order_by("order", "created_at").values(*cls.VALUE_FIELDS)
