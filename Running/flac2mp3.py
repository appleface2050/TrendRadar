from pydub import AudioSegment
from pydub.utils import which

import os

# AudioSegment.converter = which("ffmpeg")

"""
1. 网易云音乐pc客户端下载音乐 ncm格式。
2. 将ncm格式音乐转换为flac格式。（ncmppGui）
3. 将flac格式音乐保持到onedrive music文件夹
4. 使用labtop运行flac2mp3.py
5. 拷贝到耳机时，耳机要先按两下中间键，进入cf卡模式，接上线，电脑才能识别
"""





#dir = "D:\\OneDriveStore\\OneDrive\\Music"
#dir = "C:\\Users\\Shang\\OneDrive\\Music\\flac_20251025"
dir = "D:\\OneDriveStore\\OneDrive\\Music\\flac_20251025"




files = os.listdir(dir)

for file in files:
    file_dir = dir + "\\"+file
    print(file_dir)
    song = AudioSegment.from_file(file_dir)

    mp3_file_dir = "D:\\tmp\\"+file.split(".flac")[0] + ".mp3"
    print(mp3_file_dir)
    song.export(mp3_file_dir, format="mp3")




