#!/usr/bin/env python3
"""
统计项目中每种编程语言的代码行数
"""

import os
import re
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

# 常见编程语言的文件扩展名映射
LANGUAGE_MAP = {
    'Python': ['.py'],
    'JavaScript': ['.js', '.jsx', '.mjs', '.cjs'],
    'TypeScript': ['.ts', '.tsx'],
    'Java': ['.java'],
    'C': ['.c', '.h'],
    'C++': ['.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx'],
    'C#': ['.cs'],
    'Go': ['.go'],
    'Rust': ['.rs'],
    'Ruby': ['.rb'],
    'PHP': ['.php'],
    'Swift': ['.swift'],
    'Kotlin': ['.kt', '.kts'],
    'Scala': ['.scala'],
    'R': ['.r', '.R'],
    'Shell': ['.sh', '.bash', '.zsh'],
    'HTML': ['.html', '.htm'],
    'CSS': ['.css', '.scss', '.sass', '.less'],
    'SQL': ['.sql'],
    'Markdown': ['.md'],
    'YAML': ['.yaml', '.yml'],
    'JSON': ['.json'],
    'XML': ['.xml'],
}


def parse_gitignore(gitignore_path: str) -> Set[str]:
    """解析 .gitignore 文件，返回需要忽略的目录集合"""
    ignore_dirs = set()
    ignore_patterns = set()

    # 默认忽略 .git 目录
    ignore_dirs.add('.git')

    if not os.path.exists(gitignore_path):
        return ignore_dirs

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 移除通配符，提取目录名
                # 处理以 / 结尾的目录（如 node_modules/）
                if line.endswith('/'):
                    dir_name = line[:-1]
                    # 移除开头的 /
                    if dir_name.startswith('/'):
                        dir_name = dir_name[1:]
                    ignore_dirs.add(dir_name)
                # 处理带通配符的目录模式（如 *.egg-info/）
                elif '*' in line and line.endswith('/'):
                    # 暂时忽略复杂模式
                    ignore_patterns.add(line[:-1])
                # 处理明确的目录名（如 node_modules）
                elif '/' not in line or line.startswith('/'):
                    dir_name = line.lstrip('/')
                    # 如果看起来像目录（不包含扩展名分隔的点）
                    if '.' not in dir_name or dir_name.endswith('/'):
                        ignore_dirs.add(dir_name)
                else:
                    # 其他模式，如果是目录则添加
                    if '.' not in line or line.startswith('.'):
                        ignore_dirs.add(line)

    except Exception as e:
        print(f"警告：读取 .gitignore 文件时出错: {e}")

    return ignore_dirs


def get_language(file_path: str) -> str:
    """根据文件扩展名返回编程语言"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    for language, extensions in LANGUAGE_MAP.items():
        if ext in extensions:
            return language

    return 'Other'


def count_lines(file_path: str) -> int:
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def scan_directory(root_dir: str, ignore_dirs: Set[str]) -> Dict[str, int]:
    """扫描目录并统计每种语言的代码行数"""
    language_lines = defaultdict(int)

    for root, dirs, files in os.walk(root_dir):
        # 移除需要忽略的目录
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            # 跳过隐藏文件
            if file.startswith('.'):
                continue

            # 跳过 CSV 文件
            if file.endswith('.csv'):
                continue

            # 跳过非代码文件
            non_code_extensions = {
                '.txt', '.pkl', '.pdf', '.db', '.sqlite', '.db-wal', '.db-shm',
                '.xls', '.xlsx', '.xlsm', '.log', '.pid', '.scip', '.identifier'
            }
            if any(file.lower().endswith(ext) for ext in non_code_extensions):
                continue

            file_path = os.path.join(root, file)
            language = get_language(file_path)
            lines = count_lines(file_path)

            if lines > 0:
                language_lines[language] += lines

    return dict(language_lines)


def format_number(num: int) -> str:
    """格式化数字，添加千位分隔符"""
    return f"{num:,}"


def print_results(language_lines: Dict[str, int]):
    """打印统计结果"""
    if not language_lines:
        print("未找到任何代码文件")
        return

    # 计算总行数
    total_lines = sum(language_lines.values())

    # 按行数排序
    sorted_languages = sorted(
        language_lines.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # 打印结果
    print("=" * 80)
    print(f"{'语言':<15} {'行数':>20} {'占比':>10}")
    print("=" * 80)

    for language, lines in sorted_languages:
        percentage = (lines / total_lines) * 100
        print(f"{language:<15} {format_number(lines):>20} {percentage:>9.2f}%")

    print("=" * 80)
    print(f"{'总计':<15} {format_number(total_lines):>20} {100.0:>9.2f}%")
    print("=" * 80)


def main():
    """主函数"""
    # 记录开始时间
    start_time = time.time()

    # 获取项目根目录（脚本所在目录的父目录）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print(f"\n正在扫描项目: {project_root}\n")

    # 解析 .gitignore 文件
    gitignore_path = os.path.join(project_root, '.gitignore')
    ignore_dirs = parse_gitignore(gitignore_path)

    print(f"已从 .gitignore 加载 {len(ignore_dirs)} 个忽略规则\n")

    # 扫描目录
    language_lines = scan_directory(str(project_root), ignore_dirs)

    # 打印结果
    print_results(language_lines)

    # 计算并显示运行时间
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\n扫描完成，耗时: {elapsed_time:.2f} 秒\n")


if __name__ == "__main__":
    main()
