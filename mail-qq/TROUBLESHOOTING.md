# 常见问题

## `SMTPAuthenticationError: 535` — 认证失败

- QQ 邮箱需要使用**授权码**，不是登录密码
- 确认授权码正确且未过期
- 参见 `CONFIG.md` 中的"QQ 邮箱授权码获取"步骤

## `SMTPSenderRefused` — 发件人被拒绝

- 确认 `FROM_ADDR` 与登录的 QQ 邮箱一致
- QQ 邮箱 SMTP 服务已开启

## `Connection refused` — 端口连接失败

- 检查 `SMTP_PORT` 是否为 `587`（TLS 端口）
- 检查网络和代理是否拦截了 SMTP 流量

## 代理环境下发送失败

SMTP 需要直连，不支持 HTTP 代理。如需通过代理发送，可考虑：

- 使用 SOCKS 代理转发本地 SMTP 端口
- 或使用支持 SMTP 代理的工具（如 `proxymap`）

## 邮件内容为空

- 使用 `--body-file` 时确保文件路径正确
- 文件编码需要是 UTF-8

## 附件发送失败

- 确认附件文件存在且可读
- 附件会被 base64 编码，大文件可能有发送超时问题，可增加 SMTP `timeout` 参数

## HTML 正文显示为纯文本

- 确认 `--body-type` 为 `html`（默认）
- 检查邮件客户端是否禁用了 HTML 显示