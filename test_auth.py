import base64

password = "admin123"
auth_b64 = base64.b64encode(f"admin:{password}".encode()).decode()
print(f"Authorization header: Basic {auth_b64}")

decoded = base64.b64decode(auth_b64).decode()
print(f"Decoded: {decoded}")

username, pwd = decoded.split(":", 1)
print(f"Username: {username}, Password: {pwd}")
