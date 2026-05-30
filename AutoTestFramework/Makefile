.PHONY: help install test clean report docker

help:
	@echo "🚀 高可用接口自动化测试框架"
	@echo ""
	@echo "可用命令:"
	@echo "  make install    - 安装依赖"
	@echo "  make test       - 运行测试(dev环境)"
	@echo "  make test-prod  - 运行测试(prod环境)"
	@echo "  make report     - 查看Allure报告"
	@echo "  make clean      - 清理临时文件"
	@echo "  make docker     - Docker构建和运行"
	@echo ""

install:
	pip install -r requirements.txt

test:
	python run.py -e dev

test-prod:
	python run.py -e prod --dingtalk

test-parallel:
	python run.py -e dev -n 8

report:
	allure serve reports/*/allure-results

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf reports/* logs/*

docker:
	docker-compose up --build

lint:
	flake8 core/ utils/ api/ testcases/
	black --check core/ utils/ api/ testcases/

format:
	black core/ utils/ api/ testcases/
