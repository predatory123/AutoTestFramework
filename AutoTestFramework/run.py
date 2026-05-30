#!/usr/bin/env python3
"""高可用接口自动化测试框架 - 主运行入口"""
import os
import sys
import argparse
import pytest
from pathlib import Path
from datetime import datetime
from config.settings import CONFIG
from hooks.dingtalk_notifier import DingTalkPytestPlugin, TestReportNotifier

def generate_report_name():
    """生成带时间戳的报告名称"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{timestamp}"

def setup_directories():
    """确保必要目录存在"""
    dirs = ['reports', 'logs', 'data/yaml', 'data/json', 'data/excel', 'screenshots']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_tests(args):
    """执行测试主函数"""
    setup_directories()

    report_name = generate_report_name()
    report_dir = CONFIG.REPORT_DIR / report_name
    report_dir.mkdir(parents=True, exist_ok=True)

    # pytest参数构建
    pytest_args = [
        "testcases/",  # 测试目录
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback
        f"--html={report_dir}/report.html",  # HTML报告
        "--self-contained-html",  # 独立HTML
        f"--alluredir={report_dir}/allure-results",  # Allure结果
        f"-n={args.workers or CONFIG.PARALLEL_WORKERS}",  # 并行执行
        "--dist=loadfile",  # 按文件分发
    ]

    # 添加过滤条件
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    if args.mark:
        pytest_args.extend(["-m", args.mark])
    if args.failfast:
        pytest_args.append("--exitfirst")
    if args.rerun:
        pytest_args.extend(["--reruns", str(args.rerun), "--reruns-delay", "1"])

    # 添加环境变量
    os.environ['TEST_ENV'] = args.env or CONFIG.ENV
    os.environ['REPORT_DIR'] = str(report_dir)

    print(f"🚀 启动测试 - 环境: {args.env or CONFIG.ENV}")
    print(f"📊 报告目录: {report_dir}")
    print(f"⚡ 并行工作线程: {args.workers or CONFIG.PARALLEL_WORKERS}")

    # 发送开始通知
    if args.dingtalk and CONFIG.DINGTALK_WEBHOOK:
        notifier = TestReportNotifier(CONFIG)
        notifier.notify_test_start(total_cases=100, env=args.env or CONFIG.ENV)

    # 执行测试
    exit_code = pytest.main(pytest_args)

    # 生成Allure报告（如果安装了allure）
    try:
        import subprocess
        allure_report = report_dir / "allure-report"
        subprocess.run([
            "allure", "generate", 
            f"{report_dir}/allure-results", 
            "-o", str(allure_report), 
            "--clean"
        ], check=False)
        print(f"📈 Allure报告: {allure_report}/index.html")
    except Exception as e:
        print(f"⚠️ 生成Allure报告失败: {e}")

    return exit_code

def main():
    parser = argparse.ArgumentParser(
        description="高可用接口自动化测试框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py -e dev                    # 开发环境运行
  python run.py -e test -n 8 --dingtalk   # 测试环境并行8线程+钉钉通知
  python run.py -m "smoke" -x             # 只运行冒烟测试，失败即停止
  python run.py -k "login" --rerun 3      # 运行包含login的用例，失败重试3次
        """
    )
    parser.add_argument("-e", "--env", 
                       choices=["dev", "test", "staging", "prod"],
                       help="测试环境")
    parser.add_argument("-n", "--workers", type=int,
                       help="并行工作线程数（默认: 4）")
    parser.add_argument("-k", "--keyword", 
                       help="只运行匹配关键字的用例")
    parser.add_argument("-m", "--mark", 
                       help="只运行指定标记的用例（如: smoke, regression）")
    parser.add_argument("-x", "--failfast", action="store_true",
                       help="遇到失败立即停止")
    parser.add_argument("--rerun", type=int, default=0,
                       help="失败重试次数（默认: 0）")
    parser.add_argument("--dingtalk", action="store_true",
                       help="启用钉钉通知（需配置webhook）")
    parser.add_argument("--no-report", action="store_true",
                       help="不生成报告（仅控制台输出）")

    args = parser.parse_args()

    try:
        exit_code = run_tests(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
