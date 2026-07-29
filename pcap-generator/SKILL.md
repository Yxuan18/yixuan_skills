---
name: pcap-generator
description: |
  生成 PCAP 文件用于 Suricata 规则测试。将自然语言描述转换为 HTTP 请求/响应，自动生成包含完整 TCP 握手和挥手的数据包捕获文件。
  触发词：生成PCAP / create PCAP / test Suricata / simulate HTTP traffic
triggers:
  - "生成PCAP"
  - "create PCAP"
  - "generate packet capture"
  - "test Suricata"
  - "simulate HTTP traffic"
  - "create network traffic"
---

# PCAP Generator

## 快速启动

### 方式一：直接生成（推荐，跨平台支持）

直接用 scapy 生成，不依赖 web app，Linux/Windows 均可用：

```bash
cd pcap-generator/scripts

# 从文件生成
python generate_pcap_direct.py request.txt response.txt output

# 使用模板生成（无需准备文件）
python generate_pcap_direct.py --template \
  --method GET --path /api/test \
  --status "200 OK" --body "Hello World" \
  --output-dir ./pcaps \
  myfile
```

环境变量（可选）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PCAP_SRC_IP` | 源 IP | `192.168.0.1` |
| `PCAP_DST_IP` | 目标 IP | `192.168.0.2` |
| `PCAP_SRC_MAC` | 源 MAC | 内部默认 |
| `PCAP_DST_MAC` | 目标 MAC | 内部默认 |

### 方式二：Web API（依赖 web app）

先启动 web app：

```bash
cd /path/to/web_apps && python app.py
```

然后调用 `generate_pcap.py`：

```bash
python scripts/generate_pcap.py request.txt response.txt myfile
```

## 输出目录

- **方式一**（`generate_pcap_direct.py`）：默认使用系统临时目录
  - Linux/macOS：`/tmp`
  - Windows：`%TEMP%`（通常是 `C:\Users\<user>\AppData\Local\Temp`）
  - 可用 `--output-dir` 或环境变量覆盖

- **方式二**（`generate_pcap.py`）：从 `settings.ini` 读取 `output.default_dir`，无配置时使用系统临时目录

## 配置

`settings.ini` 中配置 web app 地址（方式二专用）：

```ini
[webapp]
base_url = http://localhost:9900

[output]
default_dir = /tmp  # Windows 上建议改为 C:\temp 或留空使用系统默认
```

## 常见模式

详见 `PATTERNS.md`（常见 HTTP 请求/响应模式对应的 curl 命令）。

## 直接生成 API

详见 `API.md`（`generate_pcap_direct.py` 函数接口）。

## 常见问题

详见 `TROUBLESHOOTING.md`。
