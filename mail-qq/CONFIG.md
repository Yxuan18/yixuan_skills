# 配置

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FROM_ADDR` | 发件人邮箱 | 无（必需） |
| `FROM_PASSWORD` | 发件人密码 / 授权码 | 无（必需） |
| `TO_ADDR` | 收件人邮箱（多个用逗号分隔） | 无（必需） |
| `CC_ADDR` | 抄送地址（多个用逗号分隔） | 无 |
| `SMTP_SERVER` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SUBJECT` | 邮件主题 | 无 |
| `BODY` | 邮件正文（直接写在环境变量中） | 无 |
| `BODY_FILE` | 邮件正文文件路径（优先级高于 BODY） | 无 |
| `BODY_TYPE` | 正文字段类型 | `html` |

## QQ 邮箱授权码获取

QQ 邮箱发送需要使用**授权码**而非登录密码：

1. 登录 [mail.qq.com](https://mail.qq.com)
2. 进入 **设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
3. 开启 **SMTP 服务**
4. 按提示发送短信验证，获得 **16 位授权码**
5. 将授权码填入 `FROM_PASSWORD`

## .env 示例

```bash
# 发件人（请替换为你的实际信息）
FROM_ADDR=your_qq@qq.com
FROM_PASSWORD=your_auth_code_here

# 收件人（多个用逗号分隔）
TO_ADDR=recipient@example.com

# SMTP 配置（通常不需要修改）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587

# 可选：默认主题和正文
SUBJECT=每日简报
BODY_FILE=today_brief.html
```

## 安全注意事项

> **重要**：授权码是敏感凭证，请遵循以下原则：

- **不要**将真实凭证提交到 git 仓库。`.env` 文件已在 `.gitignore` 中忽略。
- **不要**把凭证硬编码在脚本或命令行参数中——环境变量和 `.env` 文件是安全的做法。
- **不要**在 CI/CD 日志或错误消息中输出 `FROM_PASSWORD`。
- 如果凭证泄露，立即前往 QQ 邮箱网页重新生成授权码（旧的立即失效）。

获取授权码：登录 [mail.qq.com](https://mail.qq.com) → 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 → 开启 SMTP 服务 → 发送短信验证。

## 文件结构

```
mail-qq/
├── SKILL.md           # 触发词 + 快速启动
├── CONFIG.md          # 环境变量 + 授权码说明
├── TROUBLESHOOTING.md # 常见问题
├── .env.example       # 配置模板
└── scripts/
    └── mail_qq.py     # 主脚本（支持 CLI）
```