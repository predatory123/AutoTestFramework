"""日志管理模块 - 支持控制台和文件双输出"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config.settings import CONFIG

class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logger(name: str = "AutoTest", log_dir: str = "logs") -> logging.Logger:
    """配置并返回logger实例"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, CONFIG.LOG_LEVEL))

    if logger.handlers:
        return logger

    # 确保日志目录存在
    log_path = CONFIG.BASE_DIR / log_dir
    log_path.mkdir(exist_ok=True)

    # 控制台处理器 - 带颜色
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(CONFIG.LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 自动轮转
    file_handler = RotatingFileHandler(
        log_path / "test.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(CONFIG.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# 全局logger实例
LOGGER = setup_logger()
