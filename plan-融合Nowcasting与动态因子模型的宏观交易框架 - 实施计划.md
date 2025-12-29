# 融合Nowcasting与动态因子模型的宏观交易框架 - 实施计划

## 项目概述

**目标定位**：研究验证版（6-9个月），聚焦模型有效性验证
**市场范围**：中美双核同步分析
**回测方案**：Backtrader为主 + Qlib辅助 + 自定义Python代码
**计算资源**：本地GPU + CPU混合

---

## 项目现状评估

### ✅ 已有基础（可直接复用）
1. **美国数据**：完整的FRED数据获取脚本（10Y-2Y利差、国债收益率、M1/M2）
2. **数据库**：MySQL + SQLAlchemy ORM（已有表结构和数据管理代码）
3. **基础模型**：ARIMA、Prophet时间序列预测
4. **可视化**：完整的HTML/JS仪表板
5. **理论文档**：完整的研究报告和技术文档

### ❌ 主要缺失模块（需新建）
1. **中国数据源**：Wind/Tushare/akshare
2. **高级计量模型**：DFM、MIDAS、MS/HMM、Nowcasting引擎
3. **回测平台**：Backtrader、Qlib
4. **宏观数据日历对齐器**：核心基础设施
5. **量化因子库**：行业轮动因子、宏观因子

---

## 技术选型

| 模块 | 推荐方案 | 备选方案 |
|------|----------|----------|
| **动态因子模型** | statsmodels.tsa.statespace + 自定义 | dfmpy |
| **马尔可夫区制转移** | statsmodels.tsa.regime_switching | hmmlearn, TensorFlow Probability |
| **MIDAS混频回归** | midaspy + 自实现 | 参考Ghysels论文自实现 |
| **回测平台** | Backtrader（主）+ Qlib（辅助） | 自定义Python代码 |
| **深度学习** | PyTorch（优先） | TensorFlow |

---

## 分阶段实施计划（9个月）

### 📌 第一阶段：数据基础设施与核心数据源（2个月）

**目标**：构建中美双核数据管道，实现自动化数据获取与存储

#### 第1个月：美国数据扩展 + 中国数据源接入

**Week 1-2: 美国数据扩展**
- 安装库：pandas-datareader, fredapi
- 新增模块：
  - `MacroTrading/data/us/us_data_fetcher.py` - 扩展现有FRED脚本
  - `MacroTrading/data/us/us_calendar.py` - FRED发布日历
  - `MacroTrading/data/us/us_data_manager.py` - 统一数据管理接口
- 新增指标：GDP、CPI、失业率、PMI、工业产值、零售销售
- 存储：MySQL表`us_macro_data` + CSV备份

**Week 3-4: 中国数据源接入**
- 安装库：tushare, akshare
- 新增模块：
  - `MacroTrading/data/cn/tushare_fetcher.py` - 中国宏观数据
  - `MacroTrading/data/cn/cn_calendar.py` - 中国发布日历（含春节效应）
  - `MacroTrading/data/cn/cn_data_manager.py` - 统一数据管理
- 核心指标：GDP、CPI、PPI、M1/M2、社融、PMI、Shibor、DR007
- 存储：MySQL表`cn_macro_data`

#### 第2个月：宏观数据日历对齐器（核心基础设施）

**Week 1-2: 另类数据接入（可选）**
- 百度指数、高德交通数据、卫星数据

**Week 3-4: 日历对齐器**
- 安装库：pandas-market-calendars, exchange_calendars
- 核心模块：
  - `MacroTrading/utils/calendar_aligner.py` - **核心基础设施**
    ```python
    def get_available_data(date: str, indicator: str) -> float:
        """获取在date日期实际可观测的宏观数据值（杜绝未来函数）"""
    ```
  - `MacroTrading/utils/release_calendar_db.py` - 发布日历数据库
- 验证：随机抽查历史日期，确保100%准确

**✅ 第一阶段交付物**
1. 中美双核宏观数据库（MySQL + CSV）
2. 发布日历数据库
3. 日历对齐器（回测真实性保障）
4. 统一数据管理接口

