import asyncio
import aiohttp
import requests
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class Method(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

@dataclass
class Response:
    """统一响应对象"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    response_time: float
    raw_response: Any

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        return self.body if isinstance(self.body, dict) else {}

class CircuitBreaker:
    """熔断器模式 - 防止级联故障"""
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPENED for service")

def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """指数退避重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Attempt {attempt} failed: {str(e)}")
                    if attempt == max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            return None
        return wrapper
    return decorator

class RequestEngine:
    """高可用HTTP请求引擎 - 支持同步/异步、连接池、熔断、重试"""

    def __init__(self, config=None):
        self.config = config or {}
        self.session = requests.Session()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=100,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # 默认请求头
        self.session.headers.update({
            "User-Agent": "AutoTest-Framework/2.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def _get_circuit_breaker(self, host: str) -> CircuitBreaker:
        if host not in self.circuit_breakers:
            self.circuit_breakers[host] = CircuitBreaker()
        return self.circuit_breakers[host]

    @retry(max_attempts=3, delay=1, backoff=2, 
           exceptions=(requests.RequestException, TimeoutError))
    def request(self, method: Method, url: str, 
                headers: Optional[Dict] = None,
                data: Optional[Any] = None,
                params: Optional[Dict] = None,
                timeout: int = 30,
                **kwargs) -> Response:
        """同步请求方法"""

        host = url.split('/')[2]
        breaker = self._get_circuit_breaker(host)

        if not breaker.can_execute():
            raise Exception(f"Circuit breaker is OPEN for {host}")

        start_time = time.time()
        merged_headers = {**self.session.headers, **(headers or {})}

        try:
            resp = self.session.request(
                method=method.value,
                url=url,
                headers=merged_headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
                params=params,
                timeout=timeout,
                **kwargs
            )

            response_time = round((time.time() - start_time) * 1000, 2)

            # 尝试解析JSON
            try:
                body = resp.json()
            except ValueError:
                body = resp.text

            response = Response(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=body,
                response_time=response_time,
                raw_response=resp
            )

            # 记录成功
            if response.is_success:
                breaker.record_success()
            else:
                breaker.record_failure()

            logger.info(f"[{method.value}] {url} - {resp.status_code} ({response_time}ms)")
            return response

        except Exception as e:
            breaker.record_failure()
            logger.error(f"Request failed: [{method.value}] {url} - {str(e)}")
            raise

    # 便捷方法
    def get(self, url, **kwargs): return self.request(Method.GET, url, **kwargs)
    def post(self, url, **kwargs): return self.request(Method.POST, url, **kwargs)
    def put(self, url, **kwargs): return self.request(Method.PUT, url, **kwargs)
    def delete(self, url, **kwargs): return self.request(Method.DELETE, url, **kwargs)

    async def async_request(self, method: Method, url: str, **kwargs) -> Response:
        """异步请求方法 - 用于并发测试场景"""
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.request(method.value, url, **kwargs) as resp:
                response_time = round((time.time() - start_time) * 1000, 2)
                body = await resp.json()
                return Response(
                    status_code=resp.status,
                    headers=dict(resp.headers),
                    body=body,
                    response_time=response_time,
                    raw_response=resp
                )

class AsyncBatchProcessor:
    """批量异步处理器 - 用于压力测试"""

    def __init__(self, engine: RequestEngine):
        self.engine = engine

    async def batch_request(self, requests: list, max_concurrent: int = 10):
        """控制并发数的批量请求"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_request(req):
            async with semaphore:
                return await self.engine.async_request(**req)

        tasks = [bounded_request(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
