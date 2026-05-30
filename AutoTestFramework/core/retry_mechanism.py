"""重试机制与故障恢复策略"""
import time
import random
from functools import wraps
from typing import Callable, Tuple, Type, Optional
import logging

logger = logging.getLogger(__name__)

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

class CircuitBreakerWithRetry:
    """带重试的熔断器"""

    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0

    def call(self, func: Callable, *args, **kwargs):
        """执行带熔断保护的函数"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        if self.state == "HALF_OPEN" and self.half_open_calls >= self.half_open_max_calls:
            raise CircuitBreakerOpenError("Circuit breaker HALF_OPEN limit reached")

        if self.state == "HALF_OPEN":
            self.half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def _record_success(self):
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self.state = "CLOSED"
                self.success_count = 0
                logger.info("Circuit breaker CLOSED (recovered)")

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.error("Circuit breaker OPENED (half-open test failed)")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPENED after {self.failure_threshold} failures")

class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass
