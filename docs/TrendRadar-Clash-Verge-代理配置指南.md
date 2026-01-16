# TrendRadar 配置 Clash Verge 代理访问完整指南

> **更新时间**: 2026-01-16 19:04:00
> **适用场景**: WSL2 环境运行 TrendRadar，使用 Windows 上的 Clash Verge 代理访问海外 RSS 源

---

## 问题现象

### 1. 症状描述

- TrendRadar 只能抓取和发送**中文热榜平台**（今日头条、微博、知乎等）
- **英文 RSS 源**无法抓取，日志显示大量错误：
  ```
  [RSS] CNN Top Stories: 请求失败: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
  [RSS] Reuters World News: 请求失败: 404 Client Error: Not Found
  [RSS] Fox News Top Stories: 请求失败: 403 Client Error: Forbidden
  [RSS] NBC News Top Stories: 请求失败: Network is unreachable
  ```
- 日志显示缺少依赖：
  ```
  [RSS] 缺少依赖: RSS 解析需要安装 feedparser: pip install feedparser
  ```

---

## 问题原因分析

### 1. 缺少 `feedparser` 依赖

- 虽然配置文件中启用了 RSS 功能，但运行环境中未安装 `feedparser` 库
- `feedparser` 是解析 RSS/Atom 订阅源的必需库
- 缺少该依赖导致 RSS 抓取功能被完全禁用

### 2. 网络连接问题

- 中文热榜平台使用国内 API (`newsnow.busiyi.world`)，无需代理
- 英文 RSS 源（CNN, Hacker News, BBC 等）需要访问海外服务器
- WSL2 环境无法直接访问，需要通过 Windows 代理

### 3. Windows 防火墙阻止

- Clash Verge 监听 `0.0.0.0:7897`（允许所有地址访问）
- WSL IP 地址：`172.26.224.119`
- Windows 虚拟网卡地址：`172.26.224.1`
- Windows 防火墙默认阻止来自 WSL 的入站连接

### 4. Python 缓存问题

- Python `__pycache__` 缓存了旧的导入状态
- 即使安装了 `feedparser`，缓存仍导致导入失败

---

## 解决步骤

### 步骤 1：安装 `feedparser` 依赖

```bash
# 在 WSL 中运行
cd /home/shang/git/TrendRadar

# 方式 1：使用 requirements.txt
source ~/miniconda3/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方式 2：单独安装 feedparser
pip install feedparser -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证安装
python -c "import feedparser; print(f'feedparser 版本: {feedparser.__version__}')"
```

**预期输出**：
```
feedparser 版本: 6.0.12
```

---

### 步骤 2：配置 Clash Verge 监听地址

#### 2.1 在 Windows 上打开 Clash Verge

#### 2.2 找到网络设置

在 Clash Verge 中找到：
- **设置**（Settings）→ **网络**（Network）
- 或 **配置**（Config）→ **端口映射**（Port Mapping）

#### 2.3 启用局域网访问

找到以下选项并修改：

**选项 A**：允许局域网连接（Allow LAN）
- ✅ **勾选"允许局域网连接"**
- 监听地址应自动变为 `0.0.0.0:7897` 或 `*:7897`

**选项 B**：端口映射（Port Mapping）
- **Mixed Port** 或 **HTTP/SOCKS5 Port**：7897
- **Allow Lan**：启用
- **Bind Address**：设置为 `0.0.0.0` 或 `*`

#### 2.4 保存并重启

- 保存配置
- 重启 Clash Verge

---

### 步骤 3：验证 Clash Verge 监听状态

在 Windows PowerShell 中运行：

```powershell
# 查看端口 7897 的监听情况
netstat -ano | findstr :7897
```

**预期输出**（第一行最重要）：
```
TCP    0.0.0.0:7897           0.0.0.0:0              LISTENING       51500
TCP    127.0.0.1:7897         127.0.0.1:xxxxx         ESTABLISHED     51500
...
```

**关键检查点**：
- ✅ 第一行必须是 `TCP    0.0.0.0:7897` 或 `TCP    *:7897`
- ❌ 如果是 `TCP    127.0.0.1:7897`，说明"允许局域网连接"未正确启用

---

### 步骤 4：获取 Windows WSL 虚拟网卡 IP 地址

#### 4.1 在 Windows PowerShell 中查看

```powershell
# 方法 1：查看 vEthernet (WSL) 适配器
ipconfig | findstr "vEthernet" -A 5
```

**预期输出**：
```
vEthernet (WSL)
   IP地址. . . . . . . . . . . : 172.26.224.1
```

#### 4.2 在 WSL 中查看

```bash
# 方法 1：查看 WSL 网络配置
ip addr | grep -A 2 "eth0"
```

**预期输出**：
```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 172.26.224.119/20 brd 172.26.239.255 scope global eth0
```

