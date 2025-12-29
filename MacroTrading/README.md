# MacroTrading - 融合Nowcasting与动态因子模型的宏观交易框架

## 项目概述

**目标定位**：研究验证版（6-9个月），聚焦模型有效性验证
**市场范围**：中美双核同步分析
**回测方案**：Backtrader为主 + Qlib辅助 + 自定义Python代码
**计算资源**：本地GPU + CPU混合

## 项目结构

```
MacroTrading/
├── data/                           # 数据层
│   ├── us/                         # 美国数据
│   │   ├── us_data_fetcher.py      # FRED数据获取器
│   │   ├── us_data_manager.py      # 数据管理器
│   │   ├── us_calendar.py          # 发布日历
│   │   └── test_us_data.py         # 测试脚本
│   ├── cn/                         # 中国数据
│   │   ├── tushare_fetcher.py      # Tushare数据获取器
│   │   ├── cn_data_manager.py      # 数据管理器
│   │   └── cn_calendar.py          # 发布日历（含春节效应）
│   ├── alternative/                # 另类数据
│   └── flow/                       # 资金流数据
├── models/                         # 模型层
│   ├── dfm/                        # 动态因子模型
│   ├── regime/                     # 区制转移模型
│   ├── midas/                      # MIDAS混频回归
│   ├── nowcasting/                 # Nowcasting引擎
│   ├── flow/                       # 资金流模型
│   └── risk/                       # 风险预警
├── strategies/                     # 策略层
│   ├── timing/                     # 大势择时
│   └── rotation/                   # 行业轮动
├── backtest/                       # 回测层
│   ├── aligner/                    # 数据对齐
│   ├── strategies/
│   ├── runner/
│   └── analysis/
├── utils/                          # 工具层
│   ├── calendar_aligner.py         # 日历对齐器（核心！）
│   └── release_calendar_db.py      # 发布日历数据库
├── dashboard/                      # 可视化
│   └── app.py
└── configs/                        # 配置
    ├── db_config.py                # 数据库配置
    └── init_db.py                  # 数据库初始化脚本
```

## 第一阶段完成情况（数据基础设施）

### ✅ 已完成

1. **项目目录结构** - 完整的模块化目录结构
2. **数据库搭建** - MySQL数据库 `MacroTrading` 及核心表
3. **美国数据模块**
   - FRED数据获取器（支持50+核心指标）
   - 数据管理器（CRUD操作）
   - 发布日历（估算发布时间）
   - 测试验证通过

4. **中国数据模块**
   - Tushare数据获取器（支持GDP/CPI/PPI/M1/M2/PMI等）
   - 数据管理器
   - 发布日历（考虑春节效应等中国特色）
   - 支持数据源：tushare、akshare

5. **日历对齐器**（核心基础设施！）
   - 获取指定日期实际可观测的数据
   - 杜绝未来函数（look-ahead bias）
   - 支持混频数据（日/周/月/季）
   - 中美两国数据统一接口

### 📊 数据库表结构

- `us_macro_data` - 美国宏观数据表
- `cn_macro_data` - 中国宏观数据表
- `release_calendar` - 发布日历表

## 快速开始

### 1. 安装依赖

```bash
# 第一阶段依赖
pip install pandas-datareader fredapi tushare akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pandas-market-calendars exchange_calendars -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install sqlalchemy pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install chinese_calendar -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置API密钥

编辑 `configs/db_config.py`：

```python
FRED_API_KEY = 'your_fred_api_key'  # 可选，但建议设置
TUSHARE_TOKEN = 'your_tushare_token'  # 必需，用于获取中国数据
```

### 3. 初始化数据库

```bash
cd MacroTrading/configs
python init_db.py
```

### 4. 测试数据获取

```bash
# 测试美国数据
cd MacroTrading
python data/us/test_us_data.py
```

## 核心模块使用示例

### 日历对齐器使用

```python
from utils.calendar_aligner import get_available_data, get_indicator_value

# 获取2024-01-15可观测的所有美国宏观数据
data = get_available_data('2024-01-15', country='US')

# 获取单个指标值
gdp_value = get_indicator_value('2024-01-15', 'GDP', 'US')
```

### 美国数据获取

```python
from data.us.us_data_fetcher import USDataFetcher
from data.us.us_data_manager import USDataManager

# 获取数据
fetcher = USDataFetcher()
gdp_data = fetcher.fetch_indicator('GDP', start='2020-01-01')

# 保存到数据库
manager = USDataManager()
manager.save_data(gdp_data)
```

### 中国数据获取

```python
from data.cn.tushare_fetcher import CNDataFetcher
from data.cn.cn_data_manager import CNDataManager

# 获取数据
fetcher = CNDataFetcher()
cpi_data = fetcher.fetch_cpi(start='20230101')

# 保存到数据库
manager = CNDataManager()
manager.save_data(cpi_data)
```

## 技术栈

- **数据获取**：pandas-datareader, fredapi, tushare, akshare
- **数据存储**：MySQL + SQLAlchemy ORM
- **日历处理**：pandas-market-calendars, exchange_calendars, chinese_calendar
- **数值计算**：pandas, numpy
- **统计建模**：statsmodels, scikit-learn（第二阶段）
- **回测框架**：backtrader, qlib（第四阶段）

## 下一步计划

### 第二阶段：Nowcasting与状态识别模型（2.5个月）

1. **动态因子模型（DFM）** - 提取经济增长、通胀、流动性因子
2. **马尔可夫区制转移模型** - 识别宏观状态（复苏/过热/滞胀/衰退）
3. **MIDAS混频回归** - 处理不同频率数据
4. **Nowcasting引擎** - 实时预测GDP/CPI

### 第三阶段：因子模型与资金流分析（2个月）

1. **资金流驱动模型** - 三层分解（全球层、相对吸引力层、微观层）
2. **复合风险预警指数** - 机器学习动态赋权

### 第四阶段：映射模型与回测验证（2.5个月）

1. **大势择时模型** - 多因子打分系统
2. **行业轮动模型** - 基于宏观状态筛选
3. **Backtrader回测** - 端到端验证
4. **Streamlit仪表盘** - 实时监控

## 重要提醒

### ⚠️ 日历对齐的重要性

日历对齐器是整个回测系统的**生命线**，必须100%准确：

- ❌ 错误做法：直接使用数据日期（引入未来函数）
- ✅ 正确做法：使用发布日期（确保回测真实性）

示例：
```python
# ❌ 错误：2024-01-15的GDP数据可能要到2024-04-30才发布
gdp = df.loc['2024-01-15']['GDP']  # 这是在偷看未来！

# ✅ 正确：使用日历对齐器
gdp = get_indicator_value('2024-01-15', 'GDP', 'US')  # 只获取该日已发布的数据
```

### 数据质量要求

- 垃圾进垃圾出（GIGO）- 数据质量决定模型上限
- 多源交叉验证
- 人工复核异常值

## 参考文档

- 实施计划：`plan-融合Nowcasting与动态因子模型的宏观交易框架 - 实施计划`
- FRED文档：https://fred.stlouisfed.org/docs/api/fred/
- Tushare文档：https://tushare.pro/document/2

## 许可证

本项目为研究验证项目，仅供学习和研究使用。
