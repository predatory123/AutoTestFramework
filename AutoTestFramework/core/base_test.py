"""测试基类 - 提供通用测试能力（不依赖继承）"""
import json
import allure
import jsonschema
from typing import Dict, Any, List, Callable, Optional
from jsonpath_ng import parse as jsonpath_parse
from .request_engine import RequestEngine, Response, Method
from .data_driver import DataDriver


class Validator:
    """高级断言验证器"""

    @staticmethod
    def validate(response: Response, rules: List[Dict]):
        """执行多维度验证"""
        for rule in rules:
            for method_name, params in rule.items():
                validator = getattr(Validator, f"_validate_{method_name}", None)
                if validator:
                    validator(response, params)
                else:
                    raise ValueError(f"Unknown validation method: {method_name}")

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
        with open(schema_path, encoding='utf-8') as f:
            schema = json.load(f)
        jsonschema.validate(instance=response.body, schema=schema)

    @staticmethod
    def _validate_jsonpath(response: Response, params: List):
        """JSONPath验证 - jsonpath-ng 要求 $ 前缀"""
        path, expected = params
        # jsonpath-ng requires $ prefix for absolute paths
        jsonpath_expr = jsonpath_parse(path if path.startswith("$") else f"$.{path}")
        matches = [match.value for match in jsonpath_expr.find(response.body)]
        assert matches, f"JSONPath {path} found no matches in response body"
        assert expected in matches or matches[0] == expected

    @staticmethod
    def _validate_response_time(response: Response, max_time: int):
        """响应时间验证"""
        assert response.response_time < max_time, \
            f"Response time {response.response_time}ms exceeds {max_time}ms"

    @staticmethod
    def _extract_value(response: Response, key: str) -> Any:
        """从响应中提取值，支持 body.xxx.yyy 嵌套路径"""
        if key == "status_code":
            return response.status_code
        if key == "body":
            return response.body
        if key.startswith("headers."):
            return response.headers.get(key.replace("headers.", ""))
        if key.startswith("body."):
            parts = key[5:].split(".")  # 去掉 "body." 前缀
            value: Any = response.body
            for part in parts:
                if not isinstance(value, dict):
                    return None
                value = value.get(part)
                if value is None:
                    return None
            return value
        return None


class TestContext:
    """测试上下文 - 替代继承模式，提供给 fixture 使用"""

    def __init__(self, request_engine: RequestEngine, data_driver: DataDriver):
        self.request = request_engine
        self.data = data_driver
        self.validator = Validator()
        self._setup_done = False
        self._teardown_done = False

    def setup(self):
        """初始化，可被子类覆盖"""
        pass

    def teardown(self):
        """清理，可被子类覆盖"""
        pass

    def execute_step(self, step_name: str, action: Callable, **kwargs) -> Any:
        """执行带Allure报告的测试步骤"""
        with allure.step(step_name):
            try:
                result = action(**kwargs)
                body = result.body if hasattr(result, 'body') else result
                allure.attach(
                    json.dumps(body, ensure_ascii=False),
                    name="Response",
                    attachment_type=allure.attachment_type.JSON
                )
                return result
            except Exception as e:
                allure.attach(str(e), name="Error", attachment_type=allure.attachment_type.TEXT)
                raise

    def run_api_test(self, testcase: Dict) -> Response:
        """执行单个API测试用例"""
        req = testcase['request']
        response = self.request.request(
            method=Method[req.get('method', 'GET').upper()],
            url=req.get('url'),
            headers=req.get('headers'),
            data=req.get('body'),
            params=req.get('params')
        )
        if 'validate' in testcase:
            self.validator.validate(response, testcase['validate'])
        return response


# 为了向后兼容保留 BaseTestCase，但标记为废弃
class BaseTestCase(TestContext):
    """测试基类 [已废弃，请使用 TestContext + fixture]

    旧模式（继承）:
        class MyTest(BaseTestCase):
            def _setup(self):
                ...

    新模式（推荐）:
        @pytest.fixture
        def tc(request_engine, data_driver):
            ctx = TestContext(request_engine, data_driver)
            ctx.setup()
            yield ctx
            ctx.teardown()
    """

    def __init__(self, request_engine: RequestEngine, data_driver: DataDriver):
        super().__init__(request_engine, data_driver)

    def _setup(self):
        """子类可覆盖的初始化方法 - 已废弃"""
        pass

    def _teardown(self):
        """子类可覆盖的清理方法 - 已废弃"""
        pass