**⚠️ 风险**：Tushare API限流、中国数据质量、日历准确性

---

### 📌 第二阶段：Nowcasting与状态识别模型（2.5个月）

**目标**：实现核心计量模型，产出宏观状态概率序列与GDP/CPI实时预测

#### 第3个月：动态因子模型（DFM）

- 安装库：scikit-learn
- 新增模块：
  - `MacroTrading/models/dfm/base_dfm.py` - 基于statsmodels的DFM实现
  - `MacroTrading/models/dfm/us_dfm.py` - 美国DFM（经济增长、通胀、流动性因子）
  - `MacroTrading/models/dfm/cn_dfm.py` - 中国DFM
  - `MacroTrading/models/dfm/sparse_dfm.py` - 稀疏PCA优化
  - `MacroTrading/models/dfm/rolling_dfm.py` - 滚动估计避免结构性断裂
- 验证：因子稳定性（滚动相关>0.7）、经济含义（与理论一致）

#### 第4个月：马尔可夫区制转移模型（MS）

- 安装库：hmmlearn
- 新增模块：
  - `MacroTrading/models/regime/markov_switching.py` - 基于statsmodels的MS模型
  - `MacroTrading/models/regime/us_regime_model.py` - 美国4状态识别
  - `MacroTrading/models/regime/cn_regime_model.py` - 中国4状态（复苏、过热、滞胀、衰退）
  - `MacroTrading/models/regime/hmm_model.py` - HMM备选方案
- 验证：区制识别准确率（与历史衰退对比）、状态持续期合理性

#### 第5个月：MIDAS混频回归与Nowcasting引擎

- 安装库：midaspy（或自实现）
- 新增模块：
  - `MacroTrading/models/midas/midas_regression.py` - MIDAS回归核心实现
  - `MacroTrading/models/midas/us_nowcasting.py` - 美国GDP Nowcasting
  - `MacroTrading/models/midas/cn_nowcasting.py` - 中国GDP Nowcasting
  - `MacroTrading/models/nowcasting/mf_dfm.py` - 混频动态因子模型
  - `MacroTrading/models/nowcasting/nowcasting_engine.py` - **核心引擎**
    - 输入：所有可用数据（混频）
    - 输出：GDP/CPI实时预测 + 不确定性区间
- 验证：预测RMSE、领先期（vs官方发布）、预测路径稳定性

**✅ 第二阶段交付物**
1. 动态因子模型（US/CN DFM）
2. 马尔可夫区制转移模型（4状态识别）
3. MIDAS混频回归
4. Nowcasting引擎（GDP/CPI实时预测）
5. 宏观状态概率序列（每日更新）

**⚠️ 风险**：模型复杂度导致估计耗时、过拟合、混频数据缺失

---

### 📌 第三阶段：因子模型与资金流分析（2个月）

**目标**：构建中美联动分析框架、资金流Nowcasting模型、复合风险预警指数

#### 第6个月：资金流驱动模型

- 安装库：arch（GARCH模型）
- 新增模块：
  - `MacroTrading/data/flow/flow_fetcher.py` - 北向/南向资金、VIX、美元指数
  - `MacroTrading/models/flow/flow_driver_model.py` - 三层驱动模型
    - 全球层：VIX、美元指数
    - 相对吸引力层：中美实际利差、增长预期差
    - 市场微观层：AH溢价、USDCNH期权
  - `MacroTrading/models/flow/flow_nowcasting.py` - MIDAS预测未来1-5日资金流
- 验证：方向准确率>55%、驱动因子显著性

#### 第7个月：复合风险预警指数

- 安装库：xgboost, lightgbm
- 新增模块：
  - `MacroTrading/models/risk/market_risk_indicators.py`
    - 市场情绪：期权波动率偏度
    - 流动性压力：R007-DR007利差、信用利差
    - 杠杆水平：融资交易占比
    - 外资行为：北向资金Z-score
  - `MacroTrading/models/risk/macro_risk_indicators.py`
    - 宏观状态：衰退概率
    - 通胀风险：CPI超预期概率
  - `MacroTrading/models/risk/composite_risk_index.py` - **XGBoost动态赋权**
    - 训练目标：预测未来5日/20日市场回撤
    - 输出：0-100综合风险指数
