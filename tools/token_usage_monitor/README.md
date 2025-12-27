# API 使用量监控工具

快速查询 DeepSeek 和 Firecrawl API 的使用量。

## 功能特性

- ✅ 查询 DeepSeek API 余额（总余额、充值余额、赠送余额）
- ✅ 查询 Firecrawl API 积分（剩余积分、计划积分、计费周期）
- ✅ 美观的命令行输出（使用 Rich 库）
- ✅ 支持单独查询某个服务

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 查看所有服务

```bash
python monitor.py
```

### 只查看 DeepSeek

```bash
python monitor.py --service deepseek
```

### 只查看 Firecrawl

```bash
python monitor.py --service firecrawl
```

## 配置

确保 `/home/shang/git/Indeptrader/tools/.env` 文件包含以下内容：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

## 项目结构

```
token_usage_monitor/
├── monitor.py              # 主脚本入口
├── api_clients/
│   ├── __init__.py
│   ├── deepseek.py        # DeepSeek API 客户端
│   └── firecrawl.py       # Firecrawl API 客户端
├── utils/
│   ├── __init__.py
│   └── config.py          # 配置管理
└── requirements.txt       # Python 依赖
```

## 示例输出

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ API 使用量监控                                                               │
│ 2025-12-27 10:19:51                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────── 📊 DeepSeek API ───────────────────────────────╮
│ 状态: ✅ 可用                                                                │
│ 总余额:  CNY 9.39                                                            │
│   ├─ 充值余额:   CNY 9.39                                                    │
│   └─ 赠送余额:   CNY 0.00                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────── 🔥 Firecrawl API ──────────────────────────────╮
│ 剩余积分:  485                                                               │
│ 计划积分:  0                                                                 │
│                                                                              │
│ 计费周期: 未知 至 未知                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```
