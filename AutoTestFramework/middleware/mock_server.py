"""Mock服务 - 用于接口依赖未就绪时的测试"""
from typing import Dict, Any, Optional
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

logger = logging.getLogger(__name__)

class MockHandler(BaseHTTPRequestHandler):
    """Mock请求处理器"""

    routes: Dict[str, Dict] = {}

    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info(f"Mock Server: {format % args}")

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def do_PUT(self):
        self._handle_request("PUT")

    def do_DELETE(self):
        self._handle_request("DELETE")

    def _handle_request(self, method: str):
        """处理请求"""
        route_key = f"{method}:{self.path}"

        if route_key in self.routes:
            config = self.routes[route_key]
            self._send_response(config)
        else:
            self._send_error(404, {"error": "Not found"})

    def _send_response(self, config: Dict):
        """发送配置响应"""
        status = config.get('status', 200)
        headers = config.get('headers', {'Content-Type': 'application/json'})
        body = config.get('body', {})
        delay = config.get('delay', 0)

        # 模拟延迟
        if delay > 0:
            import time
            time.sleep(delay)

        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()

        response_body = json.dumps(body) if isinstance(body, dict) else str(body)
        self.wfile.write(response_body.encode('utf-8'))

    def _send_error(self, status: int, body: Dict):
        """发送错误响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode('utf-8'))

class MockServer:
    """Mock服务器管理器"""

    def __init__(self, host: str = "localhost", port: int = 9999):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self._running = False

    def add_route(self, method: str, path: str, 
                  status: int = 200, 
                  body: Any = None,
                  headers: Optional[Dict] = None,
                  delay: int = 0):
        """添加Mock路由"""
        route_key = f"{method.upper()}:{path}"
        MockHandler.routes[route_key] = {
            'status': status,
            'body': body or {},
            'headers': headers or {'Content-Type': 'application/json'},
            'delay': delay
        }
        logger.info(f"Mock route added: {route_key}")

    def start(self):
        """启动Mock服务器"""
        if self._running:
            return

        self.server = HTTPServer((self.host, self.port), MockHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self._running = True
        logger.info(f"Mock server started at http://{self.host}:{self.port}")

    def stop(self):
        """停止Mock服务器"""
        if self.server and self._running:
            self.server.shutdown()
            self._running = False
            logger.info("Mock server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
