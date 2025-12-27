import numpy as np

# 示例数据
a = [{"a": 10}, 20, 30, 40, 50, 60]
a = sorted(a, reverse=True)
data = np.array(a)

# 计算某个值的百分位排名（percentile rank）



percentile_rank = np.percentile(data, a)

print(f'% 的百分位排名是：{percentile_rank}')