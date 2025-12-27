#!/usr/bin/env python3
"""
智能上传脚本 - 避免重复上传

原理:
1. 维护一个上传记录文件，记录文件 hash 和对应的文档 ID
2. 上传前检查文件是否已更改
3. 只上传新文件或已更改的文件
4. 可选：删除知识库中的旧版本
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 添加脚本路径
sys.path.append('/home/shang/git/Indeptrader/knowledge-base/scripts')
from bigmodel_kb import BigModelKnowledgeBase

# 配置
CONFIG_FILE = "/home/shang/git/Indeptrader/confidential.json"
UPLOAD_RECORD_FILE = "/home/shang/git/Indeptrader/knowledge-base/.upload_record.json"
KB_ID = "2004906251758215168"


def get_file_hash(file_path):
    """计算文件内容的 hash 值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_upload_record():
    """加载上传记录"""
    if os.path.exists(UPLOAD_RECORD_FILE):
        with open(UPLOAD_RECORD_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_upload_record(record):
    """保存上传记录"""
    with open(UPLOAD_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=4, ensure_ascii=False)


def upload_file_smart(kb, file_path, upload_record, delete_old=False):
    """智能上传单个文件"""
    filename = os.path.basename(file_path)
    file_hash = get_file_hash(file_path)
    file_size = os.path.getsize(file_path)
    file_mtime = os.path.getmtime(file_path)

    # 检查文件是否已上传且未更改
    if filename in upload_record:
        record = upload_record[filename]
        if record.get('hash') == file_hash:
            print(f"⏭️  跳过（未更改）: {filename}")
            return False

        # 文件已更改
        if delete_old and record.get('document_id'):
            print(f"🗑️  删除旧版本: {filename} (文档 ID: {record['document_id']})")
            kb.delete_document(KB_ID, record['document_id'])

    # 上传文件
    print(f"📤 上传: {filename} ({file_size} bytes)")
    result = kb.upload_file(KB_ID, file_path)

    if result.get('success'):
        # 更新上传记录
        upload_record[filename] = {
            'hash': file_hash,
            'document_id': result.get('documentId'),
            'upload_time': datetime.now().isoformat(),
            'file_size': file_size,
            'file_mtime': file_mtime
        }
        return True
    else:
        print(f"❌ 上传失败: {filename}")
        return False


def upload_directory_smart(kb, directory, upload_record, delete_old=False):
    """智能上传目录"""
    supported_extensions = ['.md', '.txt', '.pdf', '.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']

    # 查找所有文件
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                # 跳过上传记录文件本身
                if filename == '.upload_record.json':
                    continue
                files.append(os.path.join(root, filename))

    print(f"📁 扫描目录: {directory}")
    print(f"📊 找到 {len(files)} 个文件\n")

    # 统计
    uploaded = 0
    skipped = 0
    failed = 0

    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {os.path.basename(file_path)}")
        if upload_file_smart(kb, file_path, upload_record, delete_old):
            uploaded += 1
        else:
            skipped += 1
        print()

    # 保存上传记录
    save_upload_record(upload_record)

    print(f"\n📊 上传统计:")
    print(f"  ✅ 已上传: {uploaded}")
    print(f"  ⏭️  跳过: {skipped}")
    print(f"  ❌ 失败: {failed}")
    print(f"  📝 总计: {len(files)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='智能上传知识库文档（避免重复）')
    parser.add_argument('--dir', default='/home/shang/git/Indeptrader/knowledge-base', help='要上传的目录（默认: knowledge-base）')
    parser.add_argument('--delete-old', action='store_true', help='删除知识库中的旧版本')
    args = parser.parse_args()

    print("🚀 智能上传知识库")
    print(f"📁 目录: {args.dir}")
    print(f"🗑️  删除旧版本: {'是' if args.delete_old else '否'}")
    print()

    # 初始化
    kb = BigModelKnowledgeBase()
    upload_record = load_upload_record()

    # 执行上传
    upload_directory_smart(kb, args.dir, upload_record, args.delete_old)

    print("\n✅ 上传完成!")
    print(f"📝 上传记录已保存到: {UPLOAD_RECORD_FILE}")


if __name__ == '__main__':
    main()
