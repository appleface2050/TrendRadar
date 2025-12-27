# RunningV2

跑步数据管理与分析系统，提供 CSV 到 MySQL 的数据同步和 Web Dashboard 可视化功能。

## 功能特性

- **数据同步**：将 CSV 文件自动同步到 MySQL 数据库
  - 跑步记录同步（records.csv → running_shoe_record）
  - RQ 能力值同步（rq.csv → running_rq_record）
  - 跑鞋信息同步（shoe_info.csv → running_shoe_info）
  - 支持增量同步和数据去重

- **Web Dashboard**：基于 Chart.js 的数据可视化
  - RQ 能力值历史数据展示
  - Prophet 时间序列预测（未来 30 天）
  - 预测区间阴影显示
  - 统计信息面板（当前值、增长趋势、最大值、最小值）

## 项目结构

```
RunningV2/
├── config/              # 配置模块
│   └── settings.py     # 数据库配置
├── sync/               # 数据同步模块
│   ├── base.py         # 同步基类
│   ├── records_sync.py # 跑步记录同步
│   ├── rq_sync.py      # RQ 能力值同步
│   └── shoe_info_sync.py # 跑鞋信息同步
├── dashboard/          # Web Dashboard
│   ├── app.py          # Flask API 服务
│   ├── static/         # 静态资源
│   │   ├── css/style.css
│   │   └── js/dashboard.js
│   └── templates/      # HTML 模板
│       └── index.html
├── csv/                # CSV 数据文件
│   ├── records.csv
│   ├── rq.csv
│   └── shoe_info.csv
├── utils/              # 工具模块
├── main.py             # 命令行工具入口
└── requirements.txt    # 依赖清单
```

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- pandas：数据处理
- sqlalchemy：ORM 框架
- pymysql：MySQL 驱动
- prophet：时间序列预测
- flask：Web 框架

## 使用方法

### 1. 数据同步

同步所有 CSV 文件：
```bash
python main.py sync
```

同步单个文件：
```bash
python main.py sync-records   # 只同步 records.csv
python main.py sync-rq        # 只同步 rq.csv
python main.py sync-shoe      # 只同步 shoe_info.csv
```

### 2. 启动 Dashboard

开发环境：
```bash
python dashboard/app.py
```

访问地址：http://localhost:5000

### 3. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Dashboard 主页 |
| `/api/rq/history` | GET | 获取历史 RQ 数据 |
| `/api/rq/forecast` | GET | 获取 RQ 预测数据 |
| `/api/rq/stats` | GET | 获取 RQ 统计信息 |

## 数据库表结构

- **running_shoe_record**：跑步记录表
- **running_rq_record**：RQ 能力值记录表
- **running_shoe_info**：跑鞋信息表

## 技术栈

- **后端**：Flask + SQLAlchemy + Prophet
- **前端**：HTML + CSS + JavaScript + Chart.js
- **数据库**：MySQL
- **数据处理**：Pandas

## Dashboard 预览

Dashboard 提供：
- 散点图展示历史 RQ 数据（蓝色）
- 预测值散点图（绿色）
- 预测区间阴影显示
- 响应式设计，支持移动端

## 配置说明

数据库配置位于 `config/settings.py`，根据实际情况修改数据库连接信息。
