"""
统一的数据库查询接口
整合所有 Running 项目中的数据库操作逻辑

本模块提取了以下文件中的数据库操作：
- Running/Shoe/display/daily_shoe_performance.py
- Running/Shoe/display/daily_shoe_performance2.py
- Running/Shoe/display/daily_shoe_score.py
- Running/Shoe/display/performance_line_chart.py
- Running/Shoe/display/shoe_table.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# 添加 confs 目录到路径（配置文件）
sys.path.insert(0, '/home/shang/git')

import datetime
import pandas as pd
from sqlalchemy import text
from Running.running_models import (
    engine_running, session,
    DailyShoeStats, DailyShoeScore,
    DailyShoeRecord, DailyShoeStatsCurrentMonth,
    DailyRQRecord
)

# =============================================================================
# 1. DailyShoeStats 相关查询
# =============================================================================

def get_daily_shoe_stats_by_date(today):
    """
    获取指定日期的跑鞋统计数据

    原始位置：Running/Shoe/display/daily_shoe_performance.py:36-37

    Args:
        today: 日期字符串 (YYYY-MM-DD)

    Returns:
        list[DailyShoeStats]: 按top1_performance降序排列的跑鞋统计列表

    示例：
        >>> results = get_daily_shoe_stats_by_date('2025-01-15')
        >>> for stat in results:
        ...     print(f"{stat.shoe}: {stat.top1_performance}")
    """
    return session.query(DailyShoeStats)\
        .filter(DailyShoeStats.date == today)\
        .order_by(DailyShoeStats.top1_performance.desc())\
        .all()


def get_daily_shoe_stats_by_date_with_performance(today):
    """
    获取指定日期的跑鞋统计数据，并计算加权平均performance

    原始位置：Running/Shoe/display/daily_shoe_performance.py:36-56

    Args:
        today: 日期字符串 (YYYY-MM-DD)

    Returns:
        list: 包含跑鞋统计和计算后的performance的字典列表

    示例：
        >>> results = get_daily_shoe_stats_by_date_with_performance('2025-01-15')
        >>> for item in results:
        ...     print(f"{item['shoe']}: {item['performance']}")
    """
    from Running.Shoe.display.util import time_to_minutes

    results = []
    for i in session.query(DailyShoeStats)\
            .filter(DailyShoeStats.date == today)\
            .order_by(DailyShoeStats.top1_performance.desc()):

        # 计算 performance
        try:
            if not i.weight_avg_pace or i.weight_avg_pace == "":
                performance = 0
            else:
                min_sec = i.weight_avg_pace.split(":")
                km_per_min = int(min_sec[0]) + int(min_sec[1]) / 60
                performance = round(60 / km_per_min / i.weight_avg_heart_rate * 100, 2)
        except (ValueError, ZeroDivisionError, IndexError):
            performance = 0

        results.append({
            'date': i.date,
            'shoe': i.shoe,
            'total_used_times': i.total_used_times,
            'total_distance': i.total_distance,
            'avg_distance': i.avg_distance,
            'weight_avg_run_time': i.weight_avg_run_time,
            'weight_avg_heart_rate': i.weight_avg_heart_rate,
            'weight_avg_cadence': i.weight_avg_cadence,
            'weight_avg_stride_length': i.weight_avg_stride_length,
            'top1_pace': i.top1_pace,
            'top1_performance': i.top1_performance,
            'weight_avg_pace': i.weight_avg_pace,
            'performance': performance
        })
    return results


# =============================================================================
# 2. DailyShoeScore 相关查询
# =============================================================================

def get_daily_shoe_score_by_date(today):
    """
    获取指定日期的跑鞋评分数据

    原始位置：Running/Shoe/display/daily_shoe_score.py:36-37

    Args:
        today: 日期字符串 (YYYY-MM-DD)

    Returns:
        list[DailyShoeScore]: 按order升序排列的跑鞋评分列表

    示例：
        >>> scores = get_daily_shoe_score_by_date('2025-01-15')
        >>> for score in scores:
        ...     print(f"{score.order}. {score.shoe}: {score.score}")
    """
    return session.query(DailyShoeScore)\
        .filter(DailyShoeScore.date == today)\
        .order_by(DailyShoeScore.order.asc())\
        .all()


# =============================================================================
# 3. 跑步记录相关查询
# =============================================================================

def get_records_by_date_range(start_date, end_date):
    """
    获取指定日期范围的跑步记录

    原始位置：Running/Shoe/display/performance_line_chart.py:31-34

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        list: 跑步记录列表 [(distance, used_time, average_heart_rate), ...]

    示例：
        >>> records = get_records_by_date_range('2025-01-01', '2025-01-31')
        >>> total_distance = sum(r[0] for r in records)
    """
    sql = text(
        f"select distance, used_time, average_heart_rate "
        f"from `running_shoe_record` "
        f"where date>='{start_date}' and date <= '{end_date}'"
    )
    result = session.execute(sql)
    return result.fetchall()


def calculate_monthly_performance(start_date, end_date):
    """
    计算指定月份的平均performance（加权平均）

    原始位置：Running/Shoe/display/performance_line_chart.py:31-56

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        float: 月度平均performance

    示例：
        >>> avg_perf = calculate_monthly_performance('2025-01-01', '2025-01-31')
        >>> print(f"月度平均performance: {avg_perf}")
    """
    from Running.Shoe.display.util import time_to_minutes

    records = get_records_by_date_range(start_date, end_date)

    mul_distance_performance = 0
    total_distance = 0

    for row in records:
        if row[1] == "0":  # used_time == "0"
            continue
        distance = float(row[0])
        used_time = row[1]
        average_heart_rate = float(row[2])

        minutes = time_to_minutes(used_time)
        km_per_min = minutes / distance
        performance = (60 / km_per_min) / average_heart_rate * 100

        total_distance += distance
        mul_distance_performance += performance * distance

    if total_distance != 0:
        return round(mul_distance_performance / total_distance, 2)
    else:
        return 0


# =============================================================================
# 4. 月度统计相关查询（用于 Performance of the Month 计算）
# =============================================================================

def get_monthly_shoe_performance_stats(month, table_type="month"):
    """
    获取指定月份的跑鞋性能统计

    原始位置：Running/Shoe/display/shoe_table.py:144-152

    Args:
        month: 月份 (YYYY-MM)
        table_type: "month" 或 "history"
            - "month": 使用 running_daily_shoe_stats_current_month 表
            - "history": 使用 running_daily_shoe_stats 表

    Returns:
        dict: {shoe_name: {rq_inc1, top1_pace, top1_performance, rq}}

    示例：
        >>> stats = get_monthly_shoe_performance_stats('2025-01', 'month')
        >>> for shoe, data in stats.items():
        ...     print(f"{shoe}: rq_inc1={data['rq_inc1']}")
    """
    if table_type == "month":
        table_name = "running_daily_shoe_stats_current_month"
    elif table_type == "history":
        table_name = "running_daily_shoe_stats"
    else:
        raise ValueError("table_type must be 'month' or 'history'")

    start_date = f"{month}-01"
    end_date = f"{month}-31"

    sql = text(
        f"""
        SELECT shoe, MAX(rq_inc1) AS rq_inc1, MIN(top1_pace) AS top1_pace,
               MAX(top1_performance) AS top1_performance, MAX(rq1) AS rq
        FROM `{table_name}`
        WHERE DATE >= '{start_date}' AND DATE <= '{end_date}' AND top1_pace != '00:00'
        GROUP BY shoe
        ORDER BY MAX(rq_inc1) DESC
        """
    )

    result = session.execute(sql)
    data = {}
    for row in result:
        rq_inc1 = row[1] if row[1] != "" else "0"
        rq = row[4] if row[4] != "" else "0"
        data[row[0]] = {
            "rq_inc1": rq_inc1,
            "top1_pace": row[2],
            "top1_performance": row[3],
            "rq": rq
        }
    return data


# =============================================================================
# 5. 历史排名相关查询（窗口函数）
# =============================================================================

def get_today_top1_pace_rank(today):
    """
    获取今日top1_pace排名

    原始位置：Running/Shoe/display/shoe_table.py:988-994

    Args:
        today: 日期 (YYYY-MM-DD)

    Returns:
        dict: {shoe: {rank, value}}

    示例：
        >>> ranks = get_today_top1_pace_rank('2025-01-15')
        >>> for shoe, data in ranks.items():
        ...     print(f"{shoe}: 排名 {data['rank']}, 配速 {data['value']}")
    """
    sql = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY top1_pace) AS serial_number,
               shoe, top1_pace, top1_performance, rq1, rq_inc1
        FROM `running_daily_shoe_stats`
        WHERE DATE = '{today}' AND top1_pace != '00:00'
        ORDER BY top1_pace ASC
        """
    )

    result = session.execute(sql)
    data = {}
    for row in result:
        rank = row[0]
        shoe = row[1]
        top1_pace_value = row[2]
        data[shoe] = {"rank": rank, "value": top1_pace_value}
    return data


