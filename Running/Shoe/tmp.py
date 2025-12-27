import datetime

def calculate_pace(total_time, total_distance, unit='mile'):
    # 将总时间转换为分钟
    total_time_minutes = total_time.total_seconds() / 60.0

    # 计算pace
    if unit == 'mile':
        pace = total_time_minutes / total_distance
    elif unit == 'kilometer':
        # 如果总距离单位是公里，则将总距离转换为英里
        total_distance_miles = total_distance / 1.60934
        pace = total_time_minutes / total_distance_miles
    else:
        raise ValueError("Invalid unit. Please use 'mile' or 'kilometer'.")

    return pace

# 示例用法
total_time = datetime.timedelta(minutes=63, seconds=54)  # 总时间为45分钟30秒
total_distance = 4.09  # 总距离为5英里
pace = calculate_pace(total_time, total_distance, unit='kilometer')
print(f"Pace: {pace:.2f} minutes per mile")