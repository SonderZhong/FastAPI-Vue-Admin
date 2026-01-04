# _*_ coding : UTF-8 _*_
# @Time : 2025/08/03 20:09
# @UpdateTime : 2025/08/03 20:09
# @Author : sonder
# @File : common.py
# @Software : PyCharm
# @Comment : 本程序
from typing import List, Any, Optional, Type


def bytes2human(n, format_str='%(value).1f%(symbol)s'):
    """Used by various scripts. See:
    http://goo.gl/zeJZl

    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'
    """
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format_str % locals()
    return format_str % dict(symbol=symbols[0], value=n)


async def filterKeyValues(dataList: List[dict], key: str, default: Any = None, convert_type: Optional[Type] = None) -> \
List[Any]:
    """
    获取列表字段数据，并可选择进行类型转换。
    :param dataList: 数据列表（列表中的元素是字典）
    :param key: 要提取的字段
    :param default: 如果字段不存在，返回的默认值
    :param convert_type: 需要转换的类型（如 int、str、float 等），默认为 None 不转换
    :return: 提取并转换后的值列表
    """
    return [convert_type(item.get(key, default)) if convert_type else item.get(key, default) for item in dataList]
