# 技术设计文档

## 架构概览

### 组件关系图

```
┌─────────────────────────────────────────┐
│     convert_existing_data.py            │
│     (重构后的数据转换脚本)                │
└───────────┬─────────────────────────────┘
            │ 使用
            ▼
┌─────────────────────────────────────────┐
│     DataProcessor (基类)                │
│  - read_csv()                           │
│  - save_csv()                           │
│  - standardize_date()                   │
│  - pivot_data()                         │
└───────────┬─────────────────────────────┘
            │ 使用
            ▼
┌─────────────────────────────────────────┐
│     DataValidator                       │
│  - validate_date_range()                │
│  - check_missing_values()               │
│  - detect_outliers()                    │
│  - check_duplicates()                   │
│  - generate_quality_report()            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     DataLogger                          │
│  - log_step()                           │
│  - log_error()                          │
│  - log_quality_stats()                  │
└─────────────────────────────────────────┘
```

## 详细设计

### 1. DataValidator 类

**职责**：数据验证和质量检查

**接口设计**：
```python
class DataValidator:
    """数据验证器"""

    def __init__(self, df: pd.DataFrame, dataset_name: str):
        """
        Args:
            df: 要验证的数据框
            dataset_name: 数据集名称（用于日志）
        """
        self.df = df
        self.dataset_name = dataset_name
        self.issues = []

    def validate_date_column(self, column: str,
                           min_date: str = None,
                           max_date: str = None) -> bool:
        """
        验证日期列

        Args:
            column: 日期列名
            min_date: 最小日期（YYYY-MM-DD）
            max_date: 最大日期（YYYY-MM-DD）

        Returns:
            是否通过验证
        """

    def check_missing_values(self, threshold: float = 0.1) -> dict:
        """
        检查缺失值

        Args:
            threshold: 缺失值比例阈值（超过此比例报警）

        Returns:
            各列缺失值统计
        """

    def detect_outliers(self, column: str,
                       method: str = 'iqr') -> pd.DataFrame:
        """
        检测异常值

        Args:
            column: 要检测的列
            method: 检测方法 ('iqr' 或 'zscore')

        Returns:
            包含异常值的行
        """

    def check_duplicates(self, subset: list = None) -> int:
        """
        检查重复值

        Args:
            subset: 用于判断重复的列列表

        Returns:
            重复行数
        """

    def validate_required_columns(self, columns: list) -> bool:
        """
        验证必需列是否存在

        Args:
            columns: 必需列名列表

        Returns:
            是否全部存在
        """

    def generate_quality_report(self) -> dict:
        """
        生成数据质量报告

        Returns:
            包含各项质量指标的字典
        """
```

**实现要点**：
- 使用 IQR 方法检测异常值（Q1 - 1.5*IQR, Q3 + 1.5*IQR）
- 记录所有检测到的问题到 `self.issues`
- 提供汇总报告方法

### 2. DataProcessor 基类

**职责**：提供通用数据处理方法

**接口设计**：
```python
class DataProcessor:
    """数据处理基类"""

    def __init__(self, logger: DataLogger = None):
        """
        Args:
            logger: 日志记录器
        """
        self.logger = logger or DataLogger()

    def read_csv(self, filepath: Path,
                encodings: list = ['utf-8', 'utf-8-sig', 'gbk'],
                **kwargs) -> pd.DataFrame:
        """
        通用 CSV 读取方法（支持多种编码）

        Args:
            filepath: 文件路径
            encodings: 尝试的编码列表
            **kwargs: 传递给 pd.read_csv 的其他参数

        Returns:
            数据框

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 所有编码都失败
        """

    def save_csv(self, df: pd.DataFrame,
                filepath: Path,
                encoding: str = 'utf-8-sig') -> bool:
        """
        通用 CSV 保存方法

        Args:
            df: 要保存的数据框
            filepath: 保存路径
            encoding: 文件编码

        Returns:
            是否成功
        """

    def standardize_date(self, df: pd.DataFrame,
                        date_column: str,
                        target_format: str = '%Y-%m-%d') -> pd.DataFrame:
        """
        标准化日期格式

        Args:
            df: 数据框
            date_column: 日期列名
            target_format: 目标格式

        Returns:
            处理后的数据框
        """

    def filter_by_date(self, df: pd.DataFrame,
                      date_column: str,
                      start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        按日期范围过滤

        Args:
            df: 数据框
            date_column: 日期列名
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            过滤后的数据框
        """

    def pivot_to_wide(self, df: pd.DataFrame,
                     index: str,
                     columns: str,
                     values: str) -> pd.DataFrame:
        """
        长格式转宽格式

        Args:
            df: 数据框
            index: 索引列
            columns: 列名来源
            values: 值列

        Returns:
            转换后的数据框
        """
```

**实现要点**：
- 自动尝试多种编码，避免中文乱码
- 统一的错误处理和日志记录
- 保持原有数据不变，返回新的数据框

### 3. DataLogger 类

**职责**：统一的日志记录

**接口设计**：
```python
class DataLogger:
    """数据处理日志记录器"""

    def __init__(self, log_file: str = 'data_processing.log'):
        """
        Args:
            log_file: 日志文件路径
        """
        self.logger = logging.getLogger('DataProcessing')
        self._setup_logger(log_file)

    def _setup_logger(self, log_file: str):
        """配置日志记录器"""
        # 配置格式和输出目标

    def log_step(self, step_name: str, details: str = ''):
        """记录处理步骤"""

    def log_success(self, step_name: str, details: str = ''):
        """记录成功"""

    def log_error(self, step_name: str, error: Exception):
        """记录错误"""

    def log_warning(self, step_name: str, message: str):
        """记录警告"""

    def log_quality_stats(self, stats: dict):
        """记录数据质量统计"""
```

**实现要点**：
- 同时输出到文件和终端
- 使用统一的日志格式
- 包含时间戳和步骤名称

## 重构示例

### 重构前：convert_money_supply()

```python
def convert_money_supply():
    """转换货币供应量数据"""
    try:
        project_root = Path(__file__).parent.parent.parent
        input_file = project_root / 'data/processed/china/cn_money_supply.csv'
        df = pd.read_csv(input_file)

        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= '2016-01-01']

        df_pivot = df.pivot(index='date', columns='indicator_code', values='value')
        df_pivot = df_pivot.reset_index()
        df_pivot['date'] = df_pivot['date'].dt.strftime('%Y-%m-%d')

        if 'M1' in df_pivot.columns and 'M2' in df_pivot.columns:
            result = df_pivot[['date', 'M1', 'M2']].copy()
        else:
            print(f"  ⚠️ 可用的指标: {df_pivot.columns.tolist()}")
            return False

        output_file = Path('data/processed/china/m1_m2.csv')
        result.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功转换 {len(result)} 条记录")
        return True

    except Exception as e:
        print(f"  ❌ 转换失败: {str(e)}")
        return False
```

### 重构后

```python
def convert_money_supply():
    """转换货币供应量数据"""
    processor = DataProcessor()
    validator = None  # 延迟初始化
    logger = DataLogger()

    logger.log_step("convert_money_supply", "开始转换货币供应量数据")

    try:
        # 读取数据
        input_file = Path('data/processed/china/cn_money_supply.csv')
        df = processor.read_csv(input_file)
        logger.log_success("读取数据", f"成功读取 {len(df)} 条记录")

        # 验证数据
        validator = DataValidator(df, 'cn_money_supply')
        if not validator.validate_required_columns(['date', 'indicator_code', 'value']):
            raise ValueError("缺少必需列")

        # 处理数据
        df = processor.standardize_date(df, 'date')
        df = processor.filter_by_date(df, 'date', start_date='2016-01-01')
        df = processor.pivot_to_wide(df, 'date', 'indicator_code', 'value')

        # 验证输出列
        if not all(col in df.columns for col in ['M1', 'M2']):
            logger.log_warning("列检查", f"可用的指标: {df.columns.tolist()}")
            return False

        # 保存结果
        result = df[['date', 'M1', 'M2']].copy()
        output_file = Path('data/processed/china/m1_m2.csv')
        processor.save_csv(result, output_file)

        # 生成质量报告
        quality_report = validator.generate_quality_report()
        logger.log_quality_stats(quality_report)

        logger.log_success("convert_money_supply",
                          f"成功转换 {len(result)} 条记录")
        return True

    except Exception as e:
        logger.log_error("convert_money_supply", e)
        return False
```

## 测试策略

### 单元测试覆盖

| 组件 | 测试内容 | 优先级 |
|------|----------|--------|
| DataValidator | - 验证各种数据质量问题<br>- 边界条件<br>- 错误输入 | 高 |
| DataProcessor | - 各种编码的 CSV 读取<br>- 日期格式转换<br>- 数据透视 | 高 |
| DataLogger | - 日志格式<br>- 文件输出 | 中 |
| convert_* 函数 | - 使用模拟数据测试<br>- 验证输出正确性 | 高 |

### 集成测试

1. **回归测试**：对比重构前后的输出文件
   ```python
   def test_regression():
       # 使用相同输入运行新旧代码
       # 比较输出是否一致
   ```

2. **端到端测试**：运行完整的数据处理流程

## 性能考虑

### 优化措施

1. **延迟加载**：只在需要时加载完整数据
2. **分块处理**：对于大数据集，分块读取和处理
3. **缓存**：缓存重复使用的计算结果

### 性能基准

在重构前后测量：
- 数据读取时间
- 处理时间
- 内存使用

目标：性能下降 < 10%

## 向后兼容性

### 保持不变的接口

- 所有 `convert_*` 函数的输入输出接口
- 生成的 CSV 文件格式
- 数据目录结构

### 迁移路径

1. 保留原始文件备份（`.bak`）
2. 逐步替换函数实现
3. 测试验证后再删除备份