- 验证：风险指数与未来回撤相关>0.5、预警准确率>70%

**✅ 第三阶段交付物**
1. 资金流驱动模型（三层分解）
2. 资金流Nowcasting（1-5日预测）
3. 复合风险预警指数（0-100综合评分）
4. 外资情绪因子（标准化序列）

**⚠️ 风险**：期权数据需付费、机器学习过拟合、指标滞后性

---

### 📌 第四阶段：映射模型与回测验证（2.5个月）

**目标**：构建从宏观状态到资产价格的映射模型，完成端到端回测验证

#### 第8个月：映射模型构建

**Week 1-2: 大势择时模型**
- 新增模块：
  - `MacroTrading/strategies/timing/macro_scorecard.py` - **多因子打分系统**
    - 宏观状态分：MS模型状态概率
    - 流动性分：M1-M2剪刀差、社融增速
    - 估值分：股债风险溢价（ERP）
    - 外资情绪分：资金流Nowcasting
  - `MacroTrading/strategies/timing/signal_generator.py`
    - 输出：仓位建议（0%-100%）
    - 风险调整：根据风险指数动态缩减

**Week 3-4: 行业轮动模型**
- 新增模块：
  - `MacroTrading/strategies/rotation/industry_macro_db.py` - 宏观状态-行业表现数据库
  - `MacroTrading/strategies/rotation/industry_selector.py`
    - 基于宏观状态筛选行业池
    - 结合宏观因子边际变化二次筛选
    - 引入行业动量确认
    - 输出：行业权重建议

#### 第9个月：回测平台与验证

**Week 1-2: Backtrader框架搭建**
- 安装库：backtrader, qlib
- 新增模块：
  - `MacroTrading/backtest/aligner/macro_data_feed.py` - **自定义数据源**
    - 集成日历对齐器（无未来函数）
    - 混频数据处理
  - `MacroTrading/backtest/strategies/macro_strategy.py` - Backtrader策略类
  - `MacroTrading/backtest/runner/backtest_engine.py` - 回测引擎
    - 样本内/样本外划分
    - 滚动窗口回测

**Week 3-4: 全面回测与验证**
- 新增模块：
  - `MacroTrading/backtest/analysis/performance_attribution.py` - 绩效归因
  - `MacroTrading/backtest/analysis/report_generator.py` - 报告生成
- 回测设计：
  - 样本期：2016-2024（完整周期）
  - 样本外：2022-2024（泛化能力）
  - 基准：沪深300、中证500
  - 评估：年化收益、夏普、最大回撤、Calmar、极端年份表现

**Week 5-6: 监控仪表盘**
- 安装库：streamlit, plotly
- 新增模块：
  - `MacroTrading/dashboard/app.py` - **实时监控**
    - 宏观状态概率
    - Nowcasting预测路径
    - 复合风险指数
    - 择时信号
    - 行业权重建议

**✅ 第四阶段交付物**
1. 大势择时模型（多因子打分）
2. 行业轮动模型（基于宏观状态）
3. Backtrader回测框架（带日历对齐）
4. 完整回测报告（2016-2024绩效与归因）
5. Streamlit监控仪表盘

**⚠️ 风险**：未来函数（日历对齐必须100%准确）、过拟合、交易成本、极端行情

---

## 项目文件结构

```
MacroTrading/
├── data/                           # 数据层
│   ├── us/                         # 美国数据
│   │   ├── us_data_fetcher.py
│   │   ├── us_calendar.py
│   │   └── us_data_manager.py
│   ├── cn/                         # 中国数据
│   │   ├── tushare_fetcher.py
│   │   ├── cn_calendar.py
│   │   └── cn_data_manager.py
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
│   └── release_calendar_db.py
├── dashboard/                      # 可视化
│   └── app.py
└── configs/                        # 配置
    ├── db_config.py
    └── model_config.py
```

---

