# def time_to_minutes(time_str):
#     try:
#         hours, minutes, seconds = map(int, time_str.split(':'))
#         total_minutes = hours * 60 + minutes + seconds / 60
#     except Exception as e:
#         total_minutes = 0
#     return total_minutes

import datetime
import time

def pace1_to_pace2(pace1):
    total_seconds = pace1 * 60 # 变为秒数
    # 计算分钟和秒
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    # 格式化为字符串表示法
    pace_string = f"{minutes:02d}:{seconds:02d}"

    return pace_string

def time_to_second(time_str):
    try:
        hours, minutes, seconds = map(int, time_str.split(':'))
        total_second = hours * 60 * 60 + minutes* 60 + seconds
    except Exception as e:
        print(e)
        total_second = 0
    return total_second

def second_to_time(seconds):
    # return datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_string = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
    return time_string

if __name__ == '__main__':
    print(time_to_second("1:00:01"))
    print(second_to_time(100*60))

    print(pace1_to_pace2(6.76))