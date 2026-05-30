"""API封装基类 - 提供业务接口的统一封装"""

from typing import Dict, Any, Optional, Union
from core.request_engine import RequestEngine, Method, Response  # 假设Response类存在
from config.environments import get_env_config
import logging

logger = logging.getLogger(__name__)


class BaseAPI:
    """业务API基类，封装HTTP请求公共逻辑"""

    def __init__(self, request_engine: RequestEngine, env: str = "dev") -> None:
        """
        初始化API客户端

        Args:
            request_engine: 请求引擎实例
            env: 环境标识（dev/test/prod等）
        """
        self.request = request_engine
        self.env_config = get_env_config(env)
        self.base_url = self.env_config.get('base_url', '')
        if not self.base_url:
            logger.warning(f"环境 {env} 未配置 base_url，请检查配置")
        self._token: Optional[str] = None

    def _build_url(self, endpoint: str) -> str:
        """构建完整URL，支持绝对路径直接返回"""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        # 去除base_url末尾斜杠和endpoint开头斜杠
        base = self.base_url.rstrip('/')
        path = endpoint.lstrip('/')
        return f"{base}/{path}"

    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建请求头，自动添加认证Token"""
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def set_token(self, token: str) -> None:
        """设置认证令牌"""
        self._token = token
        logger.debug("Token已更新")

    def clear_token(self) -> None:
        """清除认证令牌"""
        self._token = None
        logger.debug("Token已清除")

    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        """内部统一请求方法，处理日志和异常"""
        url = self._build_url(endpoint)
        headers = self._get_headers(kwargs.pop('headers', None))
        logger.debug(f"发起 {method.upper()} 请求: {url}")
        try:
            response = self.request.request(method, url, headers=headers, **kwargs)
            logger.debug(f"响应状态码: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"请求失败 {method} {url}: {e}", exc_info=True)
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """发送GET请求"""
        return self._request('GET', endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs) -> Response:
        """发送POST请求"""
        return self._request('POST', endpoint, data=data, json=json, **kwargs)

    def put(self, endpoint: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs) -> Response:
        """发送PUT请求"""
        return self._request('PUT', endpoint, data=data, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        """发送DELETE请求"""
        return self._request('DELETE', endpoint, **kwargs)

    def patch(self, endpoint: str, data: Optional[Any] = None, **kwargs) -> Response:
        """发送PATCH请求"""
        return self._request('PATCH', endpoint, data=data, **kwargs)


class AuthAPI(BaseAPI):
    """认证相关API封装"""

    def login(self, username: str, password: str) -> Response:
        """
        用户登录，成功后自动保存Token

        Args:
            username: 用户名
            password: 密码
        """
        response = self.post("/api/auth/login", json={"username": username, "password": password})
        if response.is_success:
            # 尝试多种可能的Token路径
            token = (
                    response.body.get("data", {}).get("token") or
                    response.body.get("token") or
                    response.headers.get("Authorization", "").replace("Bearer ", "")
            )
            if token:
                self.set_token(token)
                logger.info(f"用户 {username} 登录成功")
            else:
                logger.warning("登录响应中未找到Token")
        else:
            logger.warning(f"用户 {username} 登录失败: {response.status_code}")
        return response

    def logout(self) -> Response:
        """用户登出，清除本地Token"""
        response = self.post("/api/auth/logout")
        if response.is_success:
            self.clear_token()
        return response

    def refresh_token(self) -> Response:
        """刷新令牌，如果成功则更新本地Token"""
        response = self.post("/api/auth/refresh")
        if response.is_success:
            new_token = response.body.get("data", {}).get("token")
            if new_token:
                self.set_token(new_token)
        return response


class UserAPI(BaseAPI):
    """用户管理API封装"""

    def get_user_list(self, page: int = 1, size: int = 20) -> Response:
        """获取用户列表（分页）"""
        return self.get("/api/users", params={"page": page, "size": size})

    def get_user_detail(self, user_id: Union[str, int]) -> Response:
        """获取指定用户详情"""
        return self.get(f"/api/users/{user_id}")

    def create_user(self, user_data: Dict[str, Any]) -> Response:
        """创建新用户"""
        return self.post("/api/users", json=user_data)

    def update_user(self, user_id: Union[str, int], user_data: Dict[str, Any]) -> Response:
        """更新用户信息（全量更新）"""
        return self.put(f"/api/users/{user_id}", json=user_data)

    def delete_user(self, user_id: Union[str, int]) -> Response:
        """删除用户"""
        return self.delete(f"/api/users/{user_id}")