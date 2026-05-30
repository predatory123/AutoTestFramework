# 更新日志

## [1.0.0] - 2024-01-15

### ✨ 新增功能
- 高可用请求引擎（熔断器 + 指数退避重试）
- 多格式数据驱动（YAML/JSON/Excel/CSV）
- 钉钉机器人通知（支持签名验证）
- 多进程并行执行（pytest-xdist）
- Allure + pytest-html 双报告体系
- 多环境配置管理（dev/test/staging/prod）
- 异步批量请求处理器（压力测试）
- Mock服务支持

### 🔧 技术特性
- 连接池管理（HTTPAdapter）
- 敏感数据自动脱敏
- Token自动刷新机制
- 彩色日志输出
- 数据库连接池（MySQL/PostgreSQL/SQLite）
- JSONPath 数据提取
- JSON Schema 响应验证

### 📦 项目结构
- 模块化架构（config/core/utils/api/testcases）
- 插件化通知系统
- 完整的示例代码和文档
- Docker支持
- Jenkins CI/CD 配置

## [Unreleased]

### 🚧 计划功能
- [ ] 企业微信通知
- [ ] 飞书通知
- [ ] 邮件通知（SMTP）
- [ ] 接口录制生成用例
- [ ] Swagger文档导入
- [ ] 性能测试集成（Locust）
- [ ] 分布式执行（多机并行）
- [ ] Web管理界面
- [ ] 定时任务调度
- [ ] 历史趋势分析
