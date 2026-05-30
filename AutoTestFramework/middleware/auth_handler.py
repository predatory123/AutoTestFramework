"""认证中间件 - 处理Token刷新和权限验证"""
from typing import Dict, Optional, Callable
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class AuthHandler:
    """认证处理器 - 自动管理Token生命周期"""

    def __init__(self, 
                 token_refresh_callback: Callable,
                 token_validity_threshold: int = 300):  # 5分钟
        self.token_refresh_callback = token_refresh_callback
        self.token_validity_threshold = token_validity_threshold
        self._token = None
        self._token_expiry = 0
        self._refresh_lock = False

    @property
    def token(self) -> Optional[str]:
        """获取当前有效令牌"""
        if self._is_token_expired() and not self._refresh_lock:
            self._refresh_token()
        return self._token

    def _is_token_expired(self) -> bool:
        """检查令牌是否即将过期"""
        return time.time() >= (self._token_expiry - self.token_validity_threshold)

    def _refresh_token(self):
        """刷新令牌"""
        try:
            self._refresh_lock = True
            new_token, expiry = self.token_refresh_callback()
            self._token = new_token
            self._token_expiry = expiry
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
        finally:
            self._refresh_lock = False

    def set_token(self, token: str, expires_in: int = 3600):
        """手动设置令牌"""
        self._token = token
        self._token_expiry = time.time() + expires_in

    def clear_token(self):
        """清除令牌"""
        self._token = None
        self._token_expiry = 0

def require_auth(auth_handler: AuthHandler):
    """认证装饰器 - 自动添加认证头"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            headers = kwargs.get('headers', {})
            token = auth_handler.token
            if token:
                headers['Authorization'] = f'Bearer {token}'
                kwargs['headers'] = headers
            return func(*args, **kwargs)
        return wrapper
    return decorator
