"""Firecrawl API 客户端"""

import requests
from typing import Dict
from datetime import datetime


class FirecrawlClient:
    """Firecrawl API 客户端"""

    def __init__(self, api_key: str):
        """
        初始化 Firecrawl 客户端

        Args:
            api_key: Firecrawl API Key
        """
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_credit_usage(self) -> Dict:
        """
        获取积分使用情况

        Returns:
            dict: 积分使用信息
                - remaining_credits (int): 剩余积分
                - plan_credits (int): 计划积分
                - billing_period_start (str): 计费周期开始
                - billing_period_end (str): 计费周期结束

        Raises:
            requests.RequestException: API 请求失败
            ValueError: API 返回错误
        """
        url = f"{self.base_url}/team/credit-usage"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            result = response.json()

            # API 返回结构: {"success": true, "data": {...}}
            if not result.get("success", False):
                raise ValueError("API 返回失败状态")

            data = result.get("data", {})

            return {
                "remaining_credits": data.get("remainingCredits", 0),
                "plan_credits": data.get("planCredits", 0),
                "billing_period_start": data.get("billingPeriodStart", ""),
                "billing_period_end": data.get("billingPeriodEnd", "")
            }

        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Firecrawl API 请求失败: {str(e)}")

    def format_usage_info(self, usage_data: Dict) -> str:
        """
        格式化积分使用信息为可读字符串

        Args:
            usage_data: get_credit_usage() 返回的数据

        Returns:
            str: 格式化后的使用信息
        """
        remaining = usage_data["remaining_credits"]
        plan = usage_data["plan_credits"]
        start = usage_data["billing_period_start"]
        end = usage_data["billing_period_end"]

        # 格式化日期
        def format_date(date_str: str) -> str:
            if not date_str:
                return "未知"
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                return date_str

        lines = [
            f"剩余积分:  {remaining:,}",
            f"计划积分:  {plan:,}",
            "",
            f"计费周期: {format_date(start)} 至 {format_date(end)}"
        ]

        return "\n".join(lines)
