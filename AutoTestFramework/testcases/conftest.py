"""pytest全局配置和fixtures"""
import pytest
import allure
import os
from typing import Dict, Any
from core.request_engine import RequestEngine
from core.data_driver import DataDriver
from core.base_test import TestContext, Validator
from api.base_api import AuthAPI, UserAPI
from config.settings import CONFIG
from hooks.dingtalk_notifier import DingTalkPytestPlugin


# ---------------------------------------------------------------------------
# 核心 fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def request_engine():
    """全局请求引擎 - 会话级"""
    engine = RequestEngine(CONFIG.__dict__)
    yield engine
    engine.session.close()


@pytest.fixture(scope="session")
def data_driver():
    """数据驱动实例 - 会话级"""
    return DataDriver()


@pytest.fixture(scope="session")
def auth_api(request_engine):
    """认证API实例"""
    return AuthAPI(request_engine, CONFIG.ENV)


@pytest.fixture(scope="session")
def user_api(request_engine):
    """用户API实例"""
    return UserAPI(request_engine, CONFIG.ENV)


# ---------------------------------------------------------------------------
# 认证 fixtures
# ---------------------------------------------------------------------------

def _get_admin_credentials():
    """从环境变量获取管理员凭证，避免硬编码"""
    return {
        "username": os.getenv("ADMIN_USER", ""),
        "password": os.getenv("ADMIN_PASSWORD", "")
    }


@pytest.fixture(scope="session")
def admin_token(auth_api):
    """管理员令牌 - 失败时返回 None，不跳过整个测试会话"""
    creds = _get_admin_credentials()
    username = creds.get("username")
    password = creds.get("password")

    if not username or not password:
        pytest.skip("ADMIN_USER or ADMIN_PASSWORD environment variable not set")

    response = auth_api.login(username, password)
    if not response.is_success:
        pytest.skip(f"Failed to get admin token: {response.status_code}")

    token = (
        response.body.get("data", {}).get("token") or
        response.body.get("token")
    )
    return token


@pytest.fixture
def api_with_auth(request_engine, admin_token):
    """带认证的API实例"""
    if not admin_token:
        pytest.skip("No admin token available")
    api = AuthAPI(request_engine, CONFIG.ENV)
    api.set_token(admin_token)
    return api


@pytest.fixture
def test_context(request_engine, data_driver):
    """测试上下文 fixture - 推荐使用"""
    ctx = TestContext(request_engine, data_driver)
    ctx.setup()
    yield ctx
    ctx.teardown()


# ---------------------------------------------------------------------------
# 数据生成
# ---------------------------------------------------------------------------

@pytest.fixture
def test_data():
    """测试数据生成器"""
    from utils.helpers import generate_random_string, generate_random_phone
    return {
        "random_string": generate_random_string,
        "random_phone": generate_random_phone,
        "timestamp": lambda: str(int(__import__('time').time()))
    }


# ---------------------------------------------------------------------------
# Mock API Server
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mock_api_server():
    """Mock API 服务器 - 会话级自动启停"""
    from testcases.mock_api import MockAPIServer
    server = MockAPIServer(host="localhost", port=19999)
    server.start()
    yield server
    server.stop()


# ---------------------------------------------------------------------------
# pytest 钩子
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "api: API接口测试")

    if CONFIG.DINGTALK_WEBHOOK:
        plugin = DingTalkPytestPlugin(CONFIG)
        config.pluginmanager.register(plugin)


def pytest_collection_modifyitems(config, items):
    """测试用例收集后处理"""
    for item in items:
        if hasattr(item, 'cls') and item.cls:
            doc = item.cls.__doc__ or item.cls.__name__
            allure.feature(doc)
