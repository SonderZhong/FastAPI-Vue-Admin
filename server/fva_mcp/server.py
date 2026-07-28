# _*_ coding : UTF-8 _*_
"""
FVA Helper MCP 服务器

提供数据库操作、Redis操作、辅助开发等功能
"""

import sys
from pathlib import Path

SERVER_DIR = Path(__file__).parent.parent
FVA_MCP_DIR = Path(__file__).parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
if str(FVA_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(FVA_MCP_DIR))

from fastmcp import FastMCP

mcp = FastMCP(
    name="fva-helper",
    instructions="FVA Helper - 提供数据库操作、Redis操作、辅助开发等功能。",
)

# 导入并注册工具
import tools.db_tools as db_tools
import tools.redis_tools as redis_tools
import tools.dev_tools as dev_tools

db_tools.register(mcp)
redis_tools.register(mcp)
dev_tools.register(mcp)


def run_stdio():
    mcp.run(transport="stdio")


def run_sse(host: str = "0.0.0.0", port: int = 9091):
    tools = (
        list(mcp._tool_manager._tools.keys()) if hasattr(mcp, "_tool_manager") else []
    )
    print(f"\n{'=' * 50}")
    print("  FVA Helper MCP 服务")
    print(f"  SSE: http://{host}:{port}/sse")
    if tools:
        print(f"  已注册工具: {len(tools)} 个")
    print(f"{'=' * 50}\n")
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FVA Helper MCP 服务器")
    parser.add_argument("--mode", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9091)
    args = parser.parse_args()
    if args.mode == "sse":
        run_sse(args.host, args.port)
    else:
        run_stdio()
