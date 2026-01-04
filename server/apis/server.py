# _*_ coding : UTF-8 _*_
# @Time : 2025/08/25 03:15
# @UpdateTime : 2025/08/25 03:15
# @Author : sonder
# @File : server.py
# @Software : PyCharm
# @Comment : 本程序
import os
import platform
import socket
import time

import psutil
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from annotation.auth import Auth, AuthController
from annotation.log import Log, OperationType
from schemas.server import (
    GetServerInfoResponse, CpuInfo, MemoryInfo, SystemInfo, PythonInfo, SystemFiles,
    GetSystemInfoResult, NetworkInfo, DiskIOInfo
)
from utils.common import bytes2human
from utils.log import logger
from utils.response import ResponseUtil

serverAPI = APIRouter(
    prefix="/server",
    dependencies=[Depends(AuthController.get_current_user)]
)


@serverAPI.get("", response_class=JSONResponse, response_model=GetServerInfoResponse, summary="获取服务器信息")
@Log(title="获取服务器信息", operation_type=OperationType.SELECT)
@Auth(permission_list=["server:btn:info", "GET:/server"])
async def get_server_info(request: Request):
    # CPU信息
    # 获取CPU总核心数（逻辑核心）
    cpu_num = psutil.cpu_count(logical=True)
    # 获取物理核心数
    physical_cpu_num = psutil.cpu_count(logical=False)
    # 获取CPU使用率详情
    cpu_usage_percent = psutil.cpu_times_percent()
    cpu_used = cpu_usage_percent.user
    cpu_sys = cpu_usage_percent.system
    cpu_free = cpu_usage_percent.idle
    # 获取CPU总使用率
    total_usage = psutil.cpu_percent(interval=0.1)
    
    # 尝试获取CPU型号和频率
    cpu_model = "Unknown"
    cpu_freq_str = "Unknown"
    try:
        # 在Windows上尝试获取CPU信息
        if platform.system() == "Windows":
            import wmi
            c = wmi.WMI()
            for processor in c.Win32_Processor():
                cpu_model = processor.Name
                break
        else:
            # Linux系统从/proc/cpuinfo读取
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_model = line.split(':')[1].strip()
                        break
    except Exception as e:
        logger.warning(f"无法获取CPU型号: {e}")
    
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_freq_str = f"{cpu_freq.current:.2f} MHz (最大: {cpu_freq.max:.2f} MHz)"
    except Exception as e:
        logger.warning(f"无法获取CPU频率: {e}")
    
    cpu = CpuInfo(
        cpu_num=cpu_num,
        physical_cpu_num=physical_cpu_num,
        used=cpu_used,
        sys=cpu_sys,
        free=cpu_free,
        total_usage=round(total_usage, 2),
        cpu_model=cpu_model,
        cpu_freq=cpu_freq_str
    )

    # 内存信息
    memory_info = psutil.virtual_memory()
    memory_total = bytes2human(memory_info.total)
    memory_used = bytes2human(memory_info.used)
    memory_free = bytes2human(memory_info.free)
    memory_available = bytes2human(memory_info.available)
    memory_usage = memory_info.percent
    
    # 交换内存信息
    swap_info = psutil.swap_memory()
    swap_total = bytes2human(swap_info.total)
    swap_used = bytes2human(swap_info.used)
    swap_free = bytes2human(swap_info.free)
    swap_usage = swap_info.percent
    
    mem = MemoryInfo(
        total=memory_total,
        used=memory_used,
        free=memory_free,
        available=memory_available,
        usage=memory_usage,
        swap_total=swap_total,
        swap_used=swap_used,
        swap_free=swap_free,
        swap_usage=swap_usage
    )

    # 主机信息
    # 获取主机名
    hostname = socket.gethostname()
    # 获取IP
    computer_ip = socket.gethostbyname(hostname)
    os_name = platform.platform()
    computer_name = platform.node()
    os_arch = platform.machine()
    os_version = platform.version()
    user_dir = os.path.abspath(os.getcwd())
    
    # 获取系统启动时间
    boot_timestamp = psutil.boot_time()
    boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_timestamp))
    
    # 计算系统运行时长
    current_timestamp = time.time()
    uptime_seconds = current_timestamp - boot_timestamp
    uptime_days = int(uptime_seconds // (24 * 60 * 60))
    uptime_hours = int((uptime_seconds % (24 * 60 * 60)) // (60 * 60))
    uptime_minutes = int((uptime_seconds % (60 * 60)) // 60)
    system_uptime = f'{uptime_days}天{uptime_hours}小时{uptime_minutes}分钟'
    
    # 当前时间
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp))
    
    sys = SystemInfo(
        computer_ip=computer_ip,
        computer_name=computer_name,
        os_arch=os_arch,
        os_name=os_name,
        os_version=os_version,
        user_dir=user_dir,
        boot_time=boot_time,
        system_uptime=system_uptime,
        current_time=current_time
    )

    # python解释器信息
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    python_name = current_process.name()
    python_version = platform.python_version()
    python_home = current_process.exe()
    start_time_stamp = current_process.create_time()
    start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time_stamp))
    current_time_stamp = time.time()
    difference = current_time_stamp - start_time_stamp
    # 将时间差转换为天、小时和分钟数
    days = int(difference // (24 * 60 * 60))  # 每天的秒数
    hours = int((difference % (24 * 60 * 60)) // (60 * 60))  # 每小时的秒数
    minutes = int((difference % (60 * 60)) // 60)  # 每分钟的秒数
    run_time = f'{days}天{hours}小时{minutes}分钟'
    # 获取当前Python程序的pid
    pid = os.getpid()
    # 获取该进程的内存信息
    current_process_memory_info = psutil.Process(pid).memory_info()
    py = PythonInfo(
        name=python_name,
        version=python_version,
        start_time=start_time,
        run_time=run_time,
        home=python_home,
        total=bytes2human(memory_info.available),
        used=bytes2human(current_process_memory_info.rss),
        free=bytes2human(memory_info.available - current_process_memory_info.rss),
        usage=round((current_process_memory_info.rss / memory_info.available) * 100, 2),
    )

    # 磁盘信息
    io = psutil.disk_partitions()
    sys_files = []
    for i in io:
        try:
            o = psutil.disk_usage(i.device)
            disk_data = SystemFiles(
                dir_name=i.device,
                sys_type_name=i.fstype,
                type_name='本地固定磁盘（' + i.mountpoint.replace('\\', '') + '）',
                mount_point=i.mountpoint,
                total=bytes2human(o.total),
                used=bytes2human(o.used),
                free=bytes2human(o.free),
                usage=f'{psutil.disk_usage(i.device).percent}%',
            )
            sys_files.append(disk_data)
        except Exception as e:
            logger.error(f"获取磁盘信息失败：{e}")
            continue

    # 网络信息
    network_list = []
    try:
        net_io = psutil.net_io_counters(pernic=True)
        net_if_addrs = psutil.net_if_addrs()
        
        for interface_name, io_counters in net_io.items():
            # 获取该网卡的地址信息
            ip_address = "N/A"
            mac_address = "N/A"
            
            if interface_name in net_if_addrs:
                for addr in net_if_addrs[interface_name]:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip_address = addr.address
                    elif addr.family == psutil.AF_LINK:  # MAC地址
                        mac_address = addr.address
            
            network_info = NetworkInfo(
                interface_name=interface_name,
                ip_address=ip_address,
                mac_address=mac_address,
                bytes_sent=bytes2human(io_counters.bytes_sent),
                bytes_recv=bytes2human(io_counters.bytes_recv),
                packets_sent=io_counters.packets_sent,
                packets_recv=io_counters.packets_recv
            )
            network_list.append(network_info)
    except Exception as e:
        logger.error(f"获取网络信息失败：{e}")

    # 磁盘IO信息
    disk_io = None
    try:
        disk_io_counters = psutil.disk_io_counters()
        if disk_io_counters:
            disk_io = DiskIOInfo(
                read_count=disk_io_counters.read_count,
                write_count=disk_io_counters.write_count,
                read_bytes=bytes2human(disk_io_counters.read_bytes),
                write_bytes=bytes2human(disk_io_counters.write_bytes),
                read_time=disk_io_counters.read_time,
                write_time=disk_io_counters.write_time
            )
    except Exception as e:
        logger.error(f"获取磁盘IO信息失败：{e}")

    result = GetSystemInfoResult(
        cpu=cpu,
        memory=mem,
        system=sys,
        python=py,
        system_files=sys_files,
        network=network_list,
        disk_io=disk_io
    )
    return ResponseUtil.success(data=result)
