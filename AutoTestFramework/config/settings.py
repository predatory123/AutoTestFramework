import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class TestConfig:
    """测试配置数据中心"""
    # 基础路径
    BASE_DIR: Path = Path(__file__).parent.parent

    # 运行配置
    ENV: str = os.getenv("TEST_ENV", "dev")
    PARALLEL_WORKERS: int = int(os.getenv("WORKERS", "4"))
    RETRY_TIMES: int = int(os.getenv("RETRY_TIMES", "3"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))

    # 报告配置
    REPORT_TITLE: str = "接口自动化测试报告"
    REPORT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent / "reports")

    # 钉钉配置
    DINGTALK_WEBHOOK: str = os.getenv("DING_WEBHOOK", "")
    DINGTALK_SECRET: str = os.getenv("DING_SECRET", "")
    DING_AT_MOBILES: List[str] = field(default_factory=list)

    # 数据库配置
    DB_CONFIG: Dict = field(default_factory=dict)

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    def __post_init__(self):
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)

# 全局配置实例
CONFIG = TestConfig()
