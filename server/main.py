# _*_ coding : UTF-8 _*_
# @Time : 2025/01/02
# @Author : sonder
# @File : main.py
# @Comment : 应用入口，根据是否已初始化决定启动主服务或初始化向导

import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

CONFIG_PATH = BASE_DIR / "config.yaml"


def check_config_exists() -> bool:
    """检查配置文件是否存在且已初始化。"""
    if not CONFIG_PATH.exists() or not CONFIG_PATH.is_file():
        return False

    try:
        import yaml

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return config.get("initialized", False) is True
    except Exception:
        return False


def start_setup_server():
    """启动初始化向导服务。"""
    from setup.setup_app import run_setup_server

    run_setup_server(host="0.0.0.0", port=9090)


def start_main_app():
    """启动正式后端服务。"""
    import uvicorn
    from utils.config import config

    print("\n" + "=" * 60)
    print(f"  Ready {config.app().name}")
    print("=" * 60)
    print(f"\n  Main app: http://localhost:{config.app().port}")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(
        app="app:app",
        host=config.app().host,
        port=config.app().port,
        reload=config.app().reload,
        log_config="uvicorn_config.json",
    )


def main():
    """程序入口。"""
    if check_config_exists():
        print("Detected initialized config, starting main application...")
        start_main_app()
    else:
        print("Config not initialized, starting setup wizard...")
        start_setup_server()


if __name__ == "__main__":
    main()
