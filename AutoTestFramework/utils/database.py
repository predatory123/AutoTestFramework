"""数据库操作工具 - 支持MySQL/PostgreSQL/SQLite"""
import pymysql
import psycopg2
import sqlite3
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, db_type: str = "mysql", **kwargs):
        self.db_type = db_type.lower()
        self.config = kwargs
        self._connection = None

    def connect(self):
        """建立数据库连接"""
        try:
            if self.db_type == "mysql":
                self._connection = pymysql.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 3306),
                    user=self.config.get('user'),
                    password=self.config.get('password'),
                    database=self.config.get('database'),
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
            elif self.db_type == "postgresql":
                self._connection = psycopg2.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 5432),
                    user=self.config.get('user'),
                    password=self.config.get('password'),
                    database=self.config.get('database')
                )
            elif self.db_type == "sqlite":
                self._connection = sqlite3.connect(
                    self.config.get('database', 'test.db')
                )
                self._connection.row_factory = sqlite3.Row
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            logger.info(f"Connected to {self.db_type} database")
            return self._connection

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    @contextmanager
    def cursor(self):
        """上下文管理器获取游标"""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()

    def execute(self, sql: str, params: tuple = None) -> List[Dict]:
        """执行SQL查询"""
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            if sql.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return []

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行SQL"""
        with self.cursor() as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount

    def close(self):
        """关闭连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