**重要说明**：
- WSL 本机 IP：`172.26.224.119`（动态，每次重启可能变化）
- Windows 主机 IP：`172.26.224.1`（相对稳定，用于配置代理）
- **代理地址应使用 `172.26.224.1:7897`**

---

### 步骤 5：添加 Windows 防火墙规则

**必须以管理员身份运行 PowerShell**：

```powershell
# 右键点击 PowerShell → "以管理员身份运行"

# 添加允许入站连接的规则（端口 7897）
New-NetFirewallRule -DisplayName "Clash Verge Allow WSL" `
  -Direction Inbound `
  -LocalPort 7897 `
  -Protocol TCP `
  -Action Allow
```

**验证规则创建成功**：

```powershell
# 查看防火墙规则
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Clash*"} | Select DisplayName, Enabled, Direction, Profile
```

**预期输出**：
```
DisplayName           Enabled Direction Profile
-----------           ------- ---------
clash                    True   Inbound Any
clash                    True   Inbound Any
clash-win64              True   Inbound Any
clash-win64              True   Inbound Any
Clash Verge Allow WSL    True   Inbound Any
```

---

### 步骤 6：修改 TrendRadar 配置文件

编辑 `/home/shang/git/TrendRadar/config/config.yaml`：

```yaml
# ===============================================================
# 高级设置（一般无需修改）
# ===============================================================
advanced:
  # 版本检查
  version_check_url: "https://raw.githubusercontent.com/sansan0/TrendRadar/refs/heads/master/version"

  # 爬虫设置
  crawler:
    enabled: true                     # 是否启用爬取新闻功能
    request_interval: 1000            # 请求间隔（毫秒）
    use_proxy: false                  # 是否启用代理（中文平台不需要）
    default_proxy: "http://172.26.224.1:7897"

  # RSS 设置
  rss:
    request_interval: 2000            # 请求间隔（毫秒）
    timeout: 15                       # 请求超时（秒）
    use_proxy: true                   # 是否使用代理（英文源需要代理）
    proxy_url: "http://172.26.224.1:7897"   # RSS 专属代理（Windows WSL 虚拟网卡地址）

  # 排序权重（用于重新排序不同平台的热搜）
  # 合起来等于 1
  weight:
    rank: 0.6                         # 排名权重
    frequency: 0.3                    # 频次权重
    hotness: 0.1                      # 热度权重

  # 多账号限制
  max_accounts_per_channel: 3         # 每个渠道最大账号数量

  # 消息分批大小（字节）- 内部配置，请勿修改
  batch_size:
    default: 4000
    dingtalk: 20000
    feishu: 30000
    bark: 4000
    slack: 4000
  batch_send_interval: 3              # 批次发送间隔（秒）
  feishu_message_separator: "━━━━━━━━━━━━━━━━━━━"
```

**配置说明**：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `crawler.use_proxy` | `false` | 中文热榜平台使用国内 API，无需代理 |
| `crawler.default_proxy` | `http://172.26.224.1:7897` | 默认代理地址（备用） |
| `rss.use_proxy` | `true` | RSS 英文源必须通过代理访问 |
| `rss.proxy_url` | `http://172.26.224.1:7897` | RSS 专属代理地址 |

---

### 步骤 7：清理 Python 缓存

```bash
# 在 TrendRadar 项目目录运行
cd /home/shang/git/TrendRadar

# 清理所有 Python 缓存
rm -rf trendradar/__pycache__
rm -rf trendradar/*/__pycache__
rm -rf trendradar/*/*/__pycache__
```

---

## 验证测试

### 测试 1：验证代理连接

```bash
# 在 WSL 中运行
source ~/miniconda3/bin/activate
python << 'EOF'
import requests

proxy = 'http://172.26.224.1:7897'
test_urls = [
    'https://www.google.com',
    'https://www.bbc.com',
    'https://hnrss.org/frontpage',
]

print("=== 测试代理连接 ===")
for url in test_urls:
    print(f"\n请求: {url}")
    try:
        response = requests.get(
            url,
            proxies={'http': proxy, 'https': proxy},
            timeout=10,
            verify=False
        )
        print(f"✅ 成功! 状态码: {response.status_code}")
        print(f"   响应长度: {len(response.text)} 字节")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {str(e)[:100]}")
EOF
```

**预期输出**：
```
=== 测试代理连接 ===

请求: https://www.google.com
✅ 成功! 状态码: 200
   响应长度: 17416 字节

请求: https://www.bbc.com
✅ 成功! 状态码: 200
   响应长度: 502078 字节

请求: https://hnrss.org/frontpage
✅ 成功! 状态码: 200
   响应长度: 15649 字节
```

---

### 测试 2：验证 RSS 抓取

