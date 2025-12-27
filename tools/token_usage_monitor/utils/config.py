"""配置管理模块"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_config():
    """
    从 .env 文件加载 API Keys

    Returns:
        dict: 包含 API Keys 的字典
            - deepseek_api_key: DeepSeek API Key
            - firecrawl_api_key: Firecrawl API Key
    """
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / '.env'

    # 加载 .env 文件（覆盖环境变量）
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        raise FileNotFoundError(f"配置文件不存在: {env_file}")

    # 获取 API Keys
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')

    if not deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY 未在 .env 文件中配置")

    if not firecrawl_api_key:
        raise ValueError("FIRECRAWL_API_KEY 未在 .env 文件中配置")

    return {
        'deepseek_api_key': deepseek_api_key,
        'firecrawl_api_key': firecrawl_api_key
    }
