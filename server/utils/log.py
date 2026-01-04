# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 22:23
# @UpdateTime : 2025/08/03 22:23
# @Author : sonder
# @File : log.py
# @Software : PyCharm
# @Comment : 本程序
import os
import sys
import time

from loguru import logger

# 日志存储目录
log_path = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_path):
    os.makedirs(log_path)  # 如果目录不存在，则创建

# 按天创建日志目录
daily_log_path = os.path.join(log_path, time.strftime("%Y-%m-%d"))
if not os.path.exists(daily_log_path):
    os.makedirs(daily_log_path)

# 定义按级别分开的日志文件路径
log_path_debug = os.path.join(daily_log_path, 'debug.log')
log_path_info = os.path.join(daily_log_path, 'info.log')
log_path_error = os.path.join(daily_log_path, 'error.log')
log_path_warning = os.path.join(daily_log_path, 'warning.log')
log_path_sql = os.path.join(daily_log_path, 'sql.log')  # SQL 查询日志文件

# 定义合并后的日志文件路径
log_path_all = os.path.join(daily_log_path, 'all.log')

# 移除默认的日志处理器
logger.remove()

# 添加控制台日志处理器（彩色输出）
logger.add(
    sink=sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",  # 控制台输出所有级别的日志
    colorize=True,  # 启用彩色输出
    enqueue=True,  # 异步写入日志
)

# 添加按级别分开的日志文件处理器
logger.add(
    sink=log_path_debug,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",  # 只记录 DEBUG 级别的日志
    rotation="50 MB",  # 日志文件大小达到 50MB 时轮换
    retention="30 days",  # 日志文件保留 30 天
    compression="zip",  # 压缩旧日志文件
    encoding="utf-8",
    enqueue=True,  # 异步写入日志
    filter=lambda record: record["level"].name == "DEBUG",  # 只处理 DEBUG 级别的日志
)

logger.add(
    sink=log_path_info,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="INFO",  # 只记录 INFO 级别的日志
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: record["level"].name == "INFO",  # 只处理 INFO 级别的日志
)

logger.add(
    sink=log_path_warning,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="WARNING",  # 只记录 WARNING 级别的日志
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: record["level"].name == "WARNING",  # 只处理 WARNING 级别的日志
)

logger.add(
    sink=log_path_error,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="ERROR",  # 只记录 ERROR 级别的日志
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: record["level"].name == "ERROR",  # 只处理 ERROR 级别的日志
)

# 添加 SQL 查询日志文件处理器
logger.add(
    sink=log_path_sql,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",  # 记录所有 SQL 查询日志
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: "tortoise.db_client" in record["name"],  # 只处理 SQL 查询日志
)

# 添加合并后的日志文件处理器
logger.add(
    sink=log_path_all,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",  # 记录所有级别的日志
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
)

# 自定义日志颜色
logger.level("DEBUG", color="<blue>")  # DEBUG 级别为蓝色
logger.level("INFO", color="<green>")  # INFO 级别为绿色
logger.level("WARNING", color="<yellow>")  # WARNING 级别为金色
logger.level("ERROR", color="<red>")  # ERROR 级别为红色
