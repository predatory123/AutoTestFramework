"""API封装基类 - 提供业务接口的统一封装"""
from typing import Dict, Any, Optional
from core.request_engine import RequestEngine, Method
from config.environments import get_env_config
import logging

logger = logging.getLogger(__name__)

class BaseAPI:
    """业务API基类"""

    def __init__(self, request_engine: RequestEngine, env: str = "dev"):
        self.request = request_engine
        self.env_config = get_env_config(env)
        self.base_url = self.env_config['base_url']
        self._token = None

    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        if endpoint.startswith('http'):
            return endpoint
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _get_headers(self, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def set_token(self, token: str):
        """设置认证令牌"""
        self._token = token

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs):
        """GET请求"""
        return self.request.get(
            self._build_url(endpoint),
            headers=self._get_headers(),
            params=params,
            **kwargs
        )

    def post(self, endpoint: str, data: Any = None, **kwargs):
        """POST请求"""
        return self.request.post(
            self._build_url(endpoint),
            headers=self._get_headers(),
            data=data,
            **kwargs
        )

    def put(self, endpoint: str, data: Any = None, **kwargs):
        """PUT请求"""
        return self.request.put(
            self._build_url(endpoint),
            headers=self._get_headers(),
            data=data,
            **kwargs
        )

    def delete(self, endpoint: str, **kwargs):
        """DELETE请求"""
        return self.request.delete(
            self._build_url(endpoint),
            headers=self._get_headers(),
            **kwargs
        )

class AuthAPI(BaseAPI):
    """认证相关API封装示例"""

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        response = self.post("/api/auth/login", data={
            "username": username,
            "password": password
        })

        if response.is_success:
            token = response.body.get("data", {}).get("token")
            if token:
                self.set_token(token)

        return response

    def logout(self):
        """用户登出"""
        return self.post("/api/auth/logout")

    def refresh_token(self):
        """刷新令牌"""
        return self.post("/api/auth/refresh")

class UserAPI(BaseAPI):
    """用户管理API封装示例"""

    def get_user_list(self, page: int = 1, size: int = 20):
        """获取用户列表"""
        return self.get("/api/users", params={"page": page, "size": size})

    def get_user_detail(self, user_id: str):
        """获取用户详情"""
        return self.get(f"/api/users/{user_id}")

    def create_user(self, user_data: Dict):
        """创建用户"""
        return self.post("/api/users", data=user_data)

    def update_user(self, user_id: str, user_data: Dict):
        """更新用户"""
        return self.put(f"/api/users/{user_id}", data=user_data)

    def delete_user(self, user_id: str):
        """删除用户"""
        return self.delete(f"/api/users/{user_id}")
