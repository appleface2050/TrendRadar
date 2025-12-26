import csv
import os
import urllib.request
import urllib.error
import time
from datetime import datetime
from typing import Dict, List, Tuple

CSV_FILE = "Macroeconomic/data/fred_monthly_money_supply/money_supply_m1_m2_monthly.csv"
FRED_M1_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M1SL"
FRED_M2_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL"

def load_existing_data() -> Tuple[Dict[str, str], Dict[str, str], str]:
    m1_data = {}
    m2_data = {}
    max_date = ""
    
    if not os.path.exists(CSV_FILE):
        return m1_data, m2_data, max_date
    
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get('DATE', '')
            m1_value = row.get('M1', '')
            m2_value = row.get('M2', '')
            if date:
                if m1_value:
                    m1_data[date] = m1_value
                if m2_value:
                    m2_data[date] = m2_value
                if date > max_date:
                    max_date = date
    
    return m1_data, m2_data, max_date

def fetch_fred_data(url: str) -> List[Tuple[str, str]]:
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

def save_to_csv(m1_data: List[Tuple[str, str]], m2_data: List[Tuple[str, str]], 
                existing_m1: Dict[str, str], existing_m2: Dict[str, str]):
    file_exists = os.path.exists(CSV_FILE)
    m1_new = 0
    m2_new = 0
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(['DATE', 'M1', 'M2'])
        
        all_dates = set(d for d, _ in m1_data) | set(d for d, _ in m2_data)
        sorted_dates = sorted(all_dates)
        
        for date in sorted_dates:
            m1_val = None
            m2_val = None
            
            for d, v in m1_data:
                if d == date:
                    m1_val = v
                    break
            
            for d, v in m2_data:
                if d == date:
                    m2_val = v
                    break
            
            is_new_m1 = date not in existing_m1 and m1_val is not None
            is_new_m2 = date not in existing_m2 and m2_val is not None
            
            if is_new_m1 or is_new_m2:
                if is_new_m1:
                    m1_new += 1
                if is_new_m2:
                    m2_new += 1
                writer.writerow([date, m1_val if m1_val else '', m2_val if m2_val else ''])
    
    return m1_new, m2_new

def main():
    start_time = time.time()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取 FRED 货币供应量数据...")
    
    try:
        existing_m1, existing_m2, max_date = load_existing_data()
        print(f"已加载 M1: {len(existing_m1)} 条, M2: {len(existing_m2)} 条记录")
        
        if max_date:
            print(f"最新记录日期: {max_date}")
        
        m1_data = fetch_fred_data(FRED_M1_URL)
        print(f"从 FRED 获取到 M1: {len(m1_data)} 条记录")
        
        m2_data = fetch_fred_data(FRED_M2_URL)
        print(f"从 FRED 获取到 M2: {len(m2_data)} 条记录")
        
        m1_new, m2_new = save_to_csv(m1_data, m2_data, existing_m1, existing_m2)
        
        if m1_new > 0 or m2_new > 0:
            print(f"新增 M1: {m1_new} 条, M2: {m2_new} 条记录到 {CSV_FILE}")
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
