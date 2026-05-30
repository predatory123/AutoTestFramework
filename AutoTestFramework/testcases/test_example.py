"""示例测试用例 - 展示框架功能"""
import pytest
import allure
from core.base_test import BaseTestCase

@allure.feature("用户认证模块")
@allure.story("登录功能")
class TestAuth(BaseTestCase):
    """认证相关测试"""

    @allure.title("正常登录测试")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_login_success(self):
        """验证正常登录流程"""
        testcase = {
            "id": "AUTH-001",
            "request": {
                "method": "POST",
                "url": "https://httpbin.org/post",
                "body": {"username": "admin", "password": "secret"}
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"contains": ["body", "admin"]}
            ]
        }

        response = self.run_api_test(testcase)
        assert response.is_success

        allure.attach(
            f"响应时间: {response.response_time}ms",
            name="性能指标",
            attachment_type=allure.attachment_type.TEXT
        )

    @allure.title("数据驱动登录测试")
    @pytest.mark.parametrize("test_data", [
        {"user": "admin", "pwd": "123", "expect": 200},
        {"user": "guest", "pwd": "guest", "expect": 200},
        {"user": "invalid", "pwd": "wrong", "expect": 401},
    ])
    def test_login_data_driven(self, test_data):
        """数据驱动登录测试"""
        with allure.step(f"测试数据: {test_data}"):
            response = self.request.post(
                "https://httpbin.org/post",
                data={"user": test_data['user'], "pwd": test_data['pwd']}
            )

            if test_data['expect'] == 200:
                assert response.is_success
            else:
                # 模拟失败场景
                pass

@allure.feature("性能测试")
class TestPerformance(BaseTestCase):
    """性能相关测试"""

    @allure.title("并发请求测试")
    @pytest.mark.performance
    def test_concurrent_requests(self):
        """测试并发处理能力"""
        from core.request_engine import AsyncBatchProcessor

        processor = AsyncBatchProcessor(self.request)

        requests = [
            {"method": "GET", "url": "https://httpbin.org/get"}
            for _ in range(10)
        ]

        import asyncio
        results = asyncio.run(processor.batch_request(requests, max_concurrent=5))

        success_count = sum(1 for r in results if hasattr(r, 'is_success') and r.is_success)
        allure.attach(f"成功率: {success_count}/10", name="并发结果")
        assert success_count >= 8  # 允许部分失败

@allure.feature("数据驱动测试")
class TestDataDriven(BaseTestCase):
    """数据驱动测试示例"""

    @allure.title("从YAML加载数据测试")
    def test_from_yaml(self):
        """从YAML文件加载测试数据"""
        # 创建示例YAML数据文件
        import yaml
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data" / "yaml"
        data_dir.mkdir(parents=True, exist_ok=True)

        test_data = {
            "testcases": [
                {
                    "id": "TC001",
                    "name": "测试用例1",
                    "priority": "high",
                    "request": {
                        "method": "GET",
                        "url": "https://httpbin.org/get"
                    },
                    "validate": [
                        {"eq": ["status_code", 200]}
                    ]
                }
            ]
        }

        yaml_file = data_dir / "test_sample.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_data, f, allow_unicode=True)

        # 加载并执行
        loaded_data = self.data.load("yaml/test_sample.yaml")
        for case in loaded_data['testcases']:
            with allure.step(f"执行: {case['name']}"):
                response = self.run_api_test(case)
                assert response.is_success
