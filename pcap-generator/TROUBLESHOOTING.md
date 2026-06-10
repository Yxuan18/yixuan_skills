# 常见问题

## Web app 未运行

先启动 web app：

```bash
cd /path/to/web_apps && python app.py
```

## Connection refused

检查 `settings.ini` 中的 `base_url` 端口是否正确。Web app 必须在指定端口运行。

## "Invalid HTTP response format"

HTTP 头和 body 之间必须有空行（`\n\n`）。多行内容要直接写在 curl 命令中，**不要用 `@filename`**。

## Empty PCAP

HTTP 字符串格式不正确。验证 HTTP 字符串以空行结尾（header 后要有 `\n\n`）。

## Redirect failed

curl 需要加 `-L` 参数跟随重定向。脚本已包含。

## Content-Length mismatch

header 中的 Content-Length 值与实际 body 长度不一致。可用 `fix_content_length()` / `fix_response_length()` 自动修复。

## PCAP 无法用 Wireshark 打开

确保：
- 文件扩展名为 `.pcap`（非 `.pcapng`，除非 Wireshark 配置支持）
- TCP 握手和挥手完整
- 数据包序列正确

## 权限问题

写入 `/tmp` 失败时，指定其他目录：

```python
generate_pcap(req, resp, "output", "/path/to/writable")
```