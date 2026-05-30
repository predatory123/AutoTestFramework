FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p reports logs data screenshots

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TEST_ENV=dev

# 默认命令
CMD ["python", "run.py", "-e", "dev"]