## Python依赖安装（分阶段）

### 第一阶段
```bash
pip install pandas-datareader fredapi tushare akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pandas-market-calendars exchange_calendars -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install sqlalchemy pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第二阶段
```bash
pip install statsmodels scikit-learn hmmlearn -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install midaspy -i https://pypi.tuna.tsinghua.edu.cn/simple  # 如果可用
pip install matplotlib seaborn plotly -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第三阶段
```bash
pip install xgboost lightgbm -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install arch -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第四阶段
```bash
pip install backtrader -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install qlib -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install streamlit plotly -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyfolio empyrical -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 深度学习备选（可选）
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 成功标准与验收指标

### 模型性能指标
| 模块 | 指标 | 目标值 |
|------|------|--------|
| Nowcasting | GDP预测RMSE | <0.5% |
| Nowcasting | 领先期 | ≥1个月 |
| 状态识别 | 区制识别准确率 | >75% |
| DFM | 因子稳定性 | >0.7 |
| 资金流预测 | 方向准确率 | >55% |
| 风险指数 | 预警召回率 | >70% |

### 回测绩效指标
| 指标 | 目标值 |
|------|--------|
| 年化收益 | >8% |
| 夏普比率 | >1.0 |
| 最大回撤 | <25% |
| Calmar比率 | >0.3 |
| 2018/2022相对基准超额 | >5% |

---

## 关键成功因素

1. **数据质量**：垃圾进垃圾出，数据质量决定模型上限
2. **日历对齐**：回测真实性的生命线，必须100%准确
3. **样本外验证**：严格避免过拟合，确保泛化能力
4. **渐进式开发**：先跑通核心流程，再优化细节

---

## 优先级排序

### 高优先级（必须完成）
1. 日历对齐器（所有回测基础）
2. 中美数据管道（模型输入保障）
3. Nowcasting引擎（核心价值）
4. 状态识别模型（宏观状态量化）

### 中优先级（重要但可简化）
1. 资金流驱动模型（可先用简单回归）
2. 风险预警指数（可先用等权权重）
3. 行业轮动模型（可先用固定规则）

### 低优先级（可延后）
1. 另类数据（卫星、互联网行为）
2. 深度学习模型（传统方法已足够）
3. NLP情绪因子（增强模块）

---

## 依赖关系图

```
日历对齐器
    ↓
数据管道
    ↓
DFM → MS模型（并行）
    ↓
Nowcasting（依赖DFM + MS）
    ↓
资金流模型（可与Nowcasting并行）
    ↓
风险指数（依赖Nowcasting + 资金流）
    ↓
择时模型（依赖风险指数 + MS）
    ↓
行业轮动（依赖MS + 宏观因子）
    ↓
回测验证（依赖所有上游）
```

---

## 风险与应急方案

| 风险 | 应急方案 |
|------|----------|
| MIDAS实现困难 | 降级为简单降频处理（日→周） |
| 数据获取失败 | 手动下载或购买商业数据 |
| 模型估计失败 | 简化参数（减少因子数、状态数） |
| 回测平台问题 | 手写简化Python回测逻辑 |
| Tushare API限流 | 设计缓存策略 |
| 数据质量问题 | 多源交叉验证、人工复核 |

---

## 预期成果

9个月后，您将拥有：
1. ✅ 完整的量化宏观交易框架（从数据到回测）
2. ✅ 验证有效的核心模型（Nowcasting、状态识别、风险预警）
3. ✅ 可解释的宏观状态序列（每日更新的宏观因子）
4. ✅ 可运行的交易策略（历史绩效验证通过）
5. ✅ 可迭代的系统（支持持续优化）

---

## 下一步行动

1. 创建项目目录结构：`MacroTrading/`
2. 安装第一阶段依赖库
3. 开始数据管道开发（从美国FRED扩展开始）、
4. 数据库中创建新的database，名为：MacroTrading

---

## 关键参考文件（现有最佳实践）

- `confs/mysql.py` - 数据库配置参考

新模块应遵循这些文件的编码风格、数据管理模式和错误处理机制。
