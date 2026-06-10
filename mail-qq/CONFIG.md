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
# 发件人
FROM_ADDR=502551073@qq.com
FROM_PASSWORD=swifiuqjgtgebjff

# 收件人
TO_ADDR=921086829@qq.com,736804181@qq.com

# SMTP 配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587

# 可选：默认主题和正文
SUBJECT=每日简报
BODY_FILE=today_brief.html
```

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