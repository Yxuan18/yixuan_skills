# -*- coding: utf-8 -*-
"""
QQ Mail — SMTP 发送模块。

环境变量配置：
    SMTP_SERVER   SMTP 服务器，默认 smtp.qq.com
    SMTP_PORT     SMTP 端口，默认 587
    FROM_ADDR     发件人邮箱
    FROM_PASSWORD 发件人邮箱密码（QQ 邮箱为授权码）
    TO_ADDR       收件人邮箱（多个用逗号分隔）
    CC_ADDR       抄送地址（可选）
    SUBJECT       邮件主题
    BODY          邮件正文（HTML 或 plain）
    BODY_TYPE     正文字段类型，默认 html
    ATTACHMENTS   附件路径，多个用逗号分隔（可选）

用法：
    python mail_qq.py --subject "标题" --body "<h1>Hello</h1>" --to "a@qq.com,b@qq.com"
    BODY_FILE=body.html python mail_qq.py --subject "标题" --to "a@qq.com"
"""

from __future__ import annotations

import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename
from typing import Iterable, Sequence

logger = logging.getLogger(__name__)

# ---------- defaults ----------
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))


# ---------- message building ----------

def build_message(
    sender: str,
    recipients: str | Sequence[str],
    subject: str,
    body: str,
    *,
    subtype: str = "html",
    cc: Iterable[str] | None = None,
    bcc: Iterable[str] | None = None,
) -> EmailMessage:
    """
    构造并返回 EmailMessage。

    :param sender:       发件人邮箱。
    :param recipients:   收件人地址或地址列表。
    :param subject:      邮件主题。
    :param body:         邮件正文。
    :param subtype:      正文类型 ``'html'`` 或 ``'plain'``，默认 ``'html'``。
    :param cc:           抄送列表。
    :param bcc:          暗送列表。
    """
    to_list = [recipients] if isinstance(recipients, str) else list(recipients)
    cc_list = list(cc or [])
    bcc_list = list(bcc or [])

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if bcc_list:
        msg["Bcc"] = ", ".join(bcc_list)
    msg["Subject"] = subject
    msg.set_content(body, subtype=subtype, charset="utf-8")
    return msg


def attach_file(msg: EmailMessage, file_path: str) -> None:
    """将本地文件附加到邮件消息。"""
    with open(file_path, "rb") as f:
        data = f.read()
    filename = basename(file_path)
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
        mime = MIMEImage(data)
    else:
        mime = MIMEApplication(data)
    mime.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(mime)


# ---------- sending ----------

def send_email(
    smtp_server: str,
    port: int,
    from_addr: str,
    password: str,
    msg: EmailMessage,
) -> None:
    """通过 SMTP 发送邮件。"""
    with smtplib.SMTP(smtp_server, port, timeout=30) as server:
        server.starttls()
        server.login(from_addr, password)
        # 收集所有收件人地址（To + Cc + Bcc）
        all_recipients = (
            [msg.get("To", ""), msg.get("Cc", ""), msg.get("Bcc", "")]
        )
        recipients = [
            addr.strip()
            for addr in ",".join(all_recipients).split(",")
            if addr.strip()
        ]
        server.sendmail(from_addr, recipients, msg.as_string())
        logger.info("邮件已发送至 %s", recipients)


def send(
    subject: str,
    body: str,
    to_addrs: Sequence[str],
    from_addr: str,
    password: str,
    *,
    smtp_server: str = SMTP_SERVER,
    smtp_port: int = SMTP_PORT,
    subtype: str = "html",
    cc: Iterable[str] | None = None,
    attachments: Sequence[str] | None = None,
) -> None:
    """
    一步发送邮件。

    :param subject:     邮件主题。
    :param body:        邮件正文。
    :param to_addrs:    收件人列表。
    :param from_addr:   发件人邮箱。
    :param password:    发件人密码/授权码。
    :param smtp_server: SMTP 服务器。
    :param smtp_port:   SMTP 端口。
    :param subtype:     正文类型。
    :param cc:          抄送列表。
    :param attachments: 附件路径列表。
    """
    msg = build_message(from_addr, to_addrs, subject, body, subtype=subtype, cc=cc)
    if attachments:
        for path in attachments:
            attach_file(msg, path)
    send_email(smtp_server, smtp_port, from_addr, password, msg)


# ---------- CLI ----------

def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    import argparse

    parser = argparse.ArgumentParser(description="通过 QQ 邮箱 SMTP 发送邮件")
    parser.add_argument("--subject", "-s", default=os.environ.get("SUBJECT", ""))
    parser.add_argument("--body", "-b", default=os.environ.get("BODY", ""))
    parser.add_argument("--body-file", default=os.environ.get("BODY_FILE", ""))
    parser.add_argument("--body-type", default=os.environ.get("BODY_TYPE", "html"),
                        choices=["html", "plain"])
    parser.add_argument("--to", "-t", default=os.environ.get("TO_ADDR", ""))
    parser.add_argument("--cc", default=os.environ.get("CC_ADDR", ""))
    parser.add_argument("--from-addr", default=os.environ.get("FROM_ADDR", ""))
    parser.add_argument("--password", default=os.environ.get("FROM_PASSWORD", ""))
    parser.add_argument("--smtp-server", default=os.environ.get("SMTP_SERVER", SMTP_SERVER))
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("SMTP_PORT", str(SMTP_PORT))))
    parser.add_argument("--attach", "-a", action="append", dest="attachments", default=[],
                        help="附件路径，可多次指定")
    args = parser.parse_args()

    if not args.subject:
        logger.error("缺少 --subject 参数")
        sys.exit(1)
    if not args.to:
        logger.error("缺少 --to 参数")
        sys.exit(1)
    if not args.from_addr or not args.password:
        logger.error("缺少 --from-addr 或 --password 参数，或未设置 FROM_ADDR / FROM_PASSWORD 环境变量")
        sys.exit(1)

    body = args.body
    if args.body_file:
        body = open(args.body_file, encoding="utf-8").read()

    to_list = [a.strip() for a in args.to.split(",") if a.strip()]
    cc_list = [a.strip() for a in args.cc.split(",") if a.strip()] or None

    send(
        subject=args.subject,
        body=body,
        to_addrs=to_list,
        from_addr=args.from_addr,
        password=args.password,
        smtp_server=args.smtp_server,
        smtp_port=args.smtp_port,
        subtype=args.body_type,
        cc=cc_list,
        attachments=args.attachments or None,
    )


if __name__ == "__main__":
    _main()