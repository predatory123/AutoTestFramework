"""通用辅助函数"""
import re
import json
import random
import string
from typing import Any, Dict, List
from datetime import datetime, timedelta

def generate_random_string(length: int = 8, chars: str = string.ascii_letters + string.digits) -> str:
    """生成随机字符串"""
    return ''.join(random.choice(chars) for _ in range(length))

def generate_random_phone() -> str:
    """生成随机手机号"""
    prefixes = ['138', '139', '150', '151', '152', '157', '158', '159', '182', '183', '187', '188']
    return random.choice(prefixes) + ''.join(random.choice('0123456789') for _ in range(8))

def generate_random_email() -> str:
    """生成随机邮箱"""
    domains = ['gmail.com', 'qq.com', '163.com', 'outlook.com', 'test.com']
    return f"{generate_random_string(8)}@{random.choice(domains)}"

def mask_sensitive_data(data: Any, sensitive_keys: List[str] = None) -> Any:
    """脱敏敏感数据"""
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'secret', 'key', 'authorization', 'cookie']

    if isinstance(data, dict):
        return {
            k: '***' if any(sk in k.lower() for sk in sensitive_keys) else mask_sensitive_data(v, sensitive_keys)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_keys) for item in data]
    return data

def extract_json_from_string(text: str) -> Dict:
    """从字符串中提取JSON"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试从文本中提取JSON
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    return {}

def format_datetime(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)

def get_timestamp(ms: bool = False) -> int:
    """获取当前时间戳"""
    now = datetime.now()
    if ms:
        return int(now.timestamp() * 1000)
    return int(now.timestamp())

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并字典"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
