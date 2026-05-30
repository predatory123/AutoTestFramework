# 🚀 高可用接口自动化测试框架

基于 **Python + Pytest + Allure + YAML + 钉钉通知** 的企业级接口自动化测试解决方案。

## ✨ 核心特性

- **🔄 高可用设计**：熔断器模式 + 指数退避重试 + 连接池管理
- **⚡ 高性能执行**：多进程并行 + 异步批量请求 + 智能负载分发
- **📊 多维度报告**：pytest-html + Allure 双报告体系，支持历史趋势
- **🔔 即时通知**：钉钉机器人集成（支持签名验证），实时推送测试结果
- **📁 数据驱动**：YAML/JSON/Excel/CSV 多格式数据源支持
- **🛡️ 安全机制**：敏感数据自动脱敏 + Token 自动刷新 + 环境隔离

## 🏗️ 项目结构

```
AutoTestFramework/
├── 📁 config/                    # 配置管理
│   ├── settings.py              # 全局配置（数据类）
│   ├── environments.py          # 多环境配置
│   └── pytest.ini               # pytest 配置
├── 📁 core/                      # 核心引擎
│   ├── request_engine.py        # HTTP请求引擎（熔断+重试）
│   ├── data_driver.py           # 数据驱动引擎
│   ├── base_test.py             # 测试基类（Allure集成）
│   └── retry_mechanism.py       # 重试与熔断策略
├── 📁 utils/                     # 工具库
│   ├── logger.py                # 彩色日志管理
│   ├── database.py              # 数据库连接池
│   └── helpers.py               # 通用辅助函数
├── 📁 api/                       # 接口封装层
│   └── base_api.py              # 业务API基类（PO模式）
├── 📁 testcases/                 # 测试用例
│   ├── conftest.py              # pytest fixtures
│   └── test_example.py          # 示例用例
├── 📁 hooks/                     # 钩子函数
│   └── dingtalk_notifier.py     # 钉钉通知（pytest插件）
├── 📁 middleware/                # 中间件
│   ├── auth_handler.py          # 认证处理器
│   └── mock_server.py           # Mock服务
├── 📁 data/                      # 测试数据
│   ├── yaml/                    # YAML格式用例
│   ├── json/                    # JSON格式数据
│   └── excel/                   # Excel格式数据
├── 📁 reports/                   # 测试报告输出
├── run.py                        # 主运行入口
├── requirements.txt              # 依赖管理
└── .env                          # 环境变量配置
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd AutoTestFramework

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env`，并填写实际配置：

```bash
# 测试环境: dev/test/staging/prod
TEST_ENV=dev

# 钉钉机器人配置（可选）
# 获取方式：https://open.dingtalk.com/document/robots/custom-robot-access
DING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=your_token
DING_SECRET=your_secret_here

# 执行配置
WORKERS=4              # 并行线程数
RETRY_TIMES=3          # 失败重试次数
TIMEOUT=30             # 请求超时时间
```

### 3. 编写测试用例

**方式一：Python代码编写**

```python
# testcases/test_auth.py
import allure
from core.base_test import BaseTestCase

@allure.feature("用户认证")
class TestAuth(BaseTestCase):

    @allure.title("正常登录测试")
    def test_login_success(self):
        testcase = {
            "id": "AUTH-001",
            "request": {
                "method": "POST",
                "url": "https://api.example.com/login",
                "body": {"username": "admin", "password": "Admin@123"}
            },
            "validate": [
                {"eq": ["status_code", 200]},
                {"contains": ["body.message", "success"]}
            ]
        }
        response = self.run_api_test(testcase)
        assert response.is_success
```

**方式二：YAML数据驱动**

```yaml
# data/yaml/test_login.yaml
testcases:
  - id: TC001
    name: "正常登录"
    priority: high
    request:
      method: POST
      url: https://api.example.com/login
      body:
        username: "admin"
        password: "Admin@123"
    validate:
      - eq: [status_code, 200]
      - schema: "schemas/login_response.json"
```

### 4. 执行测试

```bash
# 基础运行（开发环境）
python run.py -e dev

# 并行8线程 + 钉钉通知
python run.py -e test -n 8 --dingtalk

# 只运行冒烟测试，失败即停止
python run.py -m "smoke" -x

# 运行包含login的用例，失败重试3次
python run.py -k "login" --rerun 3

# 查看所有选项
python run.py --help
```

## 📊 测试报告

### 本地查看

```bash
# 生成并打开Allure报告
allure serve reports/report_20240115_143022/allure-results

# 或生成静态HTML报告
allure generate reports/report_20240115_143022/allure-results -o allure-report --clean
```

### 钉钉通知效果

测试完成后自动发送钉钉消息：

```
✅ 接口自动化测试完成

| 指标 | 数值 |
|------|------|
| 总用例数 | 100 |
| ✅ 通过 | 95 |
| ❌ 失败 | 5 |
| 📊 成功率 | 95.0% |
| ⏱️ 耗时 | 45.2s |

[查看完整报告] (按钮)
```

## 🔧 高级功能

### 1. 熔断器配置

```python
from core.request_engine import RequestEngine

# 自定义熔断阈值
engine = RequestEngine({
    'circuit_failure_threshold': 5,    # 5次失败开启熔断
    'circuit_recovery_timeout': 60      # 60秒后尝试恢复
})
```

### 2. 并发压力测试

```python
from core.request_engine import AsyncBatchProcessor

processor = AsyncBatchProcessor(engine)
requests = [{"method": "GET", "url": "https://api.example.com/data"} for _ in range(100)]
results = asyncio.run(processor.batch_request(requests, max_concurrent=20))
```

### 3. 数据库断言

```python
def test_with_db_assertion(self):
    # 执行API
    response = self.api.create_user({"name": "test"})

    # 数据库验证
    db_result = self.db.execute(
        "SELECT * FROM users WHERE name = %s", 
        ("test",)
    )
    assert len(db_result) == 1
```

### 4. Mock服务

```python
from middleware.mock_server import MockServer

with MockServer(port=9999) as mock:
    mock.add_route("GET", "/api/test", status=200, body={"msg": "ok"})
    # 执行测试...
```

## 📝 配置详解

### 多环境配置

在 `config/environments.py` 中定义环境：

```python
ENVIRONMENTS = {
    "dev": {
        "base_url": "https://api-dev.example.com",
        "db_host": "localhost",
        "timeout": 30
    },
    "prod": {
        "base_url": "https://api.example.com",
        "db_host": "prod-db.example.com",
        "timeout": 60
    }
}
```

### pytest.ini 配置

```ini
[pytest]
testpaths = testcases
python_files = test_*.py
addopts = -v --tb=short --strict-markers
markers =
    smoke: 冒烟测试
    regression: 回归测试
    performance: 性能测试
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

[MIT](LICENSE) © 2024 AutoTest Framework Team

## 📞 技术支持

- 📧 邮箱：support@example.com
- 💬 钉钉群：xxxx
- 📖 文档：https://your-docs-site.com

---

**如果本项目对您有帮助，请点亮 ⭐ Star 支持我们！**
