#!/usr/bin/env python3
"""
分析项目中被归类为 "Other" 的文件
"""

import os
from pathlib import Path
from collections import defaultdict

# 复制原来的语言映射
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

def get_language(ext: str) -> str:
    """根据文件扩展名返回编程语言"""
    ext = ext.lower()

    for language, extensions in LANGUAGE_MAP.items():
        if ext in extensions:
            return language

    return 'Other'

def analyze_files():
    """分析项目中的文件类型"""
    project_root = Path(__file__).parent.parent

    # 统计所有扩展名
    all_extensions = defaultdict(lambda: {'count': 0, 'files': []})
    other_files = []

    # 需要忽略的目录
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                   'dist', 'build', '.next', '.pytest_cache', 'coverage',
                   '.mypy_cache', 'htmlcov', '*.egg-info'}

    for root, dirs, files in os.walk(project_root):
        # 移除需要忽略的目录
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            # 跳过隐藏文件
            if file.startswith('.'):
                continue

            # 跳过 CSV 文件
            if file.endswith('.csv'):
                continue

            _, ext = os.path.splitext(file)
            rel_path = os.path.relpath(os.path.join(root, file), project_root)

            all_extensions[ext]['count'] += 1
            if len(all_extensions[ext]['files']) < 10:  # 只保留前10个示例
                all_extensions[ext]['files'].append(rel_path)

            if get_language(ext) == 'Other':
                other_files.append(rel_path)

    # 打印结果
    print("=" * 80)
    print("项目中所有文件扩展名统计（按数量排序）:")
    print("=" * 80)

    sorted_exts = sorted(all_extensions.items(), key=lambda x: x[1]['count'], reverse=True)

    for ext, info in sorted_exts:
        language = get_language(ext)
        marker = " ⚠️ Other" if language == 'Other' else ""
        print(f"{ext or '(无扩展名)':<20} 数量: {info['count']:>5} {language}{marker}")

    print("\n" + "=" * 80)
    print(f"所有 'Other' 类型的文件（共 {len(other_files)} 个）:")
    print("=" * 80)

    # 按扩展名分组
    other_by_ext = defaultdict(list)
    for f in other_files:
        _, ext = os.path.splitext(f)
        other_by_ext[ext or '(无扩展名)'].append(f)

    for ext, files in sorted(other_by_ext.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{ext} ({len(files)} 个文件):")
        for f in files[:20]:  # 每种扩展名最多显示20个文件
            print(f"  - {f}")
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")

if __name__ == "__main__":
    analyze_files()
