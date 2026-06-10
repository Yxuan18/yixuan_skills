# 直接生成 API

`generate_pcap_direct.py` 直接调用 scapy 生成 PCAP，不依赖 web app。适合复杂场景（如 multipart 上传）。

## 主要函数

### `generate_pcap(request_str, response_str, output_name, output_dir)`

生成 PCAP 文件。

| 参数 | 类型 | 说明 |
|------|------|------|
| `request_str` | `str` | 原始 HTTP 请求（含完整 headers 和 body） |
| `response_str` | `str` | 原始 HTTP 响应 |
| `output_name` | `str` | 输出文件名（不含扩展名） |
| `output_dir` | `str` | 输出目录，默认 `/tmp` |

**返回值：** 生成的 PCAP 文件路径

### `fix_content_length(request_str)`

自动计算并修复 HTTP 请求的 Content-Length。

### `fix_response_length(response_str)`

自动计算并修复 HTTP 响应的 Content-Length。

### `parse_http_content(content)`

解析 HTTP 内容，分离 headers 和 body。返回 `(headers, body)` 元组。

## Python 示例

```python
import sys
sys.path.insert(0, 'scripts')
from generate_pcap_direct import generate_pcap, fix_content_length, fix_response_length

# POST multipart form upload
request = """POST /upload.php HTTP/1.1
Host: example.com
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="phpinfo.php"
Content-Type: application/x-php

<?php phpinfo(); ?>

------WebKitFormBoundary7MA4YWxkTrZu0gW--"""

response = """HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<html><body><h1>File uploaded</h1></body></html>"""

# 修复 Content-Length 并生成
request = fix_content_length(request)
response = fix_response_length(response)
output_path = generate_pcap(request, response, "phpinfo_upload", "/tmp")
print(f"PCAP: {output_path}")
```

## 命令行用法

```bash
python3 scripts/generate_pcap_direct.py [请求内容] [响应内容] [输出文件名] [--output-dir /tmp]
```

直接传参时，内容会被当作普通字符串处理。如需多行内容，建议用 Python 方式调用。