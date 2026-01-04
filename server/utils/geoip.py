# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 20:11
# @UpdateTime : 2025/08/03 20:11
# @Author : sonder
# @File : geoip.py
# @Software : PyCharm
# @Comment : 本程序
import atexit
import ipaddress
from pathlib import Path

import geoip2.database
from geoip2.errors import GeoIP2Error

# 初始化 reader 为模块级变量，避免全局污染
_reader = None


def _init_reader():
    global _reader
    if _reader is not None:
        return
    path = Path().cwd() / 'assets' / 'GeoLite2-City.mmdb'
    _reader = geoip2.database.Reader(path)
    atexit.register(_close_reader)


def _close_reader():
    global _reader
    if _reader is not None:
        _reader.close()
        _reader = None


def get_ip_location_info(ip: str) -> str:
    """
    获取 IP 对应的地理位置信息（国家、省、城市）
    :param ip: 需要查询的 IP 地址
    :return: 拼接后的地理位置信息字符串
    """
    if not isinstance(ip, str):
        return "无效IP"
    ip = ip.strip()
    if not ip:
        return "无效IP"
    _init_reader()
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return "无效IP"
    if ip_obj.is_private:
        return "内网IP"
    try:
        response = _reader.city(ip)
    except GeoIP2Error:
        return "未知"
    # 获取国家、省、城市名称
    country = response.country.names.get('zh-CN', response.country.names.get('en', '未知'))
    province = response.subdivisions[0].names.get('zh-CN', response.subdivisions[0].names.get('en',
                                                                                              '未知')) if response.subdivisions else '未知'
    city = response.city.names.get('zh-CN', response.city.names.get('en', '未知'))
    # 只有非“未知”字段才拼接
    location_parts = []
    if country != "未知":
        location_parts.append(country)
    if province != "未知":
        location_parts.append(province)
    if city != "未知":
        location_parts.append(city)
    # 如果所有字段都是“未知”，返回默认值
    if not location_parts:
        return "未知"
    return "|".join(location_parts)
