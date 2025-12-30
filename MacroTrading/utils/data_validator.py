"""
数据验证器

提供数据验证和质量检查功能
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DataValidator:
    """数据验证器"""

    def __init__(self, df: pd.DataFrame, dataset_name: str):
        """
        初始化验证器

        Args:
            df: 要验证的数据框
            dataset_name: 数据集名称（用于日志和报告）
        """
        self.df = df.copy()
        self.dataset_name = dataset_name
        self.issues = []

    def validate_date_column(self,
                            column: str,
                            min_date: Optional[str] = None,
                            max_date: Optional[str] = None) -> bool:
        """
        验证日期列

        Args:
            column: 日期列名
            min_date: 最小日期（YYYY-MM-DD）
            max_date: 最大日期（YYYY-MM-DD）

        Returns:
            是否通过验证
        """
        # 检查列是否存在
        if column not in self.df.columns:
            self.issues.append(f"缺少日期列: {column}")
            return False

        try:
            # 尝试转换为日期
            dates = pd.to_datetime(self.df[column], errors='coerce')

            # 检查无效日期
            invalid_count = dates.isna().sum()
            if invalid_count > 0:
                self.issues.append(f"日期列 '{column}' 有 {invalid_count} 个无效值")

            # 检查日期范围
            valid_dates = dates.dropna()
            if len(valid_dates) == 0:
                self.issues.append(f"日期列 '{column}' 没有有效日期")
                return False

            actual_min = valid_dates.min().strftime('%Y-%m-%d')
            actual_max = valid_dates.max().strftime('%Y-%m-%d')

            if min_date:
                min_dt = pd.to_datetime(min_date)
                if valid_dates.min() < min_dt:
                    self.issues.append(
                        f"日期范围从 {actual_min} 开始，早于要求的 {min_date}"
                    )

            if max_date:
                max_dt = pd.to_datetime(max_date)
                if valid_dates.max() > max_dt:
                    self.issues.append(
                        f"日期范围到 {actual_max} 结束，晚于要求的 {max_date}"
                    )

            return len(self.issues) == 0

        except Exception as e:
            self.issues.append(f"验证日期列失败: {str(e)}")
            return False

    def check_missing_values(self, threshold: float = 0.1) -> Dict[str, float]:
        """
        检查缺失值

        Args:
            threshold: 缺失值比例阈值（超过此比例报警）

        Returns:
            各列缺失值统计
        """
        missing_stats = {}

        for column in self.df.columns:
            total = len(self.df)
            missing = self.df[column].isna().sum()
            ratio = missing / total if total > 0 else 0

            missing_stats[column] = {
                'count': int(missing),
                'ratio': round(ratio, 4)
            }

            if ratio > threshold:
                self.issues.append(
                    f"列 '{column}' 缺失值比例 {ratio:.1%} 超过阈值 {threshold:.1%}"
                )

        return missing_stats

    def detect_outliers(self,
                       column: str,
                       method: str = 'iqr',
                       threshold: float = 1.5) -> pd.DataFrame:
        """
        检测异常值

        Args:
            column: 要检测的列
            method: 检测方法 ('iqr' 或 'zscore')
            threshold: 检测阈值
                - IQR 方法: 默认 1.5
                - Z-score 方法: 默认 3.0

        Returns:
            包含异常值的行
        """
        if column not in self.df.columns:
            self.issues.append(f"列 '{column}' 不存在")
            return pd.DataFrame()

        # 只处理数值类型
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            self.issues.append(f"列 '{column}' 不是数值类型，无法检测异常值")
            return pd.DataFrame()

        data = self.df[column].dropna()

        if method == 'iqr':
            # IQR 方法
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            outliers = self.df[
                (self.df[column] < lower_bound) |
                (self.df[column] > upper_bound)
            ].copy()

            if len(outliers) > 0:
                self.issues.append(
                    f"列 '{column}' 检测到 {len(outliers)} 个异常值（IQR 方法）"
                )

        elif method == 'zscore':
            # Z-score 方法
            mean = data.mean()
            std = data.std()

            if std == 0:
                return pd.DataFrame()

            z_scores = np.abs((self.df[column] - mean) / std)
            outliers = self.df[z_scores > threshold].copy()

            if len(outliers) > 0:
                self.issues.append(
                    f"列 '{column}' 检测到 {len(outliers)} 个异常值（Z-score 方法）"
                )
        else:
            self.issues.append(f"未知的异常值检测方法: {method}")
            return pd.DataFrame()

        return outliers

    def check_duplicates(self, subset: Optional[List[str]] = None) -> int:
        """
        检查重复值

        Args:
            subset: 用于判断重复的列列表（None 表示所有列）

        Returns:
            重复行数
        """
        duplicates = self.df.duplicated(subset=subset, keep='first').sum()

        if duplicates > 0:
            subset_str = f"（基于列: {', '.join(subset)}）" if subset else ""
            self.issues.append(f"发现 {duplicates} 行重复记录 {subset_str}")

        return int(duplicates)

    def validate_required_columns(self, columns: List[str]) -> bool:
        """
        验证必需列是否存在

        Args:
            columns: 必需列名列表

        Returns:
            是否全部存在
        """
        missing = [col for col in columns if col not in self.df.columns]

        if missing:
            self.issues.append(f"缺少必需列: {', '.join(missing)}")
            return False

        return True

    def generate_quality_report(self) -> Dict:
        """
        生成数据质量报告

        Returns:
            包含各项质量指标的字典
        """
        report = {
            'dataset_name': self.dataset_name,
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'issues_count': len(self.issues),
            'issues': self.issues.copy(),
            'missing_stats': self.check_missing_values(),
        }

        # 日期范围（如果有日期列）
        date_columns = self.df.select_dtypes(include=['datetime64']).columns
        if len(date_columns) > 0:
            date_col = date_columns[0]
            report['date_range'] = {
                'start': self.df[date_col].min().strftime('%Y-%m-%d'),
                'end': self.df[date_col].max().strftime('%Y-%m-%d')
            }

        return report

    def has_issues(self) -> bool:
        """是否存在问题"""
        return len(self.issues) > 0

    def get_issues(self) -> List[str]:
        """获取所有问题"""
        return self.issues.copy()
