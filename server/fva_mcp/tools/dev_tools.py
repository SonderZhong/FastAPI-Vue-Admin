# _*_ coding : UTF-8 _*_
"""
辅助开发工具

提供项目信息查询、代码分析、模型结构查看等功能
"""

import json
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).parent.parent.parent
MODULES_DIR = BASE_DIR / "modules"


def register(mcp):
    """注册开发辅助工具"""

    # ==================== 项目信息 ====================

    @mcp.tool()
    async def get_project_info() -> str:
        """获取项目基本信息"""
        import yaml

        config_path = BASE_DIR / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        app = config.get("app", {})
        return json.dumps(
            {
                "name": app.get("name", "FastAPI-Vue-Admin"),
                "version": app.get("version", "1.0.0"),
                "env": app.get("env", "dev"),
                "host": app.get("host", "0.0.0.0"),
                "port": app.get("port", 9090),
            },
            ensure_ascii=False,
        )

    @mcp.tool()
    async def list_modules() -> str:
        """列出所有业务模块"""
        modules = []
        for item in MODULES_DIR.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith("_")
                and item.name != "__pycache__"
            ):
                has_router = (item / "router.py").exists()
                has_service = (item / "service.py").exists()
                has_model = (item / "model.py").exists()
                has_schema = (item / "schema.py").exists()
                modules.append(
                    {
                        "name": item.name,
                        "has_router": has_router,
                        "has_service": has_service,
                        "has_model": has_model,
                        "has_schema": has_schema,
                    }
                )
        return json.dumps(modules, ensure_ascii=False)

    @mcp.tool()
    async def get_module_info(module_name: str) -> str:
        """获取指定模块的详细信息"""
        module_dir = MODULES_DIR / module_name
        if not module_dir.exists():
            return json.dumps(
                {"error": f"模块 {module_name} 不存在"}, ensure_ascii=False
            )

        info = {"name": module_name, "files": []}
        for item in module_dir.iterdir():
            if (
                item.is_file()
                and item.suffix == ".py"
                and not item.name.startswith("_")
            ):
                info["files"].append(
                    {
                        "name": item.name,
                        "size": item.stat().st_size,
                        "lines": len(item.read_text(encoding="utf-8").splitlines()),
                    }
                )
        return json.dumps(info, ensure_ascii=False)

    # ==================== 模型分析 ====================

    @mcp.tool()
    async def get_model_structure(module_name: str) -> str:
        """获取指定模块的模型结构（字段、类型、约束）"""
        model_file = MODULES_DIR / module_name / "model.py"
        if not model_file.exists():
            return json.dumps(
                {"error": f"模块 {module_name} 没有 model.py"}, ensure_ascii=False
            )

        content = model_file.read_text(encoding="utf-8")
        import re

        models = []
        class_pattern = r"class (\w+)\((?:DbBaseModel|models\.Model)\):"
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            start = match.end()
            next_class = re.search(r"class \w+\(", content[start:])
            end = start + next_class.start() if next_class else len(content)
            class_body = content[start:end]

            fields = []
            field_pattern = r"(\w+)\s*=\s*fields\.(\w+)\((.*?)\)"
            for fm in re.finditer(field_pattern, class_body, re.DOTALL):
                field_name = fm.group(1)
                field_type = fm.group(2)
                field_args = fm.group(3)[:200]
                fields.append(
                    {"name": field_name, "type": field_type, "args": field_args.strip()}
                )

            models.append({"class": class_name, "fields": fields})

        return json.dumps(models, ensure_ascii=False)

    # ==================== API 分析 ====================

    @mcp.tool()
    async def list_api_endpoints(module_name: Optional[str] = None) -> str:
        """列出 API 端点（可按模块过滤）"""
        import re

        endpoints = []

        search_dirs = (
            [MODULES_DIR / module_name]
            if module_name
            else [
                d
                for d in MODULES_DIR.iterdir()
                if d.is_dir() and not d.name.startswith("_")
            ]
        )

        for module_dir in search_dirs:
            router_file = module_dir / "router.py"
            if not router_file.exists():
                continue

            content = router_file.read_text(encoding="utf-8")
            pattern = r'@(\w+)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(pattern, content):
                method = match.group(2).upper()
                path = match.group(3)
                endpoints.append(
                    {
                        "module": module_dir.name,
                        "method": method,
                        "path": path,
                    }
                )

        return json.dumps(
            {"count": len(endpoints), "endpoints": endpoints[:50]}, ensure_ascii=False
        )

    # ==================== 配置查看 ====================

    @mcp.tool()
    async def get_dynamic_config(group: Optional[str] = None) -> str:
        """查看动态配置（从数据库读取）"""
        import yaml
        from tortoise import Tortoise
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        nodes = config.get("database", {}).get("nodes", [])
        if not nodes:
            return json.dumps({"error": "未配置数据库"}, ensure_ascii=False)

        db = nodes[0]
        engine = db.get("engine", "sqlite")
        if engine == "sqlite":
            db_url = f"sqlite://{db.get('database', 'fva.db')}"
        elif engine == "mysql":
            db_url = f"mysql://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
        else:
            db_url = f"postgres://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"

        if not Tortoise._inited:
            await Tortoise.init(
                config={
                    "connections": {"system": db_url},
                    "apps": {
                        "system": {
                            "models": ["modules.config.model"],
                            "default_connection": "system",
                        }
                    },
                },
            )

        from modules.config.model import SystemConfig

        filters = {"is_del": False}
        if group:
            filters["group"] = group
        configs = await SystemConfig.filter(**filters).values(
            "key", "value", "name", "group"
        )
        await Tortoise.close_connections()
        return json.dumps(list(configs), ensure_ascii=False)

    # ==================== 日志查看 ====================

    @mcp.tool()
    async def list_operation_logs(
        page: int = 1, page_size: int = 10, operation_type: Optional[int] = None
    ) -> str:
        """查询操作日志"""
        import yaml
        from tortoise import Tortoise
        from pathlib import Path

        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        nodes = config.get("database", {}).get("nodes", [])
        if not nodes:
            return json.dumps({"error": "未配置数据库"}, ensure_ascii=False)

        db = nodes[0]
        engine = db.get("engine", "sqlite")
        if engine == "sqlite":
            db_url = f"sqlite://{db.get('database', 'fva.db')}"
        elif engine == "mysql":
            db_url = f"mysql://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
        else:
            db_url = f"postgres://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"

        if not Tortoise._inited:
            await Tortoise.init(
                config={
                    "connections": {"system": db_url},
                    "apps": {
                        "system": {
                            "models": ["modules.log.model"],
                            "default_connection": "system",
                        }
                    },
                },
            )

        from modules.log.model import SystemOperationLog

        filters = {"is_del": False}
        if operation_type is not None:
            filters["operation_type"] = operation_type

        total = await SystemOperationLog.filter(**filters).count()
        logs = (
            await SystemOperationLog.filter(**filters)
            .order_by("-created_at")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .values(
                "id",
                "operation_name",
                "operation_type",
                "request_path",
                "request_method",
                "host",
                "status",
                "cost_time",
                "created_at",
            )
        )
        await Tortoise.close_connections()
        return json.dumps(
            {"total": total, "data": list(logs)}, default=str, ensure_ascii=False
        )
