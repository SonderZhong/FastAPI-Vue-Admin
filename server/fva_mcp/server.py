# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : server.py
# @Comment : FVA Helper MCP 服务器主入口

import sys
from pathlib import Path

# 确保项目路径在 sys.path 中
SERVER_DIR = Path(__file__).parent.parent
FVA_MCP_DIR = Path(__file__).parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
if str(FVA_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(FVA_MCP_DIR))

from fastmcp import FastMCP

# 创建 MCP 服务器
mcp = FastMCP(
    name="fva-helper",
    instructions="""
    FVA Helper - FastAPI-Vue-Admin助手工具。
    提供数据库操作、用户管理、角色管理、权限管理等功能。
    """
)

# 导入并注册工具
import tools.db_tools as db_tools
import tools.redis_tools as redis_tools
import tools.model_tools as model_tools
import tools.schema_tools as schema_tools
import tools.api_tools as api_tools

# 注册数据库工具
db_tools.register(mcp)

# 注册 Redis 工具
redis_tools.register(mcp)

# 注册模型工具
model_tools.register(mcp)

# 注册schema工具
schema_tools.register(mcp)

# 注册API工具
api_tools.register(mcp)


def run_stdio():
    """运行 MCP 服务器（stdio 模式）"""
    mcp.run(transport="stdio")


def run_sse(host: str = "0.0.0.0", port: int = 9091):
    """运行 MCP 服务器（SSE 模式）"""
    # 获取所有已注册的工具
    tools = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') else []
    
    print("\n" + "=" * 60)
    print("  🔧 FVA Helper MCP 服务")
    print("=" * 60)
    print(f"\n  ➜ SSE 端点: http://{host}:{port}/sse")
    print(f"  ➜ 消息端点: http://{host}:{port}/messages/")
    
    if tools:
        print(f"\n  📋 已注册工具 ({len(tools)} 个):")
        for tool in tools:
            print(f"     • {tool}")
    
    print("\n" + "=" * 60 + "\n")
    
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FVA Helper MCP 服务器")
    parser.add_argument("--mode", choices=["stdio", "sse"], default="stdio", help="传输模式")
    parser.add_argument("--host", default="0.0.0.0", help="SSE 模式监听地址")
    parser.add_argument("--port", type=int, default=9091, help="SSE 模式监听端口")
    
    args = parser.parse_args()
    
    if args.mode == "sse":
        run_sse(args.host, args.port)
    else:
        run_stdio()
