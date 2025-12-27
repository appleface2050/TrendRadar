"""DeepSeek API 客户端"""

import requests
from typing import Dict, Optional


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: str):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API Key
        """
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_balance(self) -> Dict:
        """
        获取账户余额信息

        Returns:
            dict: 余额信息
                - is_available (bool): 余额是否可用
                - currency (str): 货币类型
                - total_balance (float): 总余额
                - granted_balance (float): 赠送余额
                - topped_up_balance (float): 充值余额

        Raises:
            requests.RequestException: API 请求失败
            ValueError: API 返回错误
        """
        url = f"{self.base_url}/user/balance"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 解析余额信息
            if not data.get("is_available", False):
                return {
                    "is_available": False,
                    "error": "账户余额不可用"
                }

            balance_infos = data.get("balance_infos", [])
            if not balance_infos:
                return {
                    "is_available": False,
                    "error": "未找到余额信息"
                }

            # 获取主要货币的余额 (优先 USD，其次 CNY)
            balance_info = None
            for info in balance_infos:
                if info.get("currency") in ["USD", "CNY"]:
                    balance_info = info
                    break

            if not balance_info:
                balance_info = balance_infos[0]

            # API 返回的余额是字符串，需要转换为 float
            return {
                "is_available": True,
                "currency": balance_info.get("currency", "USD"),
                "total_balance": float(balance_info.get("total_balance", 0)),
                "granted_balance": float(balance_info.get("granted_balance", 0)),
                "topped_up_balance": float(balance_info.get("topped_up_balance", 0))
            }

        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"DeepSeek API 请求失败: {str(e)}")

    def format_balance_info(self, balance_data: Dict) -> str:
        """
        格式化余额信息为可读字符串

        Args:
            balance_data: get_balance() 返回的数据

        Returns:
            str: 格式化后的余额信息
        """
        if not balance_data.get("is_available"):
            return f"❌ 错误: {balance_data.get('error', '未知错误')}"

        currency = balance_data["currency"]
        total = balance_data["total_balance"]
        granted = balance_data["granted_balance"]
        topped_up = balance_data["topped_up_balance"]

        lines = [
            f"状态: ✅ 可用",
            f"总余额:  {currency} {total:.2f}",
            f"  ├─ 充值余额:   {currency} {topped_up:.2f}",
            f"  └─ 赠送余额:   {currency} {granted:.2f}",
        ]

        return "\n".join(lines)
