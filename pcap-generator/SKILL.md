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

### 方式一：Web API（推荐简单场景）

先启动 web app：

```bash
cd /path/to/web_apps && python app.py
```

然后用 curl 生成：

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=GET /path HTTP/1.1\nHost: example.com\n\n" \
  -F "response_body=HTTP/1.1 200 OK\nContent-Length: 5\n\nhello" \
  -F "file_name=myfile" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

### 方式二：直接生成（推荐复杂场景）

直接用 scapy 生成，不依赖 web app：

```bash
python3 scripts/generate_pcap_direct.py [请求内容] [响应内容] [输出文件名]
```

## 配置

`settings.ini` 中配置 web app 地址：

```ini
[webapp]
base_url = http://localhost:9900
```

## 常见模式

详见 `PATTERNS.md`（常见 HTTP 请求/响应模式对应的 curl 命令）。

## 直接生成 API

详见 `API.md`（`generate_pcap_direct.py` 函数接口）。

## 常见问题

详见 `TROUBLESHOOTING.md`。