# 常见模式

## 模式速查

| 场景 | curl 示例 |
|------|--------|
| GET 200 JSON | 见下方 Pattern 1 |
| POST 表单 + 302 重定向 | 见下方 Pattern 2 |
| POST XSS payload, 200 | 见下方 Pattern 3 |
| POST SQL 注入, 500 | 见下方 Pattern 4 |
| GET 404 | 见下方 Pattern 5 |

## Pattern 1: GET + 200 JSON

```
请求: GET /api/users HTTP/1.1
响应: HTTP/1.1 200 OK + JSON
```

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=GET /api/users HTTP/1.1\nHost: example.com\n\n" \
  -F "response_body=HTTP/1.1 200 OK\nContent-Type: application/json\nContent-Length: 15\n\n{\"id\":1,\"name\":\"a\"}" \
  -F "file_name=get_json" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

## Pattern 2: POST 表单 + 302 重定向

```
请求: POST /login 表单数据
响应: HTTP/1.1 302 Found → /dashboard
```

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=POST /login HTTP/1.1\nHost: example.com\nContent-Type: application/x-www-form-urlencoded\nContent-Length: 27\n\nusername=admin&password=123" \
  -F "response_body=HTTP/1.1 302 Found\nLocation: /dashboard\nContent-Length: 0\n\n" \
  -F "file_name=post_login" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

## Pattern 3: POST XSS payload, 200

```
请求: POST /comment 带 XSS payload
响应: HTTP/1.1 200 OK
```

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=POST /comment HTTP/1.1\nHost: example.com\nContent-Type: text/plain\nContent-Length: 29\n\n<script>alert(1)</script>" \
  -F "response_body=HTTP/1.1 200 OK\nContent-Type: text/html\nContent-Length: 0\n\n" \
  -F "file_name=post_xss" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

## Pattern 4: POST SQL 注入, 500

```
请求: POST /search 带 SQL 注入 payload
响应: HTTP/1.1 500 Internal Server Error
```

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=POST /search HTTP/1.1\nHost: example.com\nContent-Type: application/x-www-form-urlencoded\nContent-Length: 40\n\nq=test' OR '1'='1" \
  -F "response_body=HTTP/1.1 500 Internal Server Error\nContent-Type: text/html\nContent-Length: 21\n\nInternal Server Error" \
  -F "file_name=post_sqli" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

## Pattern 5: GET 404

```
请求: GET /nonexistent
响应: HTTP/1.1 404 Not Found
```

```bash
BASE_URL=$(grep base_url settings.ini | cut -d'=' -f2 | tr -d ' ')
curl -s -L -o output.pcap \
  -F "request_body=GET /nonexistent HTTP/1.1\nHost: example.com\n\n" \
  -F "response_body=HTTP/1.1 404 Not Found\nContent-Type: text/html\nContent-Length: 49\n\n<html><body><h1>Not Found</h1></body></html>" \
  -F "file_name=get_404" \
  -F "generate=生成" \
  "${BASE_URL}/generate_pcap"
```

## 注意事项

- **多行内容直接写在 curl 命令中**，不要用 `@filename` 读取，否则会报 "Invalid HTTP response format"
- **Content-Length 值必须与实际 body 长度一致**
- **HTTP 头和 body 之间要有空行**（`\n\n`）