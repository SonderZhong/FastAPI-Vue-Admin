# _*_ coding : UTF-8 _*_
# @Time : 2025/12/26
# @Author : sonder
# @File : casbin.py
# @Comment : Casbin 权限管理工具 - 完整 RBAC 权限控制（菜单/按钮/接口 + 数据权限）

import os
import tempfile
import casbin
from typing import List, Optional, Set, Dict
from enum import IntEnum

from redis.asyncio import Redis as AsyncRedis

from models import SystemConfig, SystemDepartment, SystemUser
from models.casbin import CasbinRule
from utils.get_redis import RedisKeyConfig
from utils.log import logger


class UserType(IntEnum):
    """用户类型枚举"""
    SUPER_ADMIN = 0      # 超级管理员 - 可查看所有数据
    ADMIN = 1            # 管理员 - 可管理多个部门
    DEPT_ADMIN = 2       # 部门管理员 - 可查看本部门及下属部门数据
    NORMAL_USER = 3      # 普通用户 - 只能查看自己的数据


class DataScope(IntEnum):
    """数据权限范围"""
    ALL = 1              # 全部数据
    DEPT_AND_CHILD = 2   # 本部门及下属部门
    DEPT_ONLY = 3        # 仅本部门
    SELF_ONLY = 4        # 仅本人


class PermissionType(IntEnum):
    """权限类型"""
    MENU = 0             # 菜单权限
    BUTTON = 1           # 按钮权限
    API = 2              # 接口权限


# 默认 RBAC 模型配置
# p = sub(角色), obj(权限ID或API路径), act(权限类型或HTTP方法), eft(效果，可选)
DEFAULT_CASBIN_MODEL = """[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && (r.obj == p.obj || keyMatch2(r.obj, p.obj)) && (r.act == p.act || regexMatch(r.act, p.act))
"""


class DepartmentHelper:
    """部门层级辅助类"""
    
    @classmethod
    async def get_child_department_ids(cls, dept_id: str, include_self: bool = True) -> Set[str]:
        """获取部门及其所有下属部门ID（不过滤状态）"""
        result = set()
        if include_self:
            result.add(dept_id)
        
        async def get_children(parent_id: str):
            children = await SystemDepartment.filter(
                parent_id=parent_id,
                is_del=False
            ).values_list("id", flat=True)
            
            for child_id in children:
                child_id_str = str(child_id)
                result.add(child_id_str)
                await get_children(child_id_str)
        
        await get_children(dept_id)
        return result
    
    @classmethod
    async def get_all_department_ids(cls) -> Set[str]:
        """获取所有部门ID（不过滤状态，确保能获取到所有部门）"""
        depts = await SystemDepartment.filter(
            is_del=False
        ).values_list("id", flat=True)
        return {str(d) for d in depts}


