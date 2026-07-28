# _*_ coding : UTF-8 _*_
"""
树形结构构建工具

翻译自 junoyi-framework-core TreeBuildUtils
"""

from typing import List, TypeVar, Any

T = TypeVar("T")


def build_tree(
    items: List[T],
    parent_id_key: str = "parent_id",
    id_key: str = "id",
    children_key: str = "children",
    root_parent_id: Any = None,
) -> List[dict]:
    """
    构建树形结构

    Args:
        items: 原始数据列表（需包含 parent_id 字段）
        parent_id_key: 父节点 ID 字段名
        id_key: 节点 ID 字段名
        children_key: 子节点列表字段名
        root_parent_id: 根节点的 parent_id 值

    Returns:
        树形结构列表

    Example:
        items = [
            {"id": 1, "name": "A", "parent_id": None, "sort": 0},
            {"id": 2, "name": "B", "parent_id": 1, "sort": 1},
        ]
        tree = build_tree(items)
    """
    if not items:
        return []

    # 转换为 dict 列表
    if items and hasattr(items[0], "__dict__"):
        data = [item.__dict__ for item in items]
    elif items and isinstance(items[0], dict):
        data = [dict(item) for item in items]
    else:
        data = [item for item in items]

    item_map = {str(item[id_key]): {**item, children_key: []} for item in data}
    tree = []

    for item in data:
        pid = item.get(parent_id_key)
        if pid is not None and str(pid) in item_map:
            item_map[str(pid)][children_key].append(item_map[str(item[id_key])])
        elif pid == root_parent_id or (root_parent_id is None and pid is None):
            tree.append(item_map[str(item[id_key])])

    # 递归排序子节点（如果有 sort 字段）
    def sort_children(node):
        children = node.get(children_key, [])
        if children:
            children.sort(key=lambda x: x.get("sort", 0))
            for child in children:
                sort_children(child)
        return node

    tree.sort(key=lambda x: x.get("sort", 0))
    tree = [sort_children(node) for node in tree]

    return tree