def get_today_top1_performance_rank(today):
    """
    获取今日top1_performance排名

    原始位置：Running/Shoe/display/shoe_table.py:1006-1012

    Args:
        today: 日期 (YYYY-MM-DD)

    Returns:
        dict: {shoe: {rank, value}}

    示例：
        >>> ranks = get_today_top1_performance_rank('2025-01-15')
        >>> for shoe, data in ranks[0].items():
        ...     print(f"{shoe}: 排名 {data['rank']}, performance {data['value']}")
    """
    sql = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY CAST(top1_performance AS FLOAT)) AS serial_number,
               shoe, top1_pace, top1_performance, rq1, rq_inc1
        FROM `running_daily_shoe_stats`
        WHERE DATE = '{today}' AND top1_pace != '00:00'
        ORDER BY CAST(top1_performance AS FLOAT) DESC
        """
    )

    result = session.execute(sql)
    data = {}

    for row in result:
        rank = row[0]
        shoe = row[1]
        value = row[3]
        data[shoe] = {"rank": rank, "value": value}

    # 反转排名（第1名应该是最高performance）
    count_1 = len(data) + 1
    for k, v in data.items():
        v["rank"] = count_1 - v["rank"]

    return data


def get_today_rq1_rank(today):
    """
    获取今日rq1排名

    原始位置：Running/Shoe/display/shoe_table.py:1026-1032

    Args:
        today: 日期 (YYYY-MM-DD)

    Returns:
        dict: {shoe: {rank, value}}

    示例：
        >>> ranks = get_today_rq1_rank('2025-01-15')
        >>> for shoe, data in ranks.items():
        ...     print(f"{shoe}: 排名 {data['rank']}, RQ {data['value']}")
    """
    sql = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY rq1) AS serial_number,
               shoe, top1_pace, top1_performance, rq1, rq_inc1
        FROM `running_daily_shoe_stats`
        WHERE DATE = '{today}' AND top1_pace != '00:00' AND rq != ''
        ORDER BY rq1 DESC
        """
    )

    result = session.execute(sql)
    data = {}
    for row in result:
        rank = row[0]
        shoe = row[1]
        value = row[4]
        data[shoe] = {"rank": rank, "value": value}

    # 反转排名
    count_1 = len(data) + 1
    for k, v in data.items():
        v["rank"] = count_1 - v["rank"]

    return data


