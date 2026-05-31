"""多环境配置管理"""

ENVIRONMENTS = {
    "dev": {
        "base_url": "https://api-dev.example.com",
        "db_host": "localhost",
        "db_port": 3306,
        "redis_host": "localhost",
        "timeout": 30
    },
    "test": {
        "base_url": "https://api-test.example.com",
        "db_host": "test-db.example.com",
        "db_port": 3306,
        "redis_host": "test-redis.example.com",
        "timeout": 30
    },
    "staging": {
        "base_url": "https://api-staging.example.com",
        "db_host": "staging-db.example.com",
        "db_port": 3306,
        "redis_host": "staging-redis.example.com",
        "timeout": 60
    },
    "prod": {
        "base_url": "https://api.example.com",
        "db_host": "prod-db.example.com",
        "db_port": 3306,
        "redis_host": "prod-redis.example.com",
        "timeout": 60
    },
    "local": {
        "base_url": "http://localhost:8080",
        "db_host": "localhost",
        "db_port": 3306,
        "redis_host": "localhost",
        "timeout": 30
    }
}

def get_env_config(env_name: str) -> dict:
    """获取指定环境配置"""
    return ENVIRONMENTS.get(env_name, ENVIRONMENTS["dev"])
