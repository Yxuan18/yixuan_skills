---
name: mail-qq
description: |
  通过 QQ 邮箱 SMTP 发送邮件。支持 HTML / plain 正文、抄送、附件，可指定本地 HTML 文件作为邮件正文。
  触发词：发送邮件 / 邮件发送 / send email / 发邮件 / QQ mail / 发送邮件通知
triggers:
  - "发送邮件"
  - "邮件发送"
  - "send email"
  - "发邮件"
  - "QQ mail"
  - "发送邮件通知"
---

# Mail QQ

## 快速启动

### 配置凭证

> **安全提示**：授权码是敏感凭证。请通过 `.env` 文件或环境变量传入，**不要**硬编码在脚本或命令行中。`.env` 文件已在项目 `.gitignore` 中忽略，不会被提交到仓库。

```bash
cp mail-qq/.env.example mail-qq/.env
# 编辑 .env 填入 FROM_ADDR / FROM_PASSWORD 等
```

### 发送邮件

```bash
# 基本用法（参数优先于环境变量）
python mail-qq/scripts/mail_qq.py \
  --subject "标题" \
  --body "<h1>Hello</h1>" \
  --to "收件人@qq.com"

# 从本地 HTML 文件读取正文
BODY_FILE=body.html python mail-qq/scripts/mail_qq.py \
  --subject "今日简报" \
  --to "a@qq.com,b@qq.com" \
  --cc "cc@qq.com" \
  --attach /path/to/image.png

# 多收件人 + 附件
python mail-qq/scripts/mail_qq.py \
  --subject "报告" \
  --body-file report.html \
  --to "team@qq.com" \
  --attach report.pdf \
  --attach chart.png
```

## 配置

详见 `CONFIG.md`（环境变量说明、QQ 邮箱授权码获取方式）。

## 常见问题

详见 `TROUBLESHOOTING.md`。