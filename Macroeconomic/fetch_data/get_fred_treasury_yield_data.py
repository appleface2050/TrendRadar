import csv
import os
import urllib.request
import urllib.error
import time
from datetime import datetime
from typing import Dict, List, Tuple

CSV_FILE = "Macroeconomic/data/fred_treasury_yield/treasury_yield_daily.csv"
FRED_URLS = {
    'DGS1': "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1",
    'DGS2': "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2",
    'DGS3': "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3",
    'DGS5': "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS5",
    'DGS10': "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
}

def load_existing_data() -> Tuple[Dict[str, Dict[str, str]], str]:
    """加载现有CSV数据

    Returns:
        (所有期限的数据字典, 最新日期)
        数据字典格式: {期限: {日期: 值}}
    """
    all_data = {key: {} for key in FRED_URLS.keys()}
    max_date = ""

    if not os.path.exists(CSV_FILE):
        return all_data, max_date

    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get('DATE', '')
            if date:
                for key in FRED_URLS.keys():
                    value = row.get(key, '')
                    if value:
                        all_data[key][date] = value
                if date > max_date:
                    max_date = date

    return all_data, max_date

def fetch_fred_data(url: str) -> List[Tuple[str, str]]:
    """从FRED获取单个期限的数据

    Args:
        url: FRED数据URL

    Returns:
        [(日期, 值), ...] 列表
    """
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

def save_to_csv(all_yield_data: Dict[str, List[Tuple[str, str]]],
                existing_data: Dict[str, Dict[str, str]]) -> Dict[str, int]:
    """合并并保存数据到CSV

    Args:
        all_yield_data: 所有期限的新数据 {期限: [(日期, 值), ...]}
        existing_data: 现有数据 {期限: {日期: 值}}

    Returns:
        各期限新增记录数 {期限: 新增数量}
    """
    # 确保目录存在
    csv_dir = os.path.dirname(CSV_FILE)
    if csv_dir:
        os.makedirs(csv_dir, exist_ok=True)

    file_exists = os.path.exists(CSV_FILE)
    new_counts = {key: 0 for key in FRED_URLS.keys()}

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            header = ['DATE'] + list(FRED_URLS.keys())
            writer.writerow(header)

        # 收集所有日期
        all_dates = set()
        for data_list in all_yield_data.values():
            for date, _ in data_list:
                all_dates.add(date)
        sorted_dates = sorted(all_dates)

        for date in sorted_dates:
            # 检查是否已有此日期的记录
            has_existing = any(date in existing_data[key] for key in FRED_URLS.keys())

            if not has_existing:
                # 构建此日期的所有期限数据
                row_values = []
                for key in FRED_URLS.keys():
                    value = None
                    for d, v in all_yield_data[key]:
                        if d == date:
                            value = v
                            break
                    row_values.append(value if value else '')

                # 写入行
                writer.writerow([date] + row_values)

                # 统计新增
                for i, key in enumerate(FRED_URLS.keys()):
                    if row_values[i]:
                        new_counts[key] += 1

    return new_counts

def main():
    """主函数"""
    start_time = time.time()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取 FRED 美国国债收益率数据...")

    try:
        # 加载现有数据
        existing_data, max_date = load_existing_data()
        total_existing = sum(len(data) for data in existing_data.values())
        print(f"已加载现有数据: {total_existing} 条记录")
        if max_date:
            print(f"最新记录日期: {max_date}")

        # 获取所有期限的数据
        all_new_data = {}
        for key, url in FRED_URLS.items():
            data = fetch_fred_data(url)
            all_new_data[key] = data
            print(f"从 FRED 获取到 {key}: {len(data)} 条记录")

        # 保存数据
        new_counts = save_to_csv(all_new_data, existing_data)
        total_new = sum(new_counts.values())

        if total_new > 0:
            print(f"\n新增数据统计:")
            for key, count in new_counts.items():
                if count > 0:
                    print(f"  {key}: {count} 条")
            print(f"总计新增: {total_new} 条记录到 {CSV_FILE}")
        else:
            print("没有发现新数据")

        elapsed_time = time.time() - start_time
        print(f"\n完成！耗时: {elapsed_time:.2f} 秒")

    except urllib.error.URLError as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
