# _*_ coding : UTF-8 _*_
# @Time : 2025/12/26
# @Author : sonder
# @File : casbin.py
# @Comment : Casbin 策略模型

from tortoise import fields

from models.common import BaseModel


class CasbinRule(BaseModel):
    """
    Casbin 策略规则表
    存储 RBAC 权限策略，支持 p (policy) 和 g (grouping) 规则
    
    p 规则示例: p, role_admin, /api/users, GET  (角色对资源的访问权限)
    g 规则示例: g, user_123, role_admin  (用户与角色的关联)
    """
    
    ptype = fields.CharField(
        max_length=255,
        description="策略类型 (p=policy, g=grouping)",
        source_field="ptype"
    )
    
    v0 = fields.CharField(
        max_length=255,
        null=True,
        description="第一个参数 (通常是 sub/角色)",
        source_field="v0"
    )
    
    v1 = fields.CharField(
        max_length=255,
        null=True,
        description="第二个参数 (通常是 obj/资源路径)",
        source_field="v1"
    )
    
    v2 = fields.CharField(
        max_length=255,
        null=True,
        description="第三个参数 (通常是 act/HTTP方法)",
        source_field="v2"
    )
    
    v3 = fields.CharField(
        max_length=255,
        null=True,
        description="第四个参数 (扩展字段)",
        source_field="v3"
    )
    
    v4 = fields.CharField(
        max_length=255,
        null=True,
        description="第五个参数 (扩展字段)",
        source_field="v4"
    )
    
    v5 = fields.CharField(
        max_length=255,
        null=True,
        description="第六个参数 (扩展字段)",
        source_field="v5"
    )

    class Meta:
        table = "casbin_rule"
        table_description = "Casbin权限策略表"
        ordering = ["-created_at"]
