import pytest
import allure
import jsonschema
from typing import Dict, Any, List, Callable
from jsonpath_ng import parse as jsonpath_parse
from .request_engine import RequestEngine, Response
from .data_driver import DataDriver

class Validator:
    """高级断言验证器"""

    @staticmethod
    def validate(response: Response, rules: List[Dict]):
        """执行多维度验证"""
        for rule in rules:
            for method, params in rule.items():
                validator = getattr(Validator, f"_validate_{method}", None)
                if validator:
                    validator(response, params)
                else:
                    raise ValueError(f"Unknown validation method: {method}")

    @staticmethod
    def _validate_eq(response: Response, params: List):
        """等于验证"""
        actual = Validator._extract_value(response, params[0])
        expected = params[1]
        assert actual == expected, f"Expected {expected}, got {actual}"

    @staticmethod
    def _validate_contains(response: Response, params: List):
        """包含验证"""
        actual = Validator._extract_value(response, params[0])
        expected = params[1]
        assert expected in str(actual), f"Expected '{expected}' in '{actual}'"

    @staticmethod
    def _validate_schema(response: Response, schema_path: str):
        """JSON Schema验证"""
        with open(schema_path) as f:
            schema = json.load(f)
        jsonschema.validate(instance=response.body, schema=schema)

    @staticmethod
    def _validate_jsonpath(response: Response, params: List):
        """JSONPath验证"""
        path, expected = params
        jsonpath_expr = jsonpath_parse(path)
        matches = [match.value for match in jsonpath_expr.find(response.body)]
        assert matches, f"JSONPath {path} found no matches"
        assert expected in matches or matches[0] == expected

    @staticmethod
    def _validate_response_time(response: Response, max_time: int):
        """响应时间验证"""
        assert response.response_time < max_time, \
            f"Response time {response.response_time}ms exceeds {max_time}ms"

    @staticmethod
    def _extract_value(response: Response, key: str):
        """从响应中提取值"""
        if key == "status_code":
            return response.status_code
        if key == "body":
            return response.body
        if key.startswith("body."):
            path = key.replace("body.", "")
            return response.body.get(path) if isinstance(response.body, dict) else None
        if key.startswith("headers."):
            return response.headers.get(key.replace("headers.", ""))
        return None

class BaseTestCase:
    """测试基类 - 提供通用能力"""

    @pytest.fixture(autouse=True)
    def setup_test(self, request_engine, data_driver):
        self.request = request_engine
        self.data = data_driver
        self.validator = Validator()
        self._setup()
        yield
        self._teardown()

    def _setup(self):
        """子类可覆盖的初始化方法"""
        pass

    def _teardown(self):
        """子类可覆盖的清理方法"""
        pass

    def execute_step(self, step_name: str, action: Callable, **kwargs):
        """执行带Allure报告的测试步骤"""
        with allure.step(step_name):
            try:
                result = action(**kwargs)
                allure.attach(
                    str(result.body) if hasattr(result, 'body') else str(result),
                    name="Response",
                    attachment_type=allure.attachment_type.JSON
                )
                return result
            except Exception as e:
                allure.attach(str(e), name="Error", attachment_type=allure.attachment_type.TEXT)
                raise

    def run_api_test(self, testcase: Dict):
        """执行单个API测试用例"""
        req = testcase['request']

        # 发送请求
        response = self.request.request(
            method=req.get('method'),
            url=req.get('url'),
            headers=req.get('headers'),
            data=req.get('body'),
            params=req.get('params')
        )

        # 执行验证
        if 'validate' in testcase:
            self.validator.validate(response, testcase['validate'])

        return response