class CasbinEnforcer:
    """
    Casbin 权限执行器
    
    权限策略结构：
    - p, role_code, permission_id, menu|button  (菜单/按钮权限)
    - p, role_code, /api/path/*, GET|POST|...   (API权限)
    - g, user_id, role_code                      (用户-角色关联)
    
    数据权限基于 user_type：
    - 超级管理员 (0): 全部数据
    - 管理员 (1): 全部数据
    - 部门管理员 (2): 本部门及下属部门
    - 普通用户 (3): 仅本人
    """
    
    _enforcer: Optional[casbin.Enforcer] = None
    _redis: Optional[AsyncRedis] = None
    _model_path: Optional[str] = None
    
    @classmethod
    async def init(cls, redis: AsyncRedis) -> casbin.Enforcer:
        """初始化 Casbin Enforcer"""
        if cls._enforcer is not None:
            return cls._enforcer
        
        cls._redis = redis
        
        try:
            model_text = await cls._get_model_from_redis()
            cls._model_path = cls._write_model_to_temp_file(model_text)
            cls._enforcer = casbin.Enforcer(cls._model_path)
            await cls._load_policy_from_db()
            
            logger.success("Casbin Enforcer 初始化成功")
            return cls._enforcer
            
        except Exception as e:
            logger.error(f"Casbin Enforcer 初始化失败: {e}")
            raise
    
    @classmethod
    def _write_model_to_temp_file(cls, model_text: str) -> str:
        """将模型配置写入临时文件"""
        fd, path = tempfile.mkstemp(suffix='.conf', prefix='casbin_model_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(model_text)
        except:
            os.close(fd)
            raise
        return path
    
    @classmethod
    async def _get_model_from_redis(cls) -> str:
        """从 Redis 获取模型配置"""
        redis_key = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:casbin_model"
        
        model_text = await cls._redis.get(redis_key)
        if model_text:
            return model_text
        
        config_record = await SystemConfig.filter(
            key="casbin_model",
            is_del=False
        ).first()
        
        if config_record and config_record.value:
            model_text = config_record.value
        else:
            model_text = DEFAULT_CASBIN_MODEL
            await SystemConfig.create(
                name="Casbin模型配置",
                key="casbin_model",
                value=model_text,
                type=True,
                remark="Casbin RBAC 权限模型配置"
            )
        
        await cls._redis.set(redis_key, model_text)
        return model_text
    
    @classmethod
    async def _load_policy_from_db(cls):
        """从数据库加载策略到 Enforcer"""
        rules = await CasbinRule.filter(is_del=False).all()
        
        for rule in rules:
            if rule.ptype == 'p':
                policy = [v for v in [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5] if v]
                if policy:
                    cls._enforcer.add_policy(*policy)
            elif rule.ptype == 'g':
                grouping = [v for v in [rule.v0, rule.v1, rule.v2] if v]
                if grouping:
                    cls._enforcer.add_grouping_policy(*grouping)
        
        logger.info(f"从数据库加载了 {len(rules)} 条 Casbin 策略")
    
    @classmethod
    async def _save_policy_to_db(cls, ptype: str, rule: List[str]):
        """保存策略到数据库"""
        await CasbinRule.create(
            ptype=ptype,
            v0=rule[0] if len(rule) > 0 else None,
            v1=rule[1] if len(rule) > 1 else None,
            v2=rule[2] if len(rule) > 2 else None,
            v3=rule[3] if len(rule) > 3 else None,
            v4=rule[4] if len(rule) > 4 else None,
            v5=rule[5] if len(rule) > 5 else None,
        )
    
    @classmethod
    async def _remove_policy_from_db(cls, ptype: str, rule: List[str]) -> bool:
        """从数据库删除策略"""
        filters = {"ptype": ptype, "is_del": False}
        for i, v in enumerate(rule):
            if v:
                filters[f"v{i}"] = v
        
        count = await CasbinRule.filter(**filters).update(is_del=True)
        return count > 0
    
    @classmethod
    def get_enforcer(cls) -> casbin.Enforcer:
        """获取 Enforcer 实例"""
        if cls._enforcer is None:
            raise RuntimeError("Casbin Enforcer 未初始化")
        return cls._enforcer

    # ==================== 数据权限核心方法 ====================
    
    @classmethod
    async def get_data_scope(cls, user_id: str) -> dict:
        """获取用户的数据权限范围"""
        user = await SystemUser.filter(id=user_id, is_del=False).first()
        if not user:
            return {
                "scope": DataScope.SELF_ONLY,
                "user_id": user_id,
                "user_type": UserType.NORMAL_USER,
                "department_id": None,
                "department_ids": set()
            }
        
        user_type = user.user_type
        dept_id = str(user.department_id) if user.department_id else None
        
        if user_type in (UserType.SUPER_ADMIN, UserType.ADMIN):
            all_depts = await DepartmentHelper.get_all_department_ids()
            return {
                "scope": DataScope.ALL,
                "user_id": user_id,
                "user_type": user_type,
                "department_id": dept_id,
                "department_ids": all_depts
            }
        
        if user_type == UserType.DEPT_ADMIN and dept_id:
            child_depts = await DepartmentHelper.get_child_department_ids(dept_id)
            return {
                "scope": DataScope.DEPT_AND_CHILD,
                "user_id": user_id,
                "user_type": user_type,
                "department_id": dept_id,
                "department_ids": child_depts
            }
        
        return {
            "scope": DataScope.SELF_ONLY,
            "user_id": user_id,
            "user_type": user_type,
            "department_id": dept_id,
            "department_ids": {dept_id} if dept_id else set()
        }
    
    @classmethod
    async def can_access_user_data(cls, operator_id: str, target_user_id: str) -> bool:
        """检查操作者是否可以访问目标用户的数据"""
        if operator_id == target_user_id:
            return True
        
        scope = await cls.get_data_scope(operator_id)
        
        if scope["scope"] == DataScope.ALL:
            return True
        
        if scope["scope"] == DataScope.DEPT_AND_CHILD:
            target_user = await SystemUser.filter(id=target_user_id, is_del=False).first()
            if target_user and target_user.department_id:
                return str(target_user.department_id) in scope["department_ids"]
        
        return False
    
    @classmethod
    async def can_access_department_data(cls, operator_id: str, target_dept_id: str) -> bool:
        """检查操作者是否可以访问目标部门的数据"""
        scope = await cls.get_data_scope(operator_id)
        
        if scope["scope"] == DataScope.ALL:
            return True
        
        if scope["scope"] in (DataScope.DEPT_AND_CHILD, DataScope.DEPT_ONLY):
            return target_dept_id in scope["department_ids"]
        
        return False

    # ==================== 角色-权限管理 ====================
    
    @classmethod
    async def add_permission_for_role(cls, role_code: str, permission_id: str, perm_type: str = "menu") -> bool:
        """
        为角色添加权限（菜单/按钮）
        
        Args:
            role_code: 角色编码
            permission_id: 权限ID
            perm_type: 权限类型 (menu/button)
        """
        enforcer = cls.get_enforcer()
        rule = [role_code, permission_id, perm_type]
        
        if enforcer.has_policy(*rule):
            return False
        
        result = enforcer.add_policy(*rule)
        if result:
            await cls._save_policy_to_db('p', rule)
        return result
    
    @classmethod
    async def remove_permission_for_role(cls, role_code: str, permission_id: str, perm_type: str = None) -> bool:
        """移除角色的权限"""
        enforcer = cls.get_enforcer()
        
        if perm_type:
            rule = [role_code, permission_id, perm_type]
            result = enforcer.remove_policy(*rule)
            if result:
                await cls._remove_policy_from_db('p', rule)
        else:
            # 移除所有类型
            result = enforcer.remove_filtered_policy(0, role_code, permission_id)
            if result:
                await CasbinRule.filter(
                    ptype='p', v0=role_code, v1=permission_id, is_del=False
                ).update(is_del=True)
        
        return result
    
    @classmethod
    async def add_api_permission_for_role(cls, role_code: str, api_path: str, api_method: str) -> bool:
        """
        为角色添加 API 权限
        
        Args:
            role_code: 角色编码
            api_path: API 路径（支持通配符，如 /api/user/*）
            api_method: HTTP 方法（支持正则，如 GET|POST）
        """
        enforcer = cls.get_enforcer()
        rule = [role_code, api_path, api_method]
        
        if enforcer.has_policy(*rule):
            return False
        
        result = enforcer.add_policy(*rule)
        if result:
            await cls._save_policy_to_db('p', rule)
        return result
    
    @classmethod
    async def remove_api_permission_for_role(cls, role_code: str, api_path: str, api_method: str = None) -> bool:
        """移除角色的 API 权限"""
        enforcer = cls.get_enforcer()
        
        if api_method:
            rule = [role_code, api_path, api_method]
            result = enforcer.remove_policy(*rule)
            if result:
                await cls._remove_policy_from_db('p', rule)
        else:
            result = enforcer.remove_filtered_policy(0, role_code, api_path)
            if result:
                await CasbinRule.filter(
                    ptype='p', v0=role_code, v1=api_path, is_del=False
                ).update(is_del=True)
        
        return result
    
    @classmethod
    async def get_permissions_for_role(cls, role_code: str) -> List[Dict]:
        """
        获取角色的所有权限
        
        Returns:
            [{"obj": "permission_id/api_path", "act": "menu/button/GET|POST"}]
        """
        enforcer = cls.get_enforcer()
        policies = enforcer.get_permissions_for_user(role_code)
        return [{"obj": p[1], "act": p[2]} for p in policies if len(p) >= 3]
    
    @classmethod
    async def get_menu_permissions_for_role(cls, role_code: str) -> List[str]:
        """获取角色的菜单权限ID列表"""
        enforcer = cls.get_enforcer()
        policies = enforcer.get_permissions_for_user(role_code)
        return [p[1] for p in policies if len(p) >= 3 and p[2] == "menu"]
    
    @classmethod
    async def get_button_permissions_for_role(cls, role_code: str) -> List[str]:
        """获取角色的按钮权限ID列表"""
        enforcer = cls.get_enforcer()
        policies = enforcer.get_permissions_for_user(role_code)
        return [p[1] for p in policies if len(p) >= 3 and p[2] == "button"]
    
    @classmethod
    async def get_api_permissions_for_role(cls, role_code: str) -> List[Dict]:
        """获取角色的 API 权限列表"""
        enforcer = cls.get_enforcer()
        policies = enforcer.get_permissions_for_user(role_code)
        result = []
        for p in policies:
            if len(p) >= 3 and p[2] not in ("menu", "button"):
                # 将逗号分隔的方法字符串转换回列表格式
                method = p[2].split(",") if "," in p[2] else [p[2]]
                result.append({"path": p[1], "method": method})
        return result
    
    @classmethod
    async def set_role_permissions(cls, role_code: str, permission_ids: List[str], perm_type: str = "menu") -> dict:
        """
        设置角色的权限（全量更新）
        
        Args:
            role_code: 角色编码
            permission_ids: 权限ID列表
            perm_type: 权限类型 (menu/button)
            
        Returns:
            {"added": int, "removed": int}
        """
        enforcer = cls.get_enforcer()
        result = {"added": 0, "removed": 0}
        
        # 获取当前权限
        current_policies = enforcer.get_permissions_for_user(role_code)
        current_ids = {p[1] for p in current_policies if len(p) >= 3 and p[2] == perm_type}
        
        new_ids = set(permission_ids)
        
        # 添加新权限
        for perm_id in new_ids - current_ids:
            if await cls.add_permission_for_role(role_code, perm_id, perm_type):
                result["added"] += 1
        
        # 移除旧权限
        for perm_id in current_ids - new_ids:
            if await cls.remove_permission_for_role(role_code, perm_id, perm_type):
                result["removed"] += 1
        
        return result

    # ==================== 用户-角色管理 ====================
    
    @classmethod
    async def add_role_for_user(cls, user_id: str, role_code: str) -> bool:
        """为用户分配角色"""
        enforcer = cls.get_enforcer()
        
        if enforcer.has_grouping_policy(user_id, role_code):
            return False
        
        result = enforcer.add_grouping_policy(user_id, role_code)
        if result:
            await cls._save_policy_to_db('g', [user_id, role_code])
        return result
    
    @classmethod
    async def remove_role_for_user(cls, user_id: str, role_code: str) -> bool:
        """移除用户的角色"""
        enforcer = cls.get_enforcer()
        result = enforcer.remove_grouping_policy(user_id, role_code)
        if result:
            await cls._remove_policy_from_db('g', [user_id, role_code])
        return result
    
    @classmethod
    async def get_roles_for_user(cls, user_id: str) -> List[str]:
        """获取用户的所有角色"""
        enforcer = cls.get_enforcer()
        return enforcer.get_roles_for_user(user_id)
    
    @classmethod
    async def set_roles_for_user(cls, user_id: str, role_codes: List[str]) -> dict:
        """
        设置用户的角色（全量更新）
        
        Returns:
            {"added": int, "removed": int}
        """
        result = {"added": 0, "removed": 0}
        
        current_roles = await cls.get_roles_for_user(user_id)
        current_set = set(current_roles)
        new_set = set(role_codes)
        
        # 添加新角色
        for role in new_set - current_set:
            if await cls.add_role_for_user(user_id, role):
                result["added"] += 1
        
        # 移除旧角色
        for role in current_set - new_set:
            if await cls.remove_role_for_user(user_id, role):
                result["removed"] += 1
        
        return result
    
    @classmethod
    async def get_users_for_role(cls, role_code: str) -> List[str]:
        """获取角色下的所有用户"""
        enforcer = cls.get_enforcer()
        return enforcer.get_users_for_role(role_code)
    
    @classmethod
    async def delete_role(cls, role_code: str) -> bool:
        """删除角色（包括所有关联）"""
        enforcer = cls.get_enforcer()
        result = enforcer.delete_role(role_code)
        if result:
            await CasbinRule.filter(
                ptype='g', v1=role_code, is_del=False
            ).update(is_del=True)
            await CasbinRule.filter(
                ptype='p', v0=role_code, is_del=False
            ).update(is_del=True)
        return result
    
    @classmethod
    async def delete_user(cls, user_id: str) -> bool:
        """删除用户的所有角色关联"""
        enforcer = cls.get_enforcer()
        result = enforcer.delete_user(user_id)
        if result:
            await CasbinRule.filter(
                ptype='g', v0=user_id, is_del=False
            ).update(is_del=True)
        return result

    # ==================== 用户权限查询 ====================
    
    @classmethod
    async def get_user_permissions(cls, user_id: str) -> Dict:
        """
        获取用户的所有权限（通过角色继承）
        
        Returns:
            {
                "roles": ["role1", "role2"],
                "menus": ["menu_id1", "menu_id2"],
                "buttons": ["btn_id1", "btn_id2"],
                "apis": ["GET:/api/user/*", "POST:/api/role/add"]  # method:path 格式
            }
        """
        roles = await cls.get_roles_for_user(user_id)
        
        menus = set()
        buttons = set()
        apis = set()
        
        for role in roles:
            # 菜单权限
            role_menus = await cls.get_menu_permissions_for_role(role)
            menus.update(role_menus)
            
            # 按钮权限
            role_buttons = await cls.get_button_permissions_for_role(role)
            buttons.update(role_buttons)
            
            # API 权限 - 转换为 method:path 格式
            role_apis = await cls.get_api_permissions_for_role(role)
            for api in role_apis:
                # 格式: "GET:/api/user/*" 或 "GET,POST:/api/user/*"
                apis.add(f"{api['method']}:{api['path']}")
        
        return {
            "roles": roles,
            "menus": list(menus),
            "buttons": list(buttons),
            "apis": list(apis)
        }
    
    @classmethod
    async def check_permission(cls, sub: str, obj: str, act: str) -> bool:
        """检查权限"""
        enforcer = cls.get_enforcer()
        return enforcer.enforce(sub, obj, act)
    
    @classmethod
    async def check_api_permission(cls, user_id: str, api_path: str, method: str) -> bool:
        """检查用户的 API 访问权限"""
        # 先检查用户直接权限
        if await cls.check_permission(user_id, api_path, method):
            return True
        
        # 检查用户角色权限
        roles = await cls.get_roles_for_user(user_id)
        for role in roles:
            if await cls.check_permission(role, api_path, method):
                return True
        
        return False

    # ==================== 策略管理 ====================
    
    @classmethod
    async def reload_policy(cls) -> None:
        """重新加载策略"""
        enforcer = cls.get_enforcer()
        enforcer.clear_policy()
        await cls._load_policy_from_db()
        logger.info("Casbin 策略已重新加载")
    
    @classmethod
    async def reload_model(cls) -> None:
        """重新加载模型配置"""
        if not cls._redis:
            raise RuntimeError("Redis 未初始化")
        
        redis_key = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:casbin_model"
        await cls._redis.delete(redis_key)
        model_text = await cls._get_model_from_redis()
        
        if cls._model_path and os.path.exists(cls._model_path):
            os.remove(cls._model_path)
        
        cls._model_path = cls._write_model_to_temp_file(model_text)
        cls._enforcer = casbin.Enforcer(cls._model_path)
        await cls._load_policy_from_db()
        
        logger.info("Casbin 模型配置已重新加载")
    
    @classmethod
    async def update_model(cls, model_text: str) -> bool:
        """更新模型配置"""
        try:
            temp_path = cls._write_model_to_temp_file(model_text)
            casbin.Enforcer(temp_path)
            os.remove(temp_path)
            
            config_record = await SystemConfig.filter(
                key="casbin_model",
                is_del=False
            ).first()
            
            if config_record:
                config_record.value = model_text
                await config_record.save()
            else:
                await SystemConfig.create(
                    name="Casbin模型配置",
                    key="casbin_model",
                    value=model_text,
                    type=True,
                    remark="Casbin RBAC 权限模型配置"
                )
            
            redis_key = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:casbin_model"
            await cls._redis.set(redis_key, model_text)
            await cls.reload_model()
            
            return True
            
        except Exception as e:
            logger.error(f"更新 Casbin 模型配置失败: {e}")
            return False
    
    @classmethod
    async def get_model_text(cls) -> str:
        """获取当前模型配置"""
        redis_key = f"{RedisKeyConfig.SYSTEM_CONFIG.key}:casbin_model"
        return await cls._redis.get(redis_key) or DEFAULT_CASBIN_MODEL
    
    @classmethod
    def get_all_policies(cls) -> List[List[str]]:
        """获取所有策略规则"""
        enforcer = cls.get_enforcer()
        return enforcer.get_policy()
    
    @classmethod
    def get_all_grouping_policies(cls) -> List[List[str]]:
        """获取所有用户-角色关联"""
        enforcer = cls.get_enforcer()
        return enforcer.get_grouping_policy()
