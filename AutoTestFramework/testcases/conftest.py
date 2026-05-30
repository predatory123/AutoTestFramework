"""pytest全局配置和fixtures"""
import pytest
import allure
from typing import Dict, Any
from core.request_engine import RequestEngine
from core.data_driver import DataDriver
from api.base_api import AuthAPI, UserAPI
from config.settings import CONFIG
from hooks.dingtalk_notifier import DingTalkPytestPlugin

# 全局资源管理
@pytest.fixture(scope="session")
def request_engine():
    """全局请求引擎 - 会话级"""
    engine = RequestEngine(CONFIG.__dict__)
    yield engine
    # 清理会话
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

@pytest.fixture(scope="session")
def admin_token(auth_api):
    """管理员令牌fixture"""
    # 这里应该使用测试账号登录
    # 实际项目中应从环境变量或安全配置中读取
    response = auth_api.login("admin", "Admin@123")
    if response.is_success:
        return response.body.get("data", {}).get("token")
    pytest.skip("Failed to get admin token")

@pytest.fixture(scope="function")
def api_with_auth(request_engine, admin_token):
    """带认证的API实例"""
    api = AuthAPI(request_engine, CONFIG.ENV)
    api.set_token(admin_token)
    return api

@pytest.fixture(scope="function")
def test_data():
    """测试数据生成器"""
    from utils.helpers import generate_random_string, generate_random_phone
    return {
        "random_string": generate_random_string,
        "random_phone": generate_random_phone,
        "timestamp": lambda: str(int(__import__('time').time()))
    }

# pytest钩子配置
def pytest_configure(config):
    """pytest配置钩子"""
    # 注册自定义标记
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "api: API接口测试")

    # 如果启用了钉钉通知，注册插件
    if CONFIG.DINGTALK_WEBHOOK:
        plugin = DingTalkPytestPlugin(CONFIG)
        config.pluginmanager.register(plugin)

def pytest_collection_modifyitems(config, items):
    """测试用例收集后处理"""
    # 自动添加allure标签
    for item in items:
        # 根据测试函数名自动添加feature
        if hasattr(item, 'cls'):
            allure.feature(item.cls.__doc__ or item.cls.__name__)

def pytest_runtest_setup(item):
    """测试用例执行前设置"""
    # 可以在这里添加用例级别的预处理
    pass

def pytest_runtest_teardown(item, nextitem):
    """测试用例执行后清理"""
    # 可以在这里添加用例级别的清理
    pass
