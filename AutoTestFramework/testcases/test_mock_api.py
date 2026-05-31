"""Mock API 测试套件 - 使用 TestContext + fixture 模式"""
import pytest
import allure
from typing import Dict


# ─── 共享 fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def auth_headers(request_engine, mock_api_server):
    """模块级认证头 - 供所有测试类共享"""
    resp = request_engine.post(
        f"{mock_api_server.base_url}/api/auth/login",
        data={"username": "admin", "password": "Admin@123"}
    )
    token = resp.body["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


# ─── 认证模块测试 ──────────────────────────────────────────────────────────────

@allure.feature("认证模块")
class TestAuth:
    """认证相关 API 测试"""

    @pytest.fixture
    def ctx(self, request_engine, data_driver):
        """每个测试独立的上下文"""
        from core.base_test import TestContext
        ctx = TestContext(request_engine, data_driver)
        yield ctx

    def test_login_success(self, ctx, mock_api_server):
        """AUTH-001: 正常登录-admin用户"""
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/auth/login",
                "body": {"username": "admin", "password": "Admin@123"}
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.code", 0]},
                {"contains": ["body.data.token", "mock_token"]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.body["code"] == 0
        assert "token" in response.body["data"]

    def test_login_wrong_password(self, ctx, mock_api_server):
        """AUTH-003: 登录失败-密码错误"""
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/auth/login",
                "body": {"username": "admin", "password": "wrong_password"}
            },
            "validate": [
                {"eq": ["status_code", 401]},
                {"eq": ["body.code", 401]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.status_code == 401

    def test_login_user_not_exists(self, ctx, mock_api_server):
        """AUTH-004: 登录失败-用户不存在"""
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/auth/login",
                "body": {"username": "nonexistent", "password": "anypass"}
            },
            "validate": [
                {"eq": ["status_code", 401]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.status_code == 401

    def test_login_missing_credentials(self, ctx, mock_api_server):
        """AUTH-005: 登录失败-缺少凭证"""
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/auth/login",
                "body": {"username": "", "password": ""}
            },
            "validate": [
                {"eq": ["status_code", 400]},
                {"eq": ["body.code", 400]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.status_code == 400

    def test_refresh_token(self, ctx, mock_api_server, auth_headers):
        """PERF-001: Token刷新"""
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/auth/refresh",
                "headers": auth_headers
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.code", 0]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.body["code"] == 0


# ─── 用户管理模块测试 ────────────────────────────────────────────────────────

@allure.feature("用户管理模块")
class TestUserManagement:
    """用户 CRUD API 测试"""

    @pytest.fixture
    def ctx(self, request_engine, data_driver):
        from core.base_test import TestContext
        ctx = TestContext(request_engine, data_driver)
        yield ctx

    def test_list_users(self, ctx, mock_api_server, auth_headers):
        """USER-001: 获取用户列表"""
        testcase = {
            "request": {
                "method": "GET",
                "url": f"{mock_api_server.base_url}/api/users",
                "headers": auth_headers
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.code", 0]},
                {"jsonpath": ["data.total", 2]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.body["data"]["total"] >= 2

    def test_get_user_detail(self, ctx, mock_api_server, auth_headers):
        """USER-002: 获取指定用户详情"""
        testcase = {
            "request": {
                "method": "GET",
                "url": f"{mock_api_server.base_url}/api/users/1",
                "headers": auth_headers
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.data.username", "admin"]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.body["data"]["username"] == "admin"

    def test_get_user_not_found(self, ctx, mock_api_server, auth_headers):
        """USER-003: 获取不存在的用户"""
        testcase = {
            "request": {
                "method": "GET",
                "url": f"{mock_api_server.base_url}/api/users/9999",
                "headers": auth_headers
            },
            "validate": [
                {"eq": ["status_code", 404]},
                {"eq": ["body.code", 404]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.status_code == 404

    def test_create_user(self, ctx, mock_api_server, auth_headers):
        """USER-004: 创建新用户"""
        import time
        unique_name = f"newuser_{int(time.time())}"
        testcase = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/users",
                "headers": auth_headers,
                "body": {
                    "username": unique_name,
                    "email": f"{unique_name}@example.com",
                    "role": "tester"
                }
            },
            "validate": [
                {"eq": ["status_code", 201]},
                {"eq": ["body.code", 0]},
                {"eq": ["body.data.username", unique_name]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.status_code == 201
        assert response.body["data"]["username"] == unique_name

    def test_update_user(self, ctx, mock_api_server, auth_headers):
        """USER-005: 更新用户信息"""
        testcase = {
            "request": {
                "method": "PUT",
                "url": f"{mock_api_server.base_url}/api/users/1",
                "headers": auth_headers,
                "body": {"email": "updated@example.com", "role": "superadmin"}
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.data.email", "updated@example.com"]}
            ]
        }
        response = ctx.run_api_test(testcase)
        assert response.body["data"]["email"] == "updated@example.com"

    def test_delete_user(self, ctx, mock_api_server, auth_headers):
        """USER-006: 删除用户"""
        create_case = {
            "request": {
                "method": "POST",
                "url": f"{mock_api_server.base_url}/api/users",
                "headers": auth_headers,
                "body": {"username": "delete_me", "email": "delete@example.com"}
            }
        }
        create_resp = ctx.run_api_test(create_case)
        user_id = create_resp.body["data"]["id"]

        delete_case = {
            "request": {
                "method": "DELETE",
                "url": f"{mock_api_server.base_url}/api/users/{user_id}",
                "headers": auth_headers
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"eq": ["body.code", 0]}
            ]
        }
        response = ctx.run_api_test(delete_case)
        assert response.status_code == 200


# ─── 数据驱动测试 ────────────────────────────────────────────────────────────

@allure.feature("数据驱动测试")
class TestDataDriven:
    """从 YAML 文件加载数据进行参数化测试"""

    @pytest.fixture
    def ctx(self, request_engine, data_driver):
        from core.base_test import TestContext
        ctx = TestContext(request_engine, data_driver)
        yield ctx

    @pytest.mark.parametrize("test_data", [
        {"id": "AUTH-001", "method": "POST", "path": "/api/auth/login",
         "body": {"username": "admin", "password": "Admin@123"}, "expect_code": 200},
        {"id": "AUTH-003", "method": "POST", "path": "/api/auth/login",
         "body": {"username": "admin", "password": "badpass"}, "expect_code": 401},
        {"id": "USER-001", "method": "GET", "path": "/api/users",
         "body": None, "expect_code": 200, "need_auth": True},
    ])
    def test_from_data(self, ctx, mock_api_server, test_data, request_engine):
        """从参数化数据运行测试"""
        headers = {}
        if test_data.get("need_auth"):
            login_resp = ctx.request.post(
                f"{mock_api_server.base_url}/api/auth/login",
                data={"username": "admin", "password": "Admin@123"}
            )
            token = login_resp.body.get("data", {}).get("token", "")
            headers = {"Authorization": f"Bearer {token}"}

        testcase = {
            "request": {
                "method": test_data["method"],
                "url": f"{mock_api_server.base_url}{test_data['path']}",
                "headers": headers,
                "body": test_data["body"]
            },
            "validate": [
                {"eq": ["status_code", test_data["expect_code"]]}
            ]
        }
        with allure.step(f"执行: {test_data['id']}"):
            response = ctx.run_api_test(testcase)
            assert response.status_code == test_data["expect_code"]
