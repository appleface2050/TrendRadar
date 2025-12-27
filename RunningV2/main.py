"""
RunningV2 CSV 到 MySQL 同步工具
命令行工具入口
"""
import sys
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')

import argparse
from sync.records_sync import RecordsSync
from sync.rq_sync import RQSync
from sync.shoe_info_sync import ShoeInfoSync


def sync_all():
    """同步所有 CSV 文件"""
    print("\n" + "="*60)
    print("开始同步所有 CSV 文件")
    print("="*60 + "\n")

    try:
        # 同步 shoe_info（跑鞋信息）
        print(">>> 步骤 1/3: 同步跑鞋信息")
        shoe_syncer = ShoeInfoSync()
        shoe_syncer.sync()

        # 同步 rq（RQ 能力值）
        print(">>> 步骤 2/3: 同步 RQ 能力值")
        rq_syncer = RQSync()
        rq_syncer.sync()

        # 同步 records（跑步记录）
        print(">>> 步骤 3/3: 同步跑步记录")
        records_syncer = RecordsSync()
        records_syncer.sync()

        print("\n" + "="*60)
        print("✓ 所有文件同步完成！")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] 同步失败: {e}\n")
        sys.exit(1)


def sync_records():
    """只同步 records.csv"""
    print("\n同步 records.csv")
    print("-" * 60)
    syncer = RecordsSync()
    syncer.sync()


def sync_rq():
    """只同步 rq.csv"""
    print("\n同步 rq.csv")
    print("-" * 60)
    syncer = RQSync()
    syncer.sync()


def sync_shoe():
    """只同步 shoe_info.csv"""
    print("\n同步 shoe_info.csv")
    print("-" * 60)
    syncer = ShoeInfoSync()
    syncer.sync()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='RunningV2 CSV 到 MySQL 同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py sync              # 同步所有 CSV 文件
  python main.py sync-records      # 只同步 records.csv
  python main.py sync-rq           # 只同步 rq.csv
  python main.py sync-shoe         # 只同步 shoe_info.csv
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # sync 子命令
    sync_parser = subparsers.add_parser('sync', help='同步所有 CSV 文件')

    # sync-records 子命令
    sync_records_parser = subparsers.add_parser('sync-records', help='同步 records.csv')

    # sync-rq 子命令
    sync_rq_parser = subparsers.add_parser('sync-rq', help='同步 rq.csv')

    # sync-shoe 子命令
    sync_shoe_parser = subparsers.add_parser('sync-shoe', help='同步 shoe_info.csv')

    # 解析参数
    args = parser.parse_args()

    # 执行对应的命令
    if args.command == 'sync':
        sync_all()
    elif args.command == 'sync-records':
        sync_records()
    elif args.command == 'sync-rq':
        sync_rq()
    elif args.command == 'sync-shoe':
        sync_shoe()
    else:
        # 没有子命令，显示帮助
        parser.print_help()


if __name__ == '__main__':
    main()
