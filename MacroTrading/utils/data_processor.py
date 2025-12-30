"""
数据处理基类

提供通用的数据处理方法
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Optional, Dict
from .data_logger import DataLogger


class DataProcessor:
    """数据处理基类"""

    def __init__(self, logger: Optional[DataLogger] = None):
        """
        初始化处理器

        Args:
            logger: 日志记录器（可选）
        """
        self.logger = logger or DataLogger()

    def read_csv(self,
                filepath: Union[str, Path],
                encodings: List[str] = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312'],
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
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        # 尝试不同编码
        last_error = None
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding, **kwargs)
                self.logger.log_debug(f"成功使用编码 {encoding} 读取文件")
                return df
            except Exception as e:
                last_error = e
                continue

        # 所有编码都失败
        raise ValueError(
            f"无法读取文件 {filepath}，已尝试编码: {', '.join(encodings)}。"
            f"最后一个错误: {str(last_error)}"
        )

    def save_csv(self,
                df: pd.DataFrame,
                filepath: Union[str, Path],
                encoding: str = 'utf-8-sig',
                create_dir: bool = True) -> bool:
        """
        通用 CSV 保存方法

        Args:
            df: 要保存的数据框
            filepath: 保存路径
            encoding: 文件编码
            create_dir: 是否自动创建目录

        Returns:
            是否成功
        """
        try:
            filepath = Path(filepath)

            # 创建目录
            if create_dir:
                filepath.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            df.to_csv(filepath, index=False, encoding=encoding)

            self.logger.log_debug(f"成功保存文件到 {filepath}")
            return True

        except Exception as e:
            self.logger.log_error("save_csv", e)
            return False

    def standardize_date(self,
                        df: pd.DataFrame,
                        date_column: str,
                        target_format: str = '%Y-%m-%d',
                        input_format: Optional[str] = None) -> pd.DataFrame:
        """
        标准化日期格式

        Args:
            df: 数据框
            date_column: 日期列名
            target_format: 目标格式
            input_format: 输入格式（None 表示自动检测）

        Returns:
            处理后的数据框
        """
        result = df.copy()

        try:
            # 转换为 datetime
            if input_format:
                result[date_column] = pd.to_datetime(
                    result[date_column],
                    format=input_format,
                    errors='coerce'
                )
            else:
                result[date_column] = pd.to_datetime(
                    result[date_column],
                    errors='coerce'
                )

            # 检查无效日期
            invalid_count = result[date_column].isna().sum()
            if invalid_count > 0:
                self.logger.log_warning(
                    "日期转换",
                    f"{invalid_count} 个无效日期被转换为 NaT"
                )

            # 转换为目标格式字符串
            result[date_column] = result[date_column].dt.strftime(target_format)

            return result

        except Exception as e:
            self.logger.log_error("standardize_date", e)
            return df

    def filter_by_date(self,
                      df: pd.DataFrame,
                      date_column: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      inclusive: bool = True) -> pd.DataFrame:
        """
        按日期范围过滤

        Args:
            df: 数据框
            date_column: 日期列名
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            inclusive: 是否包含边界

        Returns:
            过滤后的数据框
        """
        result = df.copy()

        try:
            # 确保日期列是 datetime 类型
            if not pd.api.types.is_datetime64_any_dtype(result[date_column]):
                result[date_column] = pd.to_datetime(result[date_column])

            # 应用过滤
            if start_date:
                start_dt = pd.to_datetime(start_date)
                if inclusive:
                    result = result[result[date_column] >= start_dt]
                else:
                    result = result[result[date_column] > start_dt]

            if end_date:
                end_dt = pd.to_datetime(end_date)
                if inclusive:
                    result = result[result[date_column] <= end_dt]
                else:
                    result = result[result[date_column] < end_dt]

            return result

        except Exception as e:
            self.logger.log_error("filter_by_date", e)
            return df

    def pivot_to_wide(self,
                     df: pd.DataFrame,
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
        try:
            # 执行透视
            df_pivot = df.pivot(index=index, columns=columns, values=values)

            # 重置索引
            df_pivot = df_pivot.reset_index()

            # 将索引列转换为字符串（如果是日期）
            if df_pivot[index].dtype.name == 'datetime64[ns]':
                df_pivot[index] = df_pivot[index].dt.strftime('%Y-%m-%d')

            return df_pivot

        except Exception as e:
            self.logger.log_error("pivot_to_wide", e)
            return pd.DataFrame()

    def validate_and_report(self,
                           df: pd.DataFrame,
                           dataset_name: str) -> Dict:
        """
        验证数据并生成报告（便捷方法）

        Args:
            df: 要验证的数据框
            dataset_name: 数据集名称

        Returns:
            质量报告字典
        """
        from .data_validator import DataValidator

        validator = DataValidator(df, dataset_name)
        report = validator.generate_quality_report()

        if validator.has_issues():
            self.logger.log_warning(
                f"数据质量检查 - {dataset_name}",
                f"发现 {len(validator.get_issues())} 个问题"
            )
            for issue in validator.get_issues():
                self.logger.log_warning(issue, "")
        else:
            self.logger.log_success(
                f"数据质量检查 - {dataset_name}",
                "未发现问题"
            )

        # 记录统计信息
        self.logger.log_info(f"📊 数据集: {dataset_name}")
        self.logger.log_info(f"   行数: {report['total_rows']:,}")
        self.logger.log_info(f"   列数: {report['total_columns']}")
        self.logger.log_info(f"   内存占用: {report['memory_usage_mb']} MB")

        if 'date_range' in report:
            self.logger.log_info(
                f"   日期范围: {report['date_range']['start']} 至 {report['date_range']['end']}"
            )

        return report

    def clean_column_names(self,
                          df: pd.DataFrame,
                          strip: bool = True,
                          lower: bool = False,
                          replace_spaces: Optional[str] = None) -> pd.DataFrame:
        """
        清理列名

        Args:
            df: 数据框
            strip: 是否去除首尾空格
            lower: 是否转为小写
            replace_spaces: 空格替换字符（None 表示不替换）

        Returns:
            处理后的数据框
        """
        result = df.copy()

        new_columns = []
        for col in result.columns:
            if strip:
                col = col.strip()
            if lower:
                col = col.lower()
            if replace_spaces is not None:
                col = col.replace(' ', replace_spaces)

            new_columns.append(col)

        result.columns = new_columns
        return result

    def drop_columns_with_high_missing(self,
                                     df: pd.DataFrame,
                                     threshold: float = 0.5) -> pd.DataFrame:
        """
        删除缺失值比例过高的列

        Args:
            df: 数据框
            threshold: 缺失值比例阈值

        Returns:
            处理后的数据框
        """
        result = df.copy()

        missing_ratio = result.isna().sum() / len(result)
        columns_to_drop = missing_ratio[missing_ratio > threshold].index.tolist()

        if columns_to_drop:
            self.logger.log_warning(
                "删除高缺失列",
                f"删除 {len(columns_to_drop)} 列: {', '.join(columns_to_drop)}"
            )
            result = result.drop(columns=columns_to_drop)

        return result
