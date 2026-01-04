# _*_ coding : UTF-8 _*_
# @Time : 2025/11/23 02:25
# @Author : sonder
# @File : doc.py
# @Software : PyCharm
# @Comment : API文档相关接口

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from utils.config import config

docAPI = APIRouter()

# 设置模板目录
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# 获取API文档配置
def get_doc_config():
    """获取API文档配置"""
    return {
        "title": config.app().name,
        "description": f'{config.app().name}接口文档 - 基于Scalar现代化API文档',
        "description_en": f'{config.app().name} API Documentation - Powered by Scalar Modern Documentation System',
        "version": config.app().version,
        "backend_server": f"http://{config.app().host}:{config.app().port}"
    }


@docAPI.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def scalar_docs(request: Request):
    """Scalar API文档页面"""
    doc_config = get_doc_config()

    # 获取当前请求的基础URL
    scheme = request.url.scheme
    host = request.headers.get("host", f"{config.app().host}:{config.app().port}")
    base_url = f"{scheme}://{host}"

    # 使用模板渲染
    return templates.TemplateResponse(
        "scalar_docs.html",
        {
            "request": request,
            "title": doc_config["title"],
            "description": doc_config["description"],
            "description_en": doc_config["description_en"],
            "version": doc_config["version"],
            "base_url": base_url,
            "backend_port": config.app().port
        }
    )


@docAPI.get("/docs/config", include_in_schema=False)
async def docs_config():
    """获取API文档配置信息"""
    return get_doc_config()