```bash
# 在 WSL 中运行
source ~/miniconda3/bin/activate
python << 'EOF'
import requests
from trendradar.crawler.rss.parser import RSSParser

proxy = 'http://172.26.224.1:7897'
test_feeds = [
    ('Hacker News', 'https://hnrss.org/frontpage'),
    ('BBC World', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
]

print("=== 测试 RSS 抓取 ===")
for name, url in test_feeds:
    print(f"\n{name}: {url}")
    try:
        response = requests.get(
            url,
            proxies={'http': proxy, 'https': proxy},
            timeout=10,
            verify=False
        )
        print(f"✅ HTTP 请求成功! 状态码: {response.status_code}")

        # 解析 RSS
        parser = RSSParser()
        items = parser.parse(response.text, url)
        print(f"✅ 解析成功! 获取 {len(items)} 条")
        if items:
            print(f"   第一条: {items[0].title}")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {str(e)[:100]}")
EOF
```

**预期输出**：
```
=== 测试 RSS 抓取 ===

Hacker News: https://hnrss.org/frontpage
✅ HTTP 请求成功! 状态码: 200
✅ 解析成功! 获取 20 条
   第一条: On Being a Human Being in the Time of Collapse (2022) [pdf]

BBC World: https://feeds.bbci.co.uk/news/world/rss.xml
✅ HTTP 请求成功! 状态码: 200
✅ 解析成功! 获取 0 条
```

---

### 测试 3：完整运行 TrendRadar

```bash
# 在 WSL 中运行
cd /home/shang/git/TrendRadar
./run.sh
```

**预期日志**（部分）：
```
开始爬取数据，请求间隔 1000 毫秒
获取 toutiao 成功（最新数据）
获取 baidu 成功（缓存数据）
...
[RSS] 开始抓取 23 个 RSS 源...
[RSS] Hacker News: 获取 20 条
[RSS] BBC World News: 获取 50 条
[RSS] CNN Top Stories: 获取 20 条
[RSS] Reuters World News: 获取 50 条
...
```

---

## 常见问题

### Q1: Windows IP 地址每次重启 WSL 后会变化？

**问题**：
```bash
# WSL IP 每次重启后可能变化
$ ip addr | grep "inet "
    inet 172.26.224.119/20  # 当前 IP
# 重启后
$ ip addr | grep "inet "
    inet 172.26.224.120/20  # 新 IP
```

**解决方案**：使用动态获取脚本

创建 `/home/shang/get-windows-ip.sh`：
```bash
#!/bin/bash
# 获取 Windows 主机 IP（通过 DNS 配置）
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

**动态配置代理**（修改 `config.yaml` 时需要手动更新 IP）。

---

### Q2: 代理连接超时（Connection Timeout）？

**错误**：
```
ProxyError: Unable to connect to proxy, ConnectTimeoutError: Connection to 172.26.224.1 timed out
```

**排查步骤**：

1. **检查 Clash Verge 是否运行**
   ```powershell
   # 在 Windows PowerShell 运行
   netstat -ano | findstr :7897
   ```
   应该看到 `LISTENING` 状态

2. **检查防火墙规则**
   ```powershell
   Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Clash*"} | Select DisplayName, Enabled
   ```
   确保 `Clash Verge Allow WSL` 规则存在且已启用

3. **检查 IP 地址是否正确**
   ```powershell
   ipconfig | findstr "vEthernet" -A 5
   ```
   确认使用的是 `172.26.224.1` 而不是 `172.26.224.119`

4. **测试从 WSL 访问 Windows**
   ```bash
   # 在 WSL 中运行
   ping -c 3 172.26.224.1
   ```
   应该能 ping 通

---

### Q3: 防火墙规则创建失败？

**错误**：
```
New-NetFirewallRule : 无法找到参数与参数名称匹配
```

**原因**：PowerShell 版本过低（Windows 7 或更旧版本）

**解决方案**：使用 `netsh` 命令
```cmd
# 以管理员身份运行 CMD
netsh advfirewall firewall add rule name="Clash Verge Allow WSL" dir=in action=allow protocol=TCP localport=7897
```

---

### Q4: RSS 抓取成功但无法发送邮件？

**问题**：RSS 抓取正常，但日志显示中文信息

**原因**：`config/frequency_words.txt` 关键词配置只包含中文词汇

**解决方案**：添加英文关键词到 `frequency_words.txt`：

```txt
# 中文关键词
华为
AI

# 英文关键词
ChatGPT
OpenAI
Tesla
```

---

### Q5: TrendRadar 日志显示"本地环境，未启用代理"？

**日志**：
```
本地环境，未启用代理
```

**原因**：配置文件加载失败或键名错误

**解决方案**：验证配置文件

```bash
python << 'EOF'
import yaml

