"""
数据处理工具单元测试

测试 DataProcessor、DataValidator 和 DataLogger 类
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_processor import DataProcessor
from utils.data_validator import DataValidator
from utils.data_logger import DataLogger


@pytest.fixture
def sample_df():
    """创建示例数据框"""
    return pd.DataFrame({
        'date': pd.date_range('2020-01-01', periods=100),
        'value1': np.random.randn(100) * 10 + 50,
        'value2': np.random.randn(100) * 20 + 100,
        'category': ['A', 'B', 'C'] * 33 + ['A']
    })


@pytest.fixture
def sample_df_with_issues():
    """创建包含问题的示例数据框"""
    data = {
        'date': ['2020-01-01', '2020-01-02', None, '2020-01-02', '2020-01-03'],
        'value': [100, 200, 150, 200, 1000],  # 包含重复和异常值
        'category': ['A', 'B', 'A', None, 'C']  # 包含缺失值
    }
    return pd.DataFrame(data)


class TestDataLogger:
    """测试 DataLogger 类"""

    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = DataLogger()
        assert logger is not None
        assert logger.logger is not None

    def test_log_methods(self, capsys):
        """测试各种日志方法"""
        logger = DataLogger()

        logger.log_step("测试步骤", "详细信息")
        logger.log_success("测试成功", "成功信息")
        logger.log_warning("测试警告", "警告信息")

        captured = capsys.readouterr()
        assert "[测试步骤]" in captured.out
        assert "✅" in captured.out
        assert "⚠️" in captured.out


class TestDataValidator:
    """测试 DataValidator 类"""

    def test_validator_creation(self, sample_df):
        """测试验证器创建"""
        validator = DataValidator(sample_df, 'test_dataset')
        assert validator.dataset_name == 'test_dataset'
        assert len(validator.df) == 100

    def test_validate_required_columns_success(self, sample_df):
        """测试必需列验证 - 成功"""
        validator = DataValidator(sample_df, 'test')
        result = validator.validate_required_columns(['date', 'value1'])
        assert result is True

    def test_validate_required_columns_failure(self, sample_df):
        """测试必需列验证 - 失败"""
        validator = DataValidator(sample_df, 'test')
        result = validator.validate_required_columns(['date', 'nonexistent'])
        assert result is False
        assert len(validator.get_issues()) > 0

    def test_check_missing_values(self, sample_df_with_issues):
        """测试缺失值检查"""
        validator = DataValidator(sample_df_with_issues, 'test')
        missing_stats = validator.check_missing_values()

        assert 'date' in missing_stats
        assert 'value' in missing_stats
        assert missing_stats['date']['count'] == 1  # 一个缺失值

    def test_detect_outliers_iqr(self, sample_df):
        """测试异常值检测 - IQR 方法"""
        validator = DataValidator(sample_df, 'test')
        outliers = validator.detect_outliers('value1', method='iqr')

        # 应该能检测到一些异常值（因为是随机数据）
        assert isinstance(outliers, pd.DataFrame)

    def test_detect_outliers_zscore(self, sample_df):
        """测试异常值检测 - Z-score 方法"""
        validator = DataValidator(sample_df, 'test')
        outliers = validator.detect_outliers('value2', method='zscore', threshold=2.0)

        assert isinstance(outliers, pd.DataFrame)

    def test_check_duplicates(self, sample_df_with_issues):
        """测试重复值检查"""
        validator = DataValidator(sample_df_with_issues, 'test')
        # 只检查 date 列的重复（因为其他列不完全相同）
        duplicates = validator.check_duplicates(subset=['date'])

        assert duplicates == 1  # date 列有一行重复

    def test_generate_quality_report(self, sample_df):
        """测试质量报告生成"""
        validator = DataValidator(sample_df, 'test')
        report = validator.generate_quality_report()

        assert 'dataset_name' in report
        assert 'total_rows' in report
        assert report['total_rows'] == 100
        assert 'memory_usage_mb' in report


class TestDataProcessor:
    """测试 DataProcessor 类"""

    def test_processor_creation(self):
        """测试处理器创建"""
        processor = DataProcessor()
        assert processor is not None
        assert processor.logger is not None

    def test_read_write_csv(self, sample_df):
        """测试 CSV 读写"""
        processor = DataProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入
            filepath = Path(tmpdir) / 'test.csv'
            result = processor.save_csv(sample_df, filepath)
            assert result is True
            assert filepath.exists()

            # 读取
            df_read = processor.read_csv(filepath)
            assert len(df_read) == len(sample_df)
            assert list(df_read.columns) == list(sample_df.columns)

    def test_read_csv_multiple_encodings(self):
        """测试多编码支持"""
        processor = DataProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个 utf-8-sig 编码的文件
            filepath = Path(tmpdir) / 'test_encoding.csv'
            df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
            df.to_csv(filepath, index=False, encoding='utf-8-sig')

            # 应该能成功读取
            df_read = processor.read_csv(filepath)
            assert len(df_read) == 3

    def test_standardize_date(self, sample_df):
        """测试日期标准化"""
        processor = DataProcessor()

        # 转换为字符串
        df_string = sample_df.copy()
        df_string['date'] = df_string['date'].dt.strftime('%Y-%m-%d')

        # 标准化
        result = processor.standardize_date(df_string, 'date', target_format='%Y-%m-%d')

        assert 'date' in result.columns
        assert result['date'].dtype == 'object'  # 字符串格式

    def test_filter_by_date(self, sample_df):
        """测试日期过滤"""
        processor = DataProcessor()

        # 过滤前10天
        result = processor.filter_by_date(
            sample_df,
            'date',
            start_date='2020-01-01',
            end_date='2020-01-10'
        )

        assert len(result) == 10  # 10天
        assert result['date'].min() <= pd.Timestamp('2020-01-10')

    def test_pivot_to_wide(self):
        """测试长宽格式转换"""
        processor = DataProcessor()

        # 创建长格式数据
        long_df = pd.DataFrame({
            'date': ['2020-01-01', '2020-01-01', '2020-01-02', '2020-01-02'],
            'indicator': ['A', 'B', 'A', 'B'],
            'value': [1, 2, 3, 4]
        })

        # 转换为宽格式
        wide_df = processor.pivot_to_wide(long_df, 'date', 'indicator', 'value')

        assert 'date' in wide_df.columns
        assert 'A' in wide_df.columns
        assert 'B' in wide_df.columns
        assert len(wide_df) == 2  # 两个日期

    def test_clean_column_names(self):
        """测试列名清理"""
        processor = DataProcessor()

        df = pd.DataFrame({
            '  Name  ': ['Alice', 'Bob'],
            'Age Value': [25, 30]
        })

        result = processor.clean_column_names(df, strip=True)
        assert 'Name' in result.columns
        assert 'Age Value' in result.columns

    def test_validate_and_report(self, sample_df):
        """测试便捷验证方法"""
        processor = DataProcessor()

        report = processor.validate_and_report(sample_df, 'test_dataset')

        assert 'dataset_name' in report
        assert report['dataset_name'] == 'test_dataset'
        assert 'total_rows' in report


class TestIntegration:
    """集成测试"""

    def test_full_processing_pipeline(self):
        """测试完整数据处理流程"""
        processor = DataProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 创建原始数据
            raw_data = pd.DataFrame({
                'date': pd.date_range('2020-01-01', periods=50).strftime('%Y-%m-%d'),
                'indicator': ['M1'] * 25 + ['M2'] * 25,
                'value': np.random.randn(50) * 10 + 100
            })

            raw_file = Path(tmpdir) / 'raw.csv'
            processor.save_csv(raw_data, raw_file)

            # 2. 读取并处理
            df = processor.read_csv(raw_file)
            df = processor.standardize_date(df, 'date')
            df = processor.filter_by_date(df, 'date', start_date='2020-01-01')

            # 3. 转换格式
            df_wide = processor.pivot_to_wide(df, 'date', 'indicator', 'value')

            # 4. 保存结果
            output_file = Path(tmpdir) / 'processed.csv'
            processor.save_csv(df_wide, output_file)

            # 5. 验证
            assert output_file.exists()
            result = processor.read_csv(output_file)
            assert 'M1' in result.columns
            assert 'M2' in result.columns

    def test_error_handling(self):
        """测试错误处理"""
        processor = DataProcessor()

        # 尝试读取不存在的文件
        with pytest.raises(FileNotFoundError):
            processor.read_csv('/nonexistent/file.csv')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
