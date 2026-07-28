# _*_ coding : UTF-8 _*_
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from modules.routers import register_api
from modules.dictionary.service import DictionaryService
from exceptions.handle import handle_exception
from middlewares.handle import handle_middleware
from utils.config import config
from utils.database import init_db, close_db
from utils.get_redis import RedisUtil
from utils.log import logger
from utils.dynamic_config import init_dynamic_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'{config.app().name}开始启动')

    redis_connections = await RedisUtil.create_all_connections()
    app.state.redis = redis_connections.get("system")
    app.state.redis_connections = redis_connections

    await init_db()
    await RedisUtil.init_system_config(app.state.redis)
    await DictionaryService.ensure_default_dictionaries(app.state.redis)

    dynamic_config = init_dynamic_config(app.state.redis)
    await dynamic_config.init_default_configs()
    await dynamic_config.load_all_to_redis()
    app.state.dynamic_config = dynamic_config

    # 初始化 Sentry（有 DSN 才上报）
    from utils.sentry import init_sentry
    await init_sentry(dynamic_config)

    logger.info(f'{config.app().name}启动成功')
    yield
    await close_db()
    await RedisUtil.close_all_connections()


docs_enabled = config.app().api_status_enabled

app = FastAPI(
    title=config.app().name,
    description=f'{config.app().name}接口文档',
    version=config.app().version,
    lifespan=lifespan,
    openapi_url="/openapi.json" if docs_enabled else None,
    docs_url=None,
    redoc_url=None,
)

handle_middleware(app)
handle_exception(app)
register_api(app)

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
        log_config="uvicorn_config.json",
    )
