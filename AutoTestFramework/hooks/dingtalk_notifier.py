import requests
import json
import hmac
import hashlib
import base64
import urllib.parse
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DingTalkNotifier:
    """钉钉机器人通知器 - 支持签名安全验证

    签名算法：timestamp + "\n" + 密钥作为签名字符串，使用HmacSHA256算法计算签名，
    然后进行Base64 encode，最后再进行urlEncode [^2^][^6^]
    """

    def __init__(self, webhook: str, secret: Optional[str] = None):
        self.webhook = webhook
        self.secret = secret

    def _generate_sign(self, timestamp: str) -> str:
        """生成钉钉签名"""
        if not self.secret:
            return ""

        # 签名字符串格式：timestamp + "\n" + secret [^6^]
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        secret_enc = self.secret.encode('utf-8')

        # 使用HmacSHA256算法计算签名 [^2^]
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        # Base64 encode后进行urlEncode [^2^]
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    def _send(self, payload: Dict) -> bool:
        """发送消息核心方法"""
        timestamp = str(round(time.time() * 1000))
        sign = self._generate_sign(timestamp)

        # 构造带签名的URL [^13^]
        url = f"{self.webhook}&timestamp={timestamp}&sign={sign}" if self.secret else self.webhook

        headers = {"Content-Type": "application/json; charset=utf-8"}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("DingTalk message sent successfully")
                return True
            else:
                logger.error(f"DingTalk API error: {result}")
                return False
        except Exception as e:
            logger.error(f"Failed to send DingTalk message: {e}")
            return False

    def send_text(self, content: str, at_mobiles: List[str] = None, is_at_all: bool = False):
        """发送文本消息"""
        payload = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        return self._send(payload)

    def send_markdown(self, title: str, content: str, at_mobiles: List[str] = None, is_at_all: bool = False):
        """发送Markdown消息 - 适合发送测试报告 [^17^]"""
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        return self._send(payload)

    def send_action_card(self, title: str, markdown: str, 
                         single_title: str = "查看详情", 
                         single_url: str = ""):
        """发送ActionCard消息 - 带按钮的报告通知"""
        payload = {
            "msgtype": "action_card",
            "action_card": {
                "title": title,
                "markdown": markdown,
                "single_title": single_title,
                "single_url": single_url
            }
        }
        return self._send(payload)

    def send_feed_card(self, links: List[Dict]):
        """发送FeedCard消息"""
        payload = {
            "msgtype": "feedCard",
            "feedCard": {"links": links}
        }
        return self._send(payload)

class TestReportNotifier:
    """测试报告专用通知器 - 集成Allure报告结果解析 [^17^]"""

    def __init__(self, config):
        self.ding = DingTalkNotifier(
            webhook=config.DINGTALK_WEBHOOK,
            secret=config.DINGTALK_SECRET
        )
        self.config = config

    def _parse_allure_results(self, allure_results_dir: str) -> Dict:
        """解析Allure测试结果 [^17^]"""
        import json
        import os

        summary_file = os.path.join(allure_results_dir, "widgets", "summary.json")
        if not os.path.exists(summary_file):
            return {}

        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'total': data.get('statistic', {}).get('total', 0),
                    'passed': data.get('statistic', {}).get('passed', 0),
                    'failed': data.get('statistic', {}).get('failed', 0),
                    'skipped': data.get('statistic', {}).get('skipped', 0),
                    'broken': data.get('statistic', {}).get('broken', 0),
                    'duration': data.get('time', {}).get('duration', 0) / 1000  # 转换为秒
                }
        except Exception as e:
            logger.error(f"Failed to parse Allure results: {e}")
            return {}

    def notify_test_start(self, total_cases: int, env: str):
        """测试开始通知"""
        content = f"""
## 🚀 测试任务启动

**环境**: {env}
**用例总数**: {total_cases}
**启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.ding.send_markdown("测试任务启动", content.strip())

    def notify_test_complete(self, result_summary: Dict, allure_report_url: str = ""):
        """测试完成通知 - 包含Allure报告链接 [^17^][^20^]"""
        total = result_summary.get('total', 0)
        passed = result_summary.get('passed', 0)
        failed = result_summary.get('failed', 0)
        skipped = result_summary.get('skipped', 0)
        duration = result_summary.get('duration', 0)

        # 计算成功率
        success_rate = (passed / total * 100) if total > 0 else 0

        # 根据结果选择表情
        emoji = "✅" if failed == 0 else "⚠️" if failed < total * 0.1 else "❌"

        content = f"""
{emoji} **接口自动化测试完成**

| 指标 | 数值 |
|------|------|
| 总用例数 | {total} |
| ✅ 通过 | {passed} |
| ❌ 失败 | {failed} |
| ⏭️ 跳过 | {skipped} |
| 📊 成功率 | {success_rate:.1f}% |
| ⏱️ 耗时 | {duration:.2f}s |

**报告链接**: [点击查看详细报告]({allure_report_url})
        """

        return self.ding.send_action_card(
            title="测试执行完成",
            markdown=content.strip(),
            single_title="查看完整报告",
            single_url=allure_report_url
        )

    def notify_failure_alert(self, failed_cases: List[Dict]):
        """失败告警通知 - 即时推送"""
        if not failed_cases:
            return

        # 只显示前5个失败用例
        display_cases = failed_cases[:5]
        cases_md = "\n".join([
            f"- **{case['name']}** ({case['id']}): {case['error'][:100]}"
            for case in display_cases
        ])

        content = f"""
## ❌ 测试失败告警

**发现 {len(failed_cases)} 个失败用例，请及时处理！**

{cases_md}

{'...' if len(failed_cases) > 5 else ''}
        """

        return self.ding.send_markdown(
            title=f"测试失败告警 - {len(failed_cases)}个用例失败",
            content=content.strip(),
            at_mobiles=self.config.DING_AT_MOBILES
        )

# pytest钩子集成 [^20^]
class DingTalkPytestPlugin:
    """pytest插件 - 自动发送通知"""

    def __init__(self, config):
        self.notifier = TestReportNotifier(config)
        self.results = {
            'total': 0, 'passed': 0, 'failed': 0, 
            'skipped': 0, 'errors': 0, 'duration': 0
        }
        self.failed_cases = []
        self.start_time = None
        self.allure_results_dir = ""

    def pytest_sessionstart(self, session):
        self.start_time = time.time()
        # 从配置中获取allure结果目录
        for arg in session.config.invocation_params.args:
            if "--alluredir" in arg:
                self.allure_results_dir = arg.split("=")[-1]

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results['total'] += 1
            if report.outcome == "passed":
                self.results['passed'] += 1
            elif report.outcome == "failed":
                self.results['failed'] += 1
                self.failed_cases.append({
                    'name': report.nodeid,
                    'id': getattr(report, 'testcase_id', 'unknown'),
                    'error': str(report.longrepr) if report.longrepr else "Unknown error"
                })
            elif report.outcome == "skipped":
                self.results['skipped'] += 1

    def pytest_sessionfinish(self, session, exitstatus):
        self.results['duration'] = time.time() - self.start_time

        # 尝试解析Allure结果获取更详细数据
        if self.allure_results_dir:
            allure_data = self.notifier._parse_allure_results(self.allure_results_dir)
            if allure_data:
                self.results.update(allure_data)

        # 发送完成通知
        report_url = f"http://your-report-server/{datetime.now().strftime('%Y%m%d')}/report.html"
        self.notifier.notify_test_complete(self.results, report_url)

        # 如果有失败，额外发送告警
        if self.failed_cases:
            self.notifier.notify_failure_alert(self.failed_cases)
