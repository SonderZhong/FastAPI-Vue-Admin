# _*_ coding : UTF-8 _*_
# @Time : 2025/08/01 00:12
# @UpdateTime : 2025/08/01 00:12
# @Author : sonder
# @File : __init__.py
# @Software : PyCharm
# @Comment : Schemas导出

# 导出所有schema模块，供其他模块使用
# 注意：这里不需要显式导出，因为schemas模块主要在各自的API中直接导入使用
# 例如：from schemas.user import AddUserParams

__all__ = [
    'auth',
    'cache',
    'common',
    'config',
    'department',
    'file',
    'log',
    'permission',
    'role',
    'server',
    'user',
]
