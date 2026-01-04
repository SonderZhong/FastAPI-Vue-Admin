# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 16:25
# @UpdateTime : 2025/08/03 16:25
# @Author : sonder
# @File : app.py
# @Software : PyCharm
# @Comment : 本程序
# 从配置模块导入全局配置实例
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apis import register_api
from exceptions.handle import handle_exception
from middlewares.handle import handle_middleware
from utils.config import config
from utils.database import init_db, close_db
from utils.get_redis import RedisUtil
from utils.log import logger
from utils.casbin import CasbinEnforcer
from utils.dynamic_config import init_dynamic_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'{config.app().name}开始启动')
    app.state.redis = await RedisUtil.create_redis_connection()
    logger.info(f'{config.app().name}启动成功')
    await init_db()
    await RedisUtil.init_system_config(app.state.redis)
    
    # 初始化动态配置服务
    dynamic_config = init_dynamic_config(app.state.redis)
    await dynamic_config.init_default_configs()  # 初始化默认配置
    await dynamic_config.load_all_to_redis()     # 加载配置到 Redis
    app.state.dynamic_config = dynamic_config
    
    # 初始化 Casbin（传入 Redis 实例）
    await CasbinEnforcer.init(app.state.redis)
    yield
    await close_db()
    await RedisUtil.close_redis_connection(app.state.redis)


# 检查是否启用API文档
docs_enabled = config.app().api_status_enabled

app = FastAPI(
    title=config.app().name,
    description=f'{config.app().name}接口文档 - 基于Scalar现代化API文档',
    version=config.app().version,
    lifespan=lifespan,
    # 配置OpenAPI规范路径，解决代理访问问题
    openapi_url="/openapi.json" if docs_enabled else None,
    # 禁用默认的Swagger UI和ReDoc，使用Scalar替代
    docs_url=None,
    redoc_url=None,
)
# 加载中间件处理方法
handle_middleware(app)
# 加载全局异常处理方法
handle_exception(app)
# 注册API路由
register_api(app)


# 配置静态文件服务 - 同时支持 /assets/ 和 /api/assets/ 路径
assets_path = Path(__file__).parent / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    app.mount("/api/assets", StaticFiles(directory=str(assets_path)), name="api_assets")

if __name__ == '__main__':
    uvicorn.run(
        app='app:app',
        host=config.app().host,
        port=config.app().port,
        reload=config.app().reload,
        log_config="uvicorn_config.json"
    )
