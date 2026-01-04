# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 02:01
# @UpdateTime : 2025/08/04 02:01
# @Author : sonder
# @File : gzip.py
# @Software : PyCharm
# @Comment : 本程序
from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware


def add_gzip_middleware(app: FastAPI):
    """
    添加gzip压缩中间件

    :param app: FastAPI对象
    :return:
    """
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)
