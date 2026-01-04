# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 03:14
# @UpdateTime : 2025/08/25 03:14
# @Author : sonder
# @File : server.py
# @Software : PyCharm
# @Comment : 本程序
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import BaseResponse


class CpuInfo(BaseModel):
    """
    CPU信息
    """
    model_config = ConfigDict()

    cpu_num: Optional[int] = Field(default=None, description='核心数')
    physical_cpu_num: Optional[int] = Field(default=None, description='物理核心数')
    used: Optional[float] = Field(default=None, description='CPU用户使用率')
    sys: Optional[float] = Field(default=None, description='CPU系统使用率')
    free: Optional[float] = Field(default=None, description='CPU当前空闲率')
    total_usage: Optional[float] = Field(default=None, description='CPU总使用率')
    cpu_model: Optional[str] = Field(default=None, description='CPU型号')
    cpu_freq: Optional[str] = Field(default=None, description='CPU频率')


class MemoryInfo(BaseModel):
    """
    内存信息
    """
    model_config = ConfigDict()

    total: Optional[str] = Field(default=None, description='内存总量')
    used: Optional[str] = Field(default=None, description='已用内存')
    free: Optional[str] = Field(default=None, description='剩余内存')
    available: Optional[str] = Field(default=None, description='可用内存')
    usage: Optional[float] = Field(default=None, description='使用率')
    swap_total: Optional[str] = Field(default=None, description='交换内存总量')
    swap_used: Optional[str] = Field(default=None, description='交换内存已用')
    swap_free: Optional[str] = Field(default=None, description='交换内存剩余')
    swap_usage: Optional[float] = Field(default=None, description='交换内存使用率')


class SystemInfo(BaseModel):
    """
    系统信息
    """
    model_config = ConfigDict()

    computer_ip: Optional[str] = Field(default=None, description='服务器IP')
    computer_name: Optional[str] = Field(default=None, description='服务器名称')
    os_arch: Optional[str] = Field(default=None, description='系统架构')
    os_name: Optional[str] = Field(default=None, description='操作系统')
    os_version: Optional[str] = Field(default=None, description='系统版本')
    user_dir: Optional[str] = Field(default=None, description='项目路径')
    boot_time: Optional[str] = Field(default=None, description='系统启动时间')
    system_uptime: Optional[str] = Field(default=None, description='系统运行时长')
    current_time: Optional[str] = Field(default=None, description='当前时间')


class PythonInfo(MemoryInfo):
    """
    Python信息
    """
    model_config = ConfigDict()

    name: Optional[str] = Field(default=None, description='Python名称')
    version: Optional[str] = Field(default=None, description='Python版本')
    start_time: Optional[str] = Field(default=None, description='启动时间')
    run_time: Optional[str] = Field(default=None, description='运行时长')
    home: Optional[str] = Field(default=None, description='安装路径')


class SystemFiles(BaseModel):
    """
    系统磁盘信息
    """
    model_config = ConfigDict()

    dir_name: Optional[str] = Field(default=None, description='盘符路径')
    sys_type_name: Optional[str] = Field(default=None, description='盘符类型')
    type_name: Optional[str] = Field(default=None, description='文件类型')
    mount_point: Optional[str] = Field(default=None, description='挂载点')
    total: Optional[str] = Field(default=None, description='总大小')
    used: Optional[str] = Field(default=None, description='已经使用量')
    free: Optional[str] = Field(default=None, description='剩余大小')
    usage: Optional[str] = Field(default=None, description='资源的使用率')


class NetworkInfo(BaseModel):
    """
    网络信息
    """
    model_config = ConfigDict()

    interface_name: Optional[str] = Field(default=None, description='网卡名称')
    ip_address: Optional[str] = Field(default=None, description='IP地址')
    mac_address: Optional[str] = Field(default=None, description='MAC地址')
    bytes_sent: Optional[str] = Field(default=None, description='发送字节数')
    bytes_recv: Optional[str] = Field(default=None, description='接收字节数')
    packets_sent: Optional[int] = Field(default=None, description='发送包数')
    packets_recv: Optional[int] = Field(default=None, description='接收包数')


class DiskIOInfo(BaseModel):
    """
    磁盘IO信息
    """
    model_config = ConfigDict()

    read_count: Optional[int] = Field(default=None, description='读取次数')
    write_count: Optional[int] = Field(default=None, description='写入次数')
    read_bytes: Optional[str] = Field(default=None, description='读取字节数')
    write_bytes: Optional[str] = Field(default=None, description='写入字节数')
    read_time: Optional[int] = Field(default=None, description='读取时间(ms)')
    write_time: Optional[int] = Field(default=None, description='写入时间(ms)')


class GetSystemInfoResult(BaseModel):
    """
    获取系统信息结果
    """
    model_config = ConfigDict()

    cpu: Optional[CpuInfo] = Field(description='CPU相关信息')
    python: Optional[PythonInfo] = Field(description='Python相关信息')
    memory: Optional[MemoryInfo] = Field(description='內存相关信息')
    system: Optional[SystemInfo] = Field(description='服务器相关信息')
    system_files: Optional[List[SystemFiles]] = Field(description='磁盘相关信息')
    network: Optional[List[NetworkInfo]] = Field(description='网络相关信息')
    disk_io: Optional[DiskIOInfo] = Field(description='磁盘IO信息')


class GetServerInfoResponse(BaseResponse):
    """
    获取服务器信息响应
    """
    data: GetSystemInfoResult = Field(default={}, description="服务器信息查询结果")
