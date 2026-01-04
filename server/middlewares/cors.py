# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 02:00
# @UpdateTime : 2025/08/04 02:00
# @Author : sonder
# @File : cors.py
# @Software : PyCharm
# @Comment : 本程序
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI):
    """
    添加跨域中间件

    :param app: FastAPI对象
    :return:
    """
    # 前端页面url
    origins = [
        "*"
    ]

    # 后台api允许跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
