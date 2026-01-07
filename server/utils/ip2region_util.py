# _*_ coding : UTF-8 _*_
# @Time : 2026/01/07
# @Author : sonder
# @File : ip2region.py
# @Software : PyCharm
# @Comment : 基于 ip2region xdb 的 IP 地理位置解析
import atexit
import ipaddress
from pathlib import Path

import ip2region.util as util
import ip2region.searcher as xdb

# 初始化 searcher 为模块级变量
_searcher = None
_c_buffer = None


def _init_searcher():
    """初始化 ip2region searcher，使用内存缓存模式以支持并发"""
    global _searcher, _c_buffer
    if _searcher is not None:
        return
    
    db_path = str(Path().cwd() / 'assets' / 'ip2region_v4.xdb')
    
    # 验证 xdb 文件适用性
    try:
        util.verify_from_file(db_path)
    except Exception as e:
        raise RuntimeError(f"ip2region xdb 文件验证失败: {str(e)}")
    
    # 加载整个 xdb 到内存，支持并发查询
    try:
        _c_buffer = util.load_content_from_file(db_path)
        _searcher = xdb.new_with_buffer(util.IPv4, _c_buffer)
    except Exception as e:
        raise RuntimeError(f"ip2region 初始化失败: {str(e)}")
    
    atexit.register(_close_searcher)


def _close_searcher():
    """关闭 searcher 资源"""
    global _searcher, _c_buffer
    if _searcher is not None:
        _searcher.close()
        _searcher = None
        _c_buffer = None


def get_ip_location(ip: str) -> str:
    """
    获取 IP 对应的地理位置信息
    
    :param ip: 需要查询的 IP 地址
    :return: 地理位置信息字符串，格式：国家|省份|城市|运营商
    """
    if not isinstance(ip, str):
        return "无效IP"
    
    ip = ip.strip()
    if not ip:
        return "无效IP"
    
    # 验证 IP 格式
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return "无效IP"
    
    # 内网 IP 直接返回
    if ip_obj.is_private:
        return "内网IP"
    
    # 目前只支持 IPv4
    if ip_obj.version != 4:
        return "暂不支持IPv6"
    
    _init_searcher()
    
    try:
        region = _searcher.search(ip)
        if not region:
            return "未知"
        return _parse_region(region)
    except Exception:
        return "未知"


def _parse_region(region: str) -> str:
    """
    解析 ip2region 返回的 region 字符串
    
    ip2region 返回格式：国家|省份|城市|网络运营商
    例如：中国|广东省|深圳市|电信
    
    :param region: ip2region 返回的原始字符串
    :return: 处理后的地理位置字符串
    """
    if not region:
        return "未知"
    
    parts = region.split('|')
    # 过滤掉 "0" 和空字符串
    valid_parts = [p for p in parts if p and p != '0']
    
    if not valid_parts:
        return "未知"
    
    return "|".join(valid_parts)


def get_ip_location_detail(ip: str) -> dict:
    """
    获取 IP 对应的详细地理位置信息
    
    :param ip: 需要查询的 IP 地址
    :return: 包含详细信息的字典
    """
    result = {
        "country": "",
        "province": "",
        "city": "",
        "isp": "",
        "raw": ""
    }
    
    if not isinstance(ip, str):
        return result
    
    ip = ip.strip()
    if not ip:
        return result
    
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return result
    
    if ip_obj.is_private:
        result["country"] = "内网"
        return result
    
    if ip_obj.version != 4:
        return result
    
    _init_searcher()
    
    try:
        region = _searcher.search(ip)
        if not region:
            return result
        
        result["raw"] = region
        parts = region.split('|')
        
        if len(parts) >= 1 and parts[0] and parts[0] != '0':
            result["country"] = parts[0]
        if len(parts) >= 2 and parts[1] and parts[1] != '0':
            result["province"] = parts[1]
        if len(parts) >= 3 and parts[2] and parts[2] != '0':
            result["city"] = parts[2]
        if len(parts) >= 4 and parts[3] and parts[3] != '0':
            result["isp"] = parts[3]
        
        return result
    except Exception:
        return result
