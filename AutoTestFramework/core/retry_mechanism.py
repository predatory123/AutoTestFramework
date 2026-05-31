"""重试机制与故障恢复策略 - 统一的实现"""
import time
import random
from functools import wraps
from typing import Callable, Tuple, Type
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "ExponentialBackoffRetry",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
]


class ExponentialBackoffRetry:
    """指数退避重试策略"""

    def __init__(self,
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, self.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    if attempt == self.max_attempts:
                        logger.error(f"Max retry attempts ({self.max_attempts}) reached. Final error: {e}")
                        raise

                    delay = min(
                        self.base_delay * (self.exponential_base ** (attempt - 1)),
                        self.max_delay
                    )
                    if self.jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
            return None
        return wrapper


class CircuitBreaker:
    """熔断器模式 - 防止级联故障"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """检查当前是否可以执行请求"""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False
        # HALF_OPEN 状态允许放行一个请求
        return True

    def record_success(self):
        """记录成功，恢复正常状态"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker CLOSED (recovered)")
        elif self.state == "CLOSED":
            self.failure_count = 0

    def record_failure(self):
        """记录失败，必要时打开熔断"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.error("Circuit breaker OPENED (half-open test failed)")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass
