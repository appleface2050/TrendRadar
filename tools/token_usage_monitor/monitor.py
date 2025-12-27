#!/usr/bin/env python3
"""API 使用量监控主脚本"""

import sys
import argparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from api_clients import DeepSeekClient, FirecrawlClient
from utils.config import load_config


def create_title(console: Console) -> Panel:
    """创建标题面板"""
    title_text = Text()
    title_text.append("API 使用量监控", style="bold cyan")
    title_text.append("\n")
    title_text.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), style="dim")

    return Panel(
        title_text,
        title_align="center",
        border_style="bright_blue"
    )


def display_deepseek(console: Console, client: DeepSeekClient):
    """显示 DeepSeek API 使用情况"""
    try:
        balance_data = client.get_balance()
        content = client.format_balance_info(balance_data)

        panel = Panel(
            content,
            title="📊 DeepSeek API",
            border_style="green"
        )
        console.print(panel)

    except Exception as e:
        error_panel = Panel(
            f"❌ 查询失败: {str(e)}",
            title="📊 DeepSeek API",
            border_style="red"
        )
        console.print(error_panel)


def display_firecrawl(console: Console, client: FirecrawlClient):
    """显示 Firecrawl API 使用情况"""
    try:
        usage_data = client.get_credit_usage()
        content = client.format_usage_info(usage_data)

        panel = Panel(
            content,
            title="🔥 Firecrawl API",
            border_style="orange3"
        )
        console.print(panel)

    except Exception as e:
        error_panel = Panel(
            f"❌ 查询失败: {str(e)}",
            title="🔥 Firecrawl API",
            border_style="red"
        )
        console.print(error_panel)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="API 使用量监控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--service',
        choices=['deepseek', 'firecrawl'],
        help='指定要查询的服务（默认查询所有）'
    )

    args = parser.parse_args()
    console = Console()

    try:
        # 加载配置
        config = load_config()

        # 显示标题
        console.print()
        console.print(create_title(console))
        console.print()

        # 根据参数选择服务
        if args.service == 'deepseek':
            client = DeepSeekClient(config['deepseek_api_key'])
            display_deepseek(console, client)

        elif args.service == 'firecrawl':
            client = FirecrawlClient(config['firecrawl_api_key'])
            display_firecrawl(console, client)

        else:
            # 显示所有服务
            deepseek_client = DeepSeekClient(config['deepseek_api_key'])
            firecrawl_client = FirecrawlClient(config['firecrawl_api_key'])

            display_deepseek(console, deepseek_client)
            console.print()
            display_firecrawl(console, firecrawl_client)

        console.print()

    except FileNotFoundError as e:
        console.print(f"[red]❌ 错误: {str(e)}[/red]")
        sys.exit(1)

    except ValueError as e:
        console.print(f"[red]❌ 配置错误: {str(e)}[/red]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ 未知错误: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
