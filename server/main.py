# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : main.py
# @Comment : 应用入口 - 自动检测配置并启动对应服务

import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)  # 切换工作目录

CONFIG_PATH = BASE_DIR / "config.yaml"


def check_config_exists() -> bool:
    """检查配置文件是否已初始化"""
    if not CONFIG_PATH.exists() or not CONFIG_PATH.is_file():
        return False
    
    # 读取配置文件检查 initialized 字段
    try:
        import yaml
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config.get('initialized', False) is True
    except Exception:
        return False


def start_setup_server():
    """启动初始化服务器"""
    # 延迟导入，避免触发 config 加载
    from setup.setup_app import run_setup_server
    run_setup_server(host="0.0.0.0", port=9090)


def start_main_app():
    """启动主应用"""
    # 延迟导入，此时配置文件已存在
    import uvicorn
    from utils.config import config
    
    print("\n" + "=" * 60)
    print(f"  🚀 {config.app().name}")
    print("=" * 60)
    print(f"\n  ➜ 主应用: http://localhost:{config.app().port}")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(
        app='app:app',
        host=config.app().host,
        port=config.app().port,
        reload=config.app().reload,
        log_config="uvicorn_config.json"
    )


def main():
    """主入口函数"""
    # 先检查配置文件，再决定导入哪个模块
    if check_config_exists():
        print("✓ 检测到配置文件，启动主应用...")
        start_main_app()
    else:
        print("✗ 未检测到配置文件，启动初始化向导...")
        start_setup_server()


if __name__ == "__main__":
    main()
