#!/bin/bash
# Docker运行脚本

echo "🐳 使用Docker运行测试框架..."

# 构建镜像
docker build -t auto-test-framework .

# 运行容器
docker run --rm \
    -v $(pwd)/reports:/app/reports \
    -v $(pwd)/logs:/app/logs \
    -e TEST_ENV=${TEST_ENV:-dev} \
    -e DING_WEBHOOK=$DING_WEBHOOK \
    -e DING_SECRET=$DING_SECRET \
    auto-test-framework \
    python run.py -e ${TEST_ENV:-dev} ${@:1}

echo "✅ Docker运行完成"
