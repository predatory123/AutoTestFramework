"""Mock API Server - 提供完整测试用Mock接口"""
import json
import time
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API 请求处理器"""

    # 模拟数据存储
    _users: Dict[int, Dict] = {
        1: {"id": 1, "username": "admin", "email": "admin@example.com", "role": "admin"},
        2: {"id": 2, "username": "tester", "email": "tester@example.com", "role": "tester"},
    }
    _next_id = 3
    _tokens: Dict[str, Dict] = {}  # token -> user info

    def log_message(self, format, *args):
        logger.info(f"MockAPI [{self.address_string()}] {format % args}")

    def _send_json(self, status: int, body: Any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Response-Time", f"{round(time.time() * 1000)}ms")
        self.end_headers()
        body_str = json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body
        self.wfile.write(body_str.encode("utf-8"))

    def _get_body(self) -> Dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def _get_token(self) -> Optional[str]:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    def _authenticate(self) -> Optional[Dict]:
        token = self._get_token()
        return self._tokens.get(token)

    # ------------------------------------------------------------------
    # Auth APIs
    # ------------------------------------------------------------------
    def do_POST(self):
        if self.path == "/api/auth/login":
            self._handle_login()
        elif self.path == "/api/auth/logout":
            self._handle_logout()
        elif self.path == "/api/auth/refresh":
            self._handle_refresh()
        elif self.path == "/api/users":
            self._handle_create_user()
        else:
            self._send_json(404, {"error": "Not found"})

    def do_GET(self):
        token_info = self._authenticate()
        if not token_info and not self.path.startswith("/api/auth"):
            self._send_json(401, {"error": "Unauthorized"})
            return

        if self.path == "/api/users":
            self._handle_list_users()
        elif self.path.startswith("/api/users/"):
            user_id = self.path.split("/")[-1]
            self._handle_get_user(user_id)
        else:
            self._send_json(404, {"error": "Not found"})

    def do_PUT(self):
        token_info = self._authenticate()
        if not token_info:
            self._send_json(401, {"error": "Unauthorized"})
            return
        if self.path.startswith("/api/users/"):
            user_id = self.path.split("/")[-1]
            self._handle_update_user(user_id)
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        token_info = self._authenticate()
        if not token_info:
            self._send_json(401, {"error": "Unauthorized"})
            return
        if self.path.startswith("/api/users/"):
            user_id = self.path.split("/")[-1]
            self._handle_delete_user(user_id)
        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_login(self):
        body = self._get_body()
        username = body.get("username")
        password = body.get("password")

        if username == "admin" and password == "Admin@123":
            token = f"mock_token_{int(time.time())}"
            self._tokens[token] = {"id": 1, "username": "admin", "role": "admin"}
            self._send_json(200, {
                "code": 0,
                "message": "success",
                "data": {"token": token, "user_id": 1}
            })
        elif username == "tester" and password == "Test@123":
            token = f"mock_token_{int(time.time())}"
            self._tokens[token] = {"id": 2, "username": "tester", "role": "tester"}
            self._send_json(200, {
                "code": 0,
                "message": "success",
                "data": {"token": token, "user_id": 2}
            })
        elif username and password:
            self._send_json(401, {
                "code": 401,
                "message": "Invalid username or password"
            })
        else:
            self._send_json(400, {"code": 400, "message": "Missing credentials"})

    def _handle_logout(self):
        token = self._get_token()
        if token and token in self._tokens:
            del self._tokens[token]
        self._send_json(200, {"code": 0, "message": "success"})

    def _handle_refresh(self):
        token_info = self._authenticate()
        if token_info:
            new_token = f"mock_token_{int(time.time())}_refresh"
            self._tokens[new_token] = token_info
            self._send_json(200, {"code": 0, "message": "success", "data": {"token": new_token}})
        else:
            self._send_json(401, {"code": 401, "message": "Invalid token"})

    def _handle_list_users(self):
        users_list = list(self._users.values())
        self._send_json(200, {
            "code": 0,
            "message": "success",
            "data": {"total": len(users_list), "items": users_list}
        })

    def _handle_get_user(self, user_id: str):
        try:
            uid = int(user_id)
        except ValueError:
            self._send_json(400, {"code": 400, "message": "Invalid user ID"})
            return
        user = self._users.get(uid)
        if user:
            self._send_json(200, {"code": 0, "message": "success", "data": user})
        else:
            self._send_json(404, {"code": 404, "message": "User not found"})

    def _handle_create_user(self):
        body = self._get_body()
        username = body.get("username")
        email = body.get("email", "")
        role = body.get("role", "tester")

        if not username:
            self._send_json(400, {"code": 400, "message": "Username is required"})
            return

        new_user = {"id": MockAPIHandler._next_id, "username": username, "email": email, "role": role}
        MockAPIHandler._users[MockAPIHandler._next_id] = new_user
        MockAPIHandler._next_id += 1
        self._send_json(201, {"code": 0, "message": "success", "data": new_user})

    def _handle_update_user(self, user_id: str):
        try:
            uid = int(user_id)
        except ValueError:
            self._send_json(400, {"code": 400, "message": "Invalid user ID"})
            return
        if uid not in self._users:
            self._send_json(404, {"code": 404, "message": "User not found"})
            return
        body = self._get_body()
        user = self._users[uid]
        user["username"] = body.get("username", user["username"])
        user["email"] = body.get("email", user["email"])
        user["role"] = body.get("role", user["role"])
        self._send_json(200, {"code": 0, "message": "success", "data": user})

    def _handle_delete_user(self, user_id: str):
        try:
            uid = int(user_id)
        except ValueError:
            self._send_json(400, {"code": 400, "message": "Invalid user ID"})
            return
        if uid in self._users:
            del self._users[uid]
            self._send_json(200, {"code": 0, "message": "success"})
        else:
            self._send_json(404, {"code": 404, "message": "User not found"})


class MockAPIServer:
    """Mock API 服务器管理器"""

    def __init__(self, host: str = "localhost", port: int = 19999):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self):
        if self.server is not None:
            return
        self.server = HTTPServer((self.host, self.port), MockAPIHandler)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"MockAPI server started at {self.base_url}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server = None
            logger.info("MockAPI server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
