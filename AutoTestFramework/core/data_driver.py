import yaml
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Iterator, Callable
import pytest

class DataDriver:
    """多源数据驱动引擎 - 支持YAML/JSON/Excel/数据库"""

    SUPPORTED_FORMATS = ['.yaml', '.yml', '.json', '.xlsx', '.xls', '.csv']

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._cache = {}

    def load_yaml(self, file_path: str) -> Any:
        """加载YAML文件"""
        path = self.data_dir / file_path
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_json(self, file_path: str) -> Any:
        """加载JSON文件"""
        path = self.data_dir / file_path
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_excel(self, file_path: str, sheet_name: str = None) -> List[Dict]:
        """加载Excel文件"""
        path = self.data_dir / file_path
        df = pd.read_excel(path, sheet_name=sheet_name)
        return df.to_dict('records')

    def load_csv(self, file_path: str) -> List[Dict]:
        """加载CSV文件"""
        path = self.data_dir / file_path
        df = pd.read_csv(path)
        return df.to_dict('records')

    def load(self, file_path: str, **kwargs) -> Any:
        """智能加载 - 根据扩展名自动选择解析器"""
        suffix = Path(file_path).suffix.lower()

        loaders = {
            '.yaml': self.load_yaml,
            '.yml': self.load_yaml,
            '.json': self.load_json,
            '.xlsx': lambda p: self.load_excel(p, **kwargs),
            '.xls': lambda p: self.load_excel(p, **kwargs),
            '.csv': self.load_csv
        }

        if suffix not in loaders:
            raise ValueError(f"Unsupported format: {suffix}")

        # 缓存检查
        cache_key = f"{file_path}:{kwargs}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = loaders[suffix](file_path)
        self._cache[cache_key] = data
        return data

    def parametrize(self, file_path: str, filter_func: Callable = None):
        """pytest参数化装饰器"""
        data = self.load(file_path)

        if isinstance(data, dict) and 'testcases' in data:
            data = data['testcases']

        if filter_func:
            data = [d for d in data if filter_func(d)]

        return pytest.mark.parametrize("test_data", data)
