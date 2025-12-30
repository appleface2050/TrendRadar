#!/bin/bash

# TrendRadar 定时任务管理脚本

case "$1" in
  status)
    echo "📅 当前定时任务配置："
    echo "================================"
    crontab -l
    echo ""
    echo "📊 Cron 服务状态："
    echo "================================"
    systemctl status cron --no-pager | grep -E "Active:|Main PID:"
    ;;

  log)
    echo "📝 最近20条日志："
    echo "================================"
    if [ -f "/home/shang/git/TrendRadar/logs/cron.log" ]; then
      tail -20 /home/shang/git/TrendRadar/logs/cron.log
    else
      echo "日志文件尚未创建"
    fi
    ;;

  disable)
    echo "⚠️  即将禁用定时任务"
    read -p "确认禁用？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      crontab -r
      echo "✅ 定时任务已禁用"
    fi
    ;;

  enable)
    echo "📝 启用定时任务..."
    cat > /tmp/trendradar_crontab.txt << 'EOF'
# TrendRadar 每小时自动推送
# 每小时第0分钟执行
0 * * * * cd /home/shang/git/TrendRadar && /home/shang/git/TrendRadar/run.sh >> /home/shang/git/TrendRadar/logs/cron.log 2>&1
EOF
    crontab /tmp/trendradar_crontab.txt
    echo "✅ 定时任务已启用"
    echo ""
    crontab -l
    ;;

  test)
    echo "🧪 立即执行一次测试..."
    /home/shang/git/TrendRadar/run.sh
    ;;

  next)
    echo "⏰ 下次执行时间："
    date -d "$(date -d '+1 hour' | awk '{print $1" "$2":00:00"}')" "+%Y-%m-%d %H:%M:%S"
    ;;

  *)
    echo "TrendRadar 定时任务管理"
    echo ""
    echo "用法: $0 {status|log|disable|enable|test|next}"
    echo ""
    echo "命令说明："
    echo "  status   - 查看定时任务配置和服务状态"
    echo "  log      - 查看最近的执行日志"
    echo "  disable  - 禁用定时任务"
    echo "  enable   - 启用定时任务"
    echo "  test     - 立即执行一次测试"
    echo "  next     - 查看下次执行时间"
    echo ""
    echo "示例："
    echo "  $0 status   # 查看状态"
    echo "  $0 log      # 查看日志"
    echo "  $0 test     # 测试运行"
    ;;
esac
