@echo off
chcp 65001 >nul
echo 🚀 开始安装接口自动化测试框架...

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    exit /b 1
)

echo 📦 创建虚拟环境...
python -m venv venv

echo 🔌 激活虚拟环境...
call venv\Scripts\activate.bat

echo ⬆️ 升级pip...
python -m pip install --upgrade pip

echo 📥 安装依赖包...
pip install -r requirements.txt

echo 📁 创建项目目录...
if not exist reports mkdir reports
if not exist logs mkdir logs
if not exist data\yaml mkdir data\yaml
if not exist data\json mkdir data\json
if not exist data\excel mkdir data\excel
if not exist screenshots mkdir screenshots

echo ⚙️ 配置环境变量...
if not exist .env (
    copy .env.example .env
    echo ✅ 已创建.env文件，请编辑配置
)

echo.
echo ✨ 安装完成！
echo.
echo 使用方法:
echo   1. 编辑 .env 文件配置环境变量
echo   2. 激活虚拟环境: venv\Scripts\activate.bat
echo   3. 运行测试: python run.py -e dev
echo.
pause
