---
name: pcap-generator
description: Generate PCAP files for Suricata testing via local web app. Use when user wants to create a PCAP file, generate network traffic capture, simulate HTTP requests/responses, test Suricata rules, or create network traffic. Provide natural language description like "GET request to /api/login with 200 response" and this skill will generate and download the PCAP file. Triggers on: "生成PCAP", "create PCAP", "generate packet capture", "test Suricata", "simulate HTTP traffic", "create network traffic".
---

# PCAP Generator Skill

Generate PCAP files by calling the Flask web app API. Configuration is read from `settings.ini`.

## Site Address Configuration

**IMPORTANT: Before generating, check and update `settings.ini` if the web app runs on a different host/port.**

```ini
[webapp]
host = localhost
port = 9900
base_url = http://localhost:9900
```

To change the site address, update the `base_url` in `settings.ini`:
```bash
# Edit settings.ini and change base_url to your new address
# Example: http://192.168.1.100:8080
```

## Workflow

### Step 1: Check Web App Status

```bash
# Read base_url from settings.ini and check health
BASE_URL=$(grep -A1 '\[webapp\]' settings.ini | grep base_url | cut -d'=' -f2 | tr -d ' ')
curl -s "${BASE_URL}/health"
```

If not running, tell user to start:
```bash
cd /path/to/web_apps && python app.py
```

### Step 2: Parse User Request

Convert natural language into HTTP request/response parameters:

| Element | Examples |
|---------|----------|
| Method | GET, POST, PUT, DELETE |
| Path | /api/login, /index.html, /submit |
| Body | form data, JSON, plain text |
| Response | 200 OK, 302 redirect, 404, 502 |

### Step 3: Build Raw HTTP Strings

**Request format:**
```
{METHOD} {PATH} HTTP/1.1
Host: example.com
{Content-Type header if body}
Content-Length: {length}

{body}
```

**Response format:**
```
HTTP/1.1 {STATUS} {MESSAGE}
Content-Type: text/html
Content-Length: {length}
Connection: close

{body}
```

### Step 4: Generate PCAP

**Using curl directly:**
```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=GET /search?q=test' OR '1'='1 HTTP/1.1
Host: example.com

" \
  -F "response_body=HTTP/1.1 500 Internal Server Error
Content-Type: text/html
Content-Length: 21
Connection: close

Internal Server Error" \
  -F "file_name=sql_injection_get" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

**Important: When sending multi-line content in curl:**
- Write multi-line content directly in the curl command (using literal newlines)
- Do NOT use `@filename` to read from file - this causes "Invalid HTTP response format" error
- The Content-Length header value must match the actual body length

### Step 5: Deliver Result

Move to accessible location and inform user:
- File location
- Request/response summary

## Common Patterns

### Pattern 1: GET with 200 JSON Response
```
User: "GET /api/users 返回 JSON 数据"
Request: GET /api/users HTTP/1.1
Host: example.com

Response: HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 15
Connection: close

{"id":1,"name":"a"}
```

### Pattern 2: POST Form with 302 Redirect
```
User: "POST 登录表单到 /login 成功后重定向到 /dashboard"
Request: POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 27

username=admin&password=123

Response: HTTP/1.1 302 Found
Location: /dashboard
Content-Length: 0
Connection: close

```

### Pattern 3: POST with XSS Payload, 200 Response
```
User: "POST XSS payload 到 /comment，返回 200"
Request: POST /comment HTTP/1.1
Host: example.com
Content-Type: text/plain
Content-Length: 29

<script>alert(1)</script>

Response: HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 0
Connection: close

```

### Pattern 4: POST with SQL Injection, 500 Error
```
User: "POST SQL 注入 payload 到 /search，返回 500"
Request: POST /search HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 40

q=test' OR '1'='1

Response: HTTP/1.1 500 Internal Server Error
Content-Type: text/html
Content-Length: 21
Connection: close

Internal Server Error
```

### Pattern 5: GET 404 Not Found
```
User: "GET 一个不存在的页面，返回 404"
Request: GET /nonexistent HTTP/1.1
Host: example.com

Response: HTTP/1.1 404 Not Found
Content-Type: text/html
Content-Length: 49
Connection: close

<html><body><h1>Not Found</h1></body></html>
```

## Direct PCAP Generation (Recommended for Complex Cases)

For complex cases like multipart form uploads, use the direct generation script instead of the web API:

```bash
# 使用 web_apps 的虚拟环境
/Users/xuan/SEC/tstools/.venv/bin/python3 scripts/generate_pcap_direct.py [请求内容] [响应内容] [输出文件名]
```

**示例：生成 POST 文件上传 PCAP**
```python
/Users/xuan/SEC/tstools/.venv/bin/python3 << 'PYEOF'
import sys
sys.path.insert(0, 'scripts')
from generate_pcap_direct import generate_pcap, fix_content_length, fix_response_length

# POST multipart form upload phpinfo.php
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

<html><body><h1>File uploaded: phpinfo.php</h1></body></html>"""

# 生成 PCAP
request = fix_content_length(request)
response = fix_response_length(response)
output_path = generate_pcap(request, response, "phpinfo_upload", "/tmp")
print(f"PCAP 生成成功: {output_path}")
PYEOF
```

**脚本函数：**
- `generate_pcap(request, response, output_name, output_dir)` - 生成 PCAP 文件
- `fix_content_length(request_str)` - 自动修复请求的 Content-Length
- `fix_response_length(response_str)` - 自动修复响应的 Content-Length

## Helper Script Usage

The `scripts/generate_pcap.py` script handles API calls:

```bash
# Basic usage
python scripts/generate_pcap.py <request_file> <response_file> [filename]
```

Note: For multipart form uploads or complex cases, use `generate_pcap_direct.py` instead.

## Distribution

To share this skill with others:

1. **Zip the entire `pcap-generator/` directory**
2. **Recipient places it in their skills folder** (project-level or `~/.claude/skills/`)
3. **Recipient updates `settings.ini`** with their web app URL

The skill is self-contained — no external dependencies beyond Python 3 for the helper script.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Web app not running | Server not started | Tell user to `python app.py` |
| Connection refused | Wrong port/URL | Check `settings.ini` base_url |
| "Invalid HTTP response format" | Line ending issue | Use inline data in curl, not `@filename` |
| Empty PCAP | Invalid request format | Verify HTTP strings end with blank line (`\n\n`) |
| Redirect failed | Curl without -L | Use `-L` to follow redirects |
| Content-Length mismatch | Header/body length mismatch | Manually calculate and set Content-Length |

## Quick Reference

**Site address:** Edit `settings.ini` → `base_url`

**Minimal curl example:**
```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=GET /path HTTP/1.1\nHost: example.com\n\n" \
  -F "response_body=HTTP/1.1 200 OK\nContent-Length: 5\n\nhello" \
  -F "file_name=myfile" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```
