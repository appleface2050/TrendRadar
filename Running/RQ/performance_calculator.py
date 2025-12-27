# jizengxing 6.76
pace ="5:15"
heart_rate = 169

# Jack J 6.9
pace ="5:48"
heart_rate = 150

# tsh 7.11
pace ="4:07"
heart_rate = 165

# 奔跑的EVer 7.53
pace ="5:23"
heart_rate = 148

# pp 7.8
pace ="4:56"
heart_rate = 156

# 奔跑的奔四中年人 7.84
pace ="5:08"
heart_rate = 149

# Tetrahedron 7.94
pace ="5:15"
heart_rate = 144

# 是小彭啊 8.06
pace ="4:52"
heart_rate = 153

# 2024-03-16 8.09

# Stefen 8.2
pace ="4:08"
heart_rate = 177

# 2024-05-12 8.22
pace = "5:06"
heart_rate = 143

# 李金磊 8.42
pace ="5:29"
heart_rate = 130

# 2024-06-10 8.6

# 2024-09-15 8.65

# Tetrahedron 8.71 积极恢复区间 >5'15"
pace ="4:45"
heart_rate = 145


# Shang 2024-07-28 8.73 积极恢复区间 >5'59"
pace ="4:04"
heart_rate = 169

# Shang 2025-10-19 8.75 积极恢复区间 >5'37"
pace ="4:22"
heart_rate = 157

# 姜雨松 8.76
pace ="4:27"
heart_rate = 154

# Xj 8.8
pace ="4:08"
heart_rate = 165

# 码虫 8.83
pace ="4:07"
heart_rate = 165

# 清风与酒 8.91
pace ="4:05"
heart_rate = 165

# 醉仙九恨 8.92
pace ="4:31"
heart_rate = 149

# phony该减肥了 9.0
pace ="3:54"
heart_rate = 171

# 黑影儿TV 9.07
pace ="4:08"
heart_rate = 160

# Junxiao Yi 9.14
pace ="4:11"
heart_rate = 157

# 刘超 9.28
pace ="4:17"
heart_rate = 151

# 努力奔跑的胖球 9.3
pace ="4:27"
heart_rate = 145

# cd 9.3
pace ="3:59"
heart_rate = 162

# 清风与酒 9.38 积极恢复区 >4'53”
pace ="4:00"
heart_rate = 160

# 晒晒爱睡觉 9.4
pace ="3:48"
heart_rate = 168

# 大叔没有树高 9.42
pace ="4:20"
heart_rate = 147

# BO LI 9.45
pace ="3:39"
heart_rate = 174

# 踏雪六十六 9.59
pace ="4:12"
heart_rate = 149

# 吉普瞧国 9.66
pace ="4:38"
heart_rate = 134

# cx 9.71
pace ="3:42"
heart_rate = 167

# 石峰 12.91 积极恢复区 >4'46"
pace ="3:44"
heart_rate = 162

# 马二伟 10.11
pace ="4:09"
heart_rate = 143

# 张庆敏 10.15
pace ="3:16"
heart_rate = 181

# 温柔 10.19
pace ="3:29"
heart_rate = 169

# 刚子1984 10.32
pace ="3:45"
heart_rate = 155


# 对跑步就是执着 10.42
pace ="3:43"
heart_rate = 155

# 长江边的追风少年 10.44
pace ="3:53"
heart_rate = 148

# 王连正 10.59
pace ="3:20"
heart_rate = 170

# 楊章兴 10.6
pace ="3:14"
heart_rate = 175

# 熊猫不打嗝 10.6
pace ="3:35"
heart_rate = 158

# 达也酱 10.62
pace ="3:43"
heart_rate = 152


# mxy 11.13
pace ="3:30"
heart_rate = 154

# 何杰 11.2
pace ="3:08"
heart_rate = 171

# 吴向东 11.25
pace ="3:06"
heart_rate = 172

# 吴向东 11.32
pace ="3:07"
heart_rate = 170

# haochuanpeng 11.37
pace ="3:31"
heart_rate = 150

# 吴向东 11.58
pace ="4:01"
heart_rate = 129

# 贾俄仁加 11.77
pace ="3:02"
heart_rate = 168

# 破二 12.03
pace ="2:50"
heart_rate = 176

# 马瑞 12.91 积极恢复区 >3'46"
pace ="2:48"
heart_rate = 166



min = pace.split(":")[0]
sec = pace.split(":")[1]
km_per_min = int(min) + int(sec) / 60
performance = round(60 / km_per_min / heart_rate * 100, 2)

print(performance)

