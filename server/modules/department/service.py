from typing import Optional

from core.common import BaseService
from modules.department.model import SystemDepartment


class DepartmentService(BaseService):
    model = SystemDepartment

    @classmethod
    async def build_ancestor_path(cls, parent_id: Optional[str], current_id: str) -> str:
        if not parent_id:
            return f"/{current_id}/"

        parent = await cls.model.get_or_none(id=parent_id, is_del=False)
        if not parent or not parent.ancestor_path:
            return f"/{parent_id}/{current_id}/"
        return f"{parent.ancestor_path}{current_id}/"

    @classmethod
    async def refresh_children_ancestor_path(cls, parent_id: str):
        children = await cls.model.filter(parent_id=parent_id, is_del=False).all()
        for child in children:
            child.ancestor_path = await cls.build_ancestor_path(parent_id, str(child.id))
            await child.save()
            await cls.refresh_children_ancestor_path(str(child.id))

    @classmethod
    async def create_department(cls, payload: dict):
        department = await cls.create(payload)
        department.ancestor_path = await cls.build_ancestor_path(payload.get("parent_id"), str(department.id))
        await department.save()
        return department

    @classmethod
    async def delete_department_recursive(cls, department_id: str):
        await cls.model.filter(id=department_id, is_del=False).update(is_del=True)
        children = await cls.model.filter(parent_id=department_id, is_del=False).all()
        for child in children:
            await cls.delete_department_recursive(str(child.id))
        return True

    @classmethod
    async def update_department_with_ancestor(cls, department: SystemDepartment, payload: dict):
        old_parent_id = str(department.parent_id) if department.parent_id else None
        new_parent_id = str(payload.get("parent_id")) if payload.get("parent_id") else None

        if new_parent_id and new_parent_id == str(department.id):
            raise ValueError("部门不能设置自己为上级部门")

        if new_parent_id and new_parent_id != old_parent_id:
            parent = await cls.model.get_or_none(id=new_parent_id, is_del=False)
            if not parent:
                raise ValueError("上级部门不存在")
            if parent.ancestor_path and f"/{department.id}/" in parent.ancestor_path:
                raise ValueError("不能移动部门到自己的下级部门")

        await department.update_from_dict(payload)
        if old_parent_id != new_parent_id:
            department.ancestor_path = await cls.build_ancestor_path(new_parent_id, str(department.id))
        await department.save()
        if old_parent_id != new_parent_id:
            await cls.refresh_children_ancestor_path(str(department.id))
        return department
