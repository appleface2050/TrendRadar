import csv
import os
import urllib.request
import urllib.error
import time
from datetime import datetime
from typing import Dict, List, Tuple

CSV_FILE = "Macroeconomic/data/fred_10y2y_spread/10y2y_spread.csv"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y"

def load_existing_data() -> Tuple[Dict[str, str], str]:
    """加载已存在的数据"""
    data = {}
    max_date = ""

    if not os.path.exists(CSV_FILE):
        return data, max_date

    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get('DATE', '')
            value = row.get('VALUE', '')
            if date and value:
                data[date] = value
                if date > max_date:
                    max_date = date

    return data, max_date

def fetch_fred_data(url: str) -> List[Tuple[str, str]]:
    """从 FRED 获取数据"""
    with urllib.request.urlopen(url, timeout=30) as response:
        content = response.read().decode('utf-8')

    data = []
    lines = content.strip().split('\n')

    for line in lines[1:]:
        parts = line.split(',')
        if len(parts) >= 2:
            date = parts[0].strip()
            value = parts[1].strip()
            if date and value and value != '.':
                data.append((date, value))

    return data

def save_to_csv(data: List[Tuple[str, str]], existing_data: Dict[str, str]) -> int:
    """保存数据到 CSV 文件"""
    file_exists = os.path.exists(CSV_FILE)
    new_count = 0

    # 确保目录存在
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(['DATE', 'VALUE'])

        for date, value in data:
            if date not in existing_data:
                writer.writerow([date, value])
                new_count += 1

    return new_count

def main():
    """主函数"""
    start_time = time.time()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取 FRED 10年期与2年期国债收益率利差数据...")

    try:
        existing_data, max_date = load_existing_data()
        print(f"已加载 {len(existing_data)} 条记录")

        if max_date:
            print(f"最新记录日期: {max_date}")

        data = fetch_fred_data(FRED_URL)
        print(f"从 FRED 获取到 {len(data)} 条记录")

        new_count = save_to_csv(data, existing_data)

        if new_count > 0:
            print(f"新增 {new_count} 条记录到 {CSV_FILE}")
        else:
            print("没有发现新数据")

        elapsed_time = time.time() - start_time
        print(f"完成！耗时: {elapsed_time:.2f} 秒")

    except urllib.error.URLError as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