def get_today_rq_inc1_rank(today):
    """
    获取今日rq_inc1排名

    原始位置：Running/Shoe/display/shoe_table.py:1046-1052

    Args:
        today: 日期 (YYYY-MM-DD)

    Returns:
        dict: {shoe: {rank, value}}

    示例：
        >>> ranks = get_today_rq_inc1_rank('2025-01-15')
        >>> for shoe, data in ranks.items():
        ...     print(f"{shoe}: 排名 {data['rank']}, RQ增量 {data['value']}")
    """
    sql = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY rq_inc1) AS serial_number,
               shoe, top1_pace, top1_performance, rq1, rq_inc1
        FROM `running_daily_shoe_stats`
        WHERE DATE = '{today}' AND top1_pace != '00:00' AND rq_inc1 != ''
        ORDER BY rq_inc1 DESC
        """
    )

    result = session.execute(sql)
    data = {}
    for row in result:
        rank = row[0]
        shoe = row[1]
        value = row[5]
        data[shoe] = {"rank": rank, "value": value}

    # 反转排名
    count_1 = len(data) + 1
    for k, v in data.items():
        v["rank"] = count_1 - v["rank"]

    return data


def get_today_all_ranks(today):
    """
    获取今日所有维度排名并计算综合排名

    原始位置：Running/Shoe/display/shoe_table.py:983-1090

    Args:
        today: 日期 (YYYY-MM-DD)

    Returns:
        tuple: (sum_rank, rank_details)
            - sum_rank: dict {shoe: sum_rank_value} - 综合排名（值越小排名越高）
            - rank_details: dict {
                "data_top1_pace": {shoe: {rank, value}},
                "data_top1_performance": {shoe: {rank, value}},
                "data_rq1": {shoe: {rank, value}},
                "data_rq_inc1": {shoe: {rank, value}}
              }

    示例：
        >>> sum_rank, details = get_today_all_ranks('2025-01-15')
        >>> # 获取综合排名前三的鞋子
        >>> for i, (shoe, score) in enumerate(list(sum_rank.items())[:3]):
        ...     print(f"第{i+1}名: {shoe}, 综合得分: {score:.2f}")
    """
    data_top1_pace = get_today_top1_pace_rank(today)
    data_top1_performance = get_today_top1_performance_rank(today)
    data_rq1 = get_today_rq1_rank(today)
    data_rq_inc1 = get_today_rq_inc1_rank(today)

    # 计算 sum_rank
    sum_rank = {}
    shoe_list = list(data_top1_pace.keys())

    for shoe in data_top1_pace:
        rank_top_pace = data_top1_pace[shoe]["rank"]

        # 处理可能缺失的鞋子
        rank_top1_performance = data_top1_performance.get(shoe, {"rank": len(shoe_list)})["rank"]
        rank_rq1 = data_rq1.get(shoe, {"rank": len(shoe_list)})["rank"]
        rank_rq_inc1 = data_rq_inc1.get(shoe, {"rank": len(shoe_list)})["rank"]

        # 为缺失的鞋子添加占位数据
        if shoe not in data_rq1:
            data_rq1[shoe] = {"rank": len(shoe_list), "value": ""}
        if shoe not in data_rq_inc1:
            data_rq_inc1[shoe] = {"rank": len(shoe_list), "value": ""}

        # 计算加权总和
        # 权重说明：
        # - top1_pace: 1.0
        # - top1_performance: 1.2
        # - rq1: 1.0
        # - rq_inc1: 1.25
        sum_rank[shoe] = (
            rank_top_pace +
            1.2 * rank_top1_performance +
            rank_rq1 +
            1.25 * rank_rq_inc1
        )

    # 按sum_rank排序（值越小排名越高）
    sum_rank = dict(sorted(sum_rank.items(), key=lambda item: item[1]))

    rank_details = {
        "data_top1_pace": data_top1_pace,
        "data_top1_performance": data_top1_performance,
        "data_rq1": data_rq1,
        "data_rq_inc1": data_rq_inc1
    }

    return sum_rank, rank_details


# =============================================================================
# 6. 当月详细统计查询
# =============================================================================

def get_current_month_performance_detail(month):
    """
    获取当月performance详细统计

    原始位置：Running/Shoe/display/shoe_table.py:906-914

    Args:
        month: 月份 (YYYY-MM)

    Returns:
        dict: {shoe: {rq_inc1_value, top1_pace_value, top1_performance_value, rq1_value}}

    示例：
        >>> detail = get_current_month_performance_detail('2025-01')
        >>> for shoe, data in detail.items():
        ...     print(f"{shoe}: {data['top1_performance_value']}")
    """
    start_date = f"{month}-01"
    end_date = f"{month}-31"

    sql = text(
        f"""
        SELECT shoe, MAX(rq_inc1) AS rq_inc1, MIN(top1_pace) AS top1_pace,
               MAX(top1_performance) AS top1_performance, MAX(rq1) AS rq1
        FROM `running_daily_shoe_stats_current_month`
        WHERE DATE >= '{start_date}' AND DATE <= '{end_date}' AND top1_pace != '00:00'
        GROUP BY shoe
        ORDER BY top1_performance DESC
        """
    )

    result = session.execute(sql)
    data = {}
    for row in result:
        top1_pace_value = row[2] if row[2] != "00:00" else ""
        top1_performance_value = row[3] if row[3] != "0" else ""
        data[row[0]] = {
            "rq_inc1_value": row[1],
            "top1_pace_value": top1_pace_value,
            "top1_performance_value": top1_performance_value,
            "rq1_value": row[4]
        }
    return data


# =============================================================================
# 7. 工具函数
# =============================================================================

def get_today_date():
    """
    获取今日日期字符串

    Returns:
        str: 今日日期，格式为 YYYY-MM-DD

    示例：
        >>> today = get_today_date()
        >>> print(f"今天是: {today}")
    """
    return datetime.date.today().strftime("%Y-%m-%d")


def get_month_list(start_date, end_date):
    """
    获取日期范围内的月份列表

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        list: 月份列表 ['YYYY-MM', ...]

    示例：
        >>> months = get_month_list('2025-01-01', '2025-03-31')
        >>> print(months)  # ['2025-01', '2025-02', '2025-03']
    """
    from AutomatedFactorResearchSystem.util_date import get_month_list_by_start_end
    return get_month_list_by_start_end(start_date, end_date)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 示例1: 获取今日的跑鞋统计数据
    today = get_today_date()
    print(f"\n=== 今日跑鞋统计 ({today}) ===")
    stats = get_daily_shoe_stats_by_date_with_performance(today)
    for item in stats[:3]:  # 只显示前3个
        print(f"{item['shoe']}: {item['performance']}")

    # 示例2: 获取今日跑鞋评分
    print(f"\n=== 今日跑鞋评分 ({today}) ===")
    scores = get_daily_shoe_score_by_date(today)
    for score in scores[:3]:  # 只显示前3个
        print(f"{score.order}. {score.shoe}: {score.score}")

    # 示例3: 计算本月平均performance
    current_month = today[:7]  # YYYY-MM
    print(f"\n=== 本月Performance ({current_month}) ===")
    avg_perf = calculate_monthly_performance(f"{current_month}-01", f"{current_month}-31")
    print(f"月度平均performance: {avg_perf}")

    # 示例4: 获取今日所有排名
    print(f"\n=== 今日综合排名 ({today}) ===")
    sum_rank, _ = get_today_all_ranks(today)
    for i, (shoe, score) in enumerate(list(sum_rank.items())[:5]):
        print(f"第{i+1}名: {shoe}, 综合得分: {score:.2f}")