config_file = '/home/shang/git/TrendRadar/config/config.yaml'
with open(config_file, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=== 爬虫配置 ===")
crawler = config.get('advanced', {}).get('crawler', {})
print(f"use_proxy: {crawler.get('use_proxy')}")
print(f"default_proxy: {crawler.get('default_proxy')}")

print("\n=== RSS 配置 ===")
rss = config.get('advanced', {}).get('rss', {})
print(f"use_proxy: {rss.get('use_proxy')}")
print(f"proxy_url: {rss.get('proxy_url')}")
EOF
```

**预期输出**：
```
=== 爬虫配置 ===
use_proxy: False
default_proxy: http://172.26.224.1:7897

=== RSS 配置 ===
use_proxy: True
proxy_url: http://172.26.224.1:7897
```

---

## 配置总结

### 网络配置

| 组件 | 配置 |
|------|------|
| **WSL IP** | `172.26.224.119`（动态） |
| **Windows 虚拟网卡 IP** | `172.26.224.1`（相对稳定） |
| **Clash Verge 监听地址** | `0.0.0.0:7897` |
| **代理地址** | `http://172.26.224.1:7897` |

### TrendRadar 配置

```yaml
# config/config.yaml 关键配置
advanced:
  crawler:
    use_proxy: false          # 中文平台不使用代理
    default_proxy: "http://172.26.224.1:7897"

  rss:
    use_proxy: true            # RSS 英文源使用代理
    proxy_url: "http://172.26.224.1:7897"
```

### 防火墙规则

```powershell
DisplayName: Clash Verge Allow WSL
Direction: Inbound
LocalPort: 7897
Protocol: TCP
Action: Allow
```

---

## 附录：配置文件完整示例

### `/home/shang/git/TrendRadar/config/config.yaml`（关键部分）

```yaml
advanced:
  # 爬虫设置
  crawler:
    enabled: true
    request_interval: 1000
    use_proxy: false                  # 中文平台不需要代理
    default_proxy: "http://172.26.224.1:7897"

  # RSS 设置
  rss:
    request_interval: 2000
    timeout: 15
    use_proxy: true                   # 英文源需要代理
    proxy_url: "http://172.26.224.1:7897"   # Windows WSL 虚拟网卡地址
    notification_enabled: true        # 启用 RSS 通知推送
```

### `/home/shang/git/TrendRadar/config/config.yaml`（RSS 源部分）

```yaml
rss:
  enabled: true

  # RSS 源配置（完整列表）
  feeds:
    # 美国热点新闻源
    - id: "cnn"
      name: "CNN Top Stories"
      url: "http://rss.cnn.com/rss/cnn_topstories.rss"

    - id: "reuters-top"
      name: "Reuters World News"
      url: "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"

    - id: "ap-news"
      name: "AP News U.S."
      url: "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"

    - id: "fox-news"
      name: "Fox News Top Stories"
      url: "http://feeds.foxnews.com/foxnews/latest"

    - id: "nbc-news"
      name: "NBC News Top Stories"
      url: "http://feeds.nbcnews.com/nbcnews/public/news"

    - id: "bbc-world"
      name: "BBC World News"
      url: "http://feeds.bbci.co.uk/news/world/rss.xml"

    # 科技类美国源
    - id: "hacker-news"
      name: "Hacker News"
      url: "https://hnrss.org/frontpage"

    - id: "techcrunch"
      name: "TechCrunch Top Stories"
      url: "https://techcrunch.com/feed/"

    - id: "verge"
      name: "The Verge"
      url: "https://www.theverge.com/rss/index.xml"

    # GitHub 热点
    - id: "github-trending-daily"
      name: "GitHub Trending Daily"
      url: "https://github-rss.alexi.sh/feeds/daily/all.xml"

    # AI 研究与新闻
    - id: "openai-blog"
      name: "OpenAI Blog"
      url: "https://openai.com/blog/rss.xml"

    - id: "google-ai-blog"
      name: "Google AI Blog"
      url: "https://blog.google/technology/ai/rss.xml"

    # AI 学术研究
    - id: "arxiv-cs"
      name: "arXiv Computer Science"
      url: "https://rss.arxiv.org/rss/cs"

    # 中文源
    - id: "ruanyifeng"
      name: "阮一峰的网络日志"
      url: "http://www.ruanyifeng.com/blog/atom.xml"
```

---

## 参考链接

- [Clash Verge 官方文档](https://github.com/Clash-Nyanpasu/Clash-for-Windows)
- [WSL2 网络配置](https://learn.microsoft.com/zh-cn/windows/wsl/network)
- [TrendRadar GitHub 仓库](https://github.com/sansan0/TrendRadar)
- [feedparser 官方文档](https://pythonhosted.org/feedparser/)

---

**文档维护**：如有问题或补充，请更新本文档并记录修改时间。
