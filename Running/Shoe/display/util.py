import pandas as pd
import numpy as np
import math

def time_to_minutes(time_str):
    try:
        hours, minutes, seconds = map(int, time_str.split(':'))
        total_minutes = hours * 60 + minutes + seconds / 60
    except Exception as e:
        total_minutes = 0
    return total_minutes

def cal_pace_performance(df):
    df['minutes'] = df['used_time'].apply(time_to_minutes)
    df["km_per_min"] = df['minutes'] / df["distance"]  # 就是pace1 命名有问题，实际是 minutes per km

    df['pace_part1'] = df['km_per_min'].astype(int)

    # 使用 apply 和 math.modf 提取小数部分
    df['decimal_part'] = df['km_per_min'].apply(lambda x: math.modf(x)[0])
    df['pace_part2'] = (60 * df['decimal_part']).astype(int)
    df['pace_part2'] = df['pace_part2'].apply(lambda x: f'0{x}' if x < 10 else x)
    df['pace_part2'] = df['pace_part2'].astype(str)
    df['pace'] = df.apply(lambda row: f"{row['pace_part1']}:{row['pace_part2']}", axis=1)

    df["performance"] = round((60 / df['km_per_min']) / df["average_heart_rate"] * 100, 2)
    df = df.drop(columns=['minutes', "km_per_min", "pace_part1", "decimal_part", "pace_part2"])
    return df