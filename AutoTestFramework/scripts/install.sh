#!/bin/bash
# 安装脚本 - 适用于Linux/macOS

echo "🚀 开始安装接口自动化测试框架..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python版本: $python_version"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 创建必要目录
echo "📁 创建项目目录..."
mkdir -p reports logs data/yaml data/json data/excel screenshots

# 复制环境变量模板
echo "⚙️ 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建.env文件，请编辑配置"
fi

echo ""
echo "✨ 安装完成！"
echo ""
echo "使用方法:"
echo "  1. 编辑 .env 文件配置环境变量"
echo "  2. 激活虚拟环境: source venv/bin/activate"
echo "  3. 运行测试: python run.py -e dev"
echo ""
