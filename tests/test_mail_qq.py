# -*- coding: utf-8 -*-
"""
Tests for mail-qq/scripts/mail_qq.py
SMTP is not actually invoked — EmailMessage objects are built and inspected.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from email.message import EmailMessage

# Patch sys.argv before importing mail_qq so argparse doesn't read pytest args
_original_argv = sys.argv


def _make_argv(args: list[str]) -> None:
    sys.argv = ["mail_qq.py"] + args


class TestBuildMessage:
    def test_sets_all_headers(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message(
            sender="from@example.com",
            recipients=["to@example.com"],
            subject="Test Subject",
            body="<h1>Hello</h1>",
            subtype="html",
        )
        assert msg["From"] == "from@example.com"
        assert msg["To"] == "to@example.com"
        assert msg["Subject"] == "Test Subject"

    def test_accepts_string_recipient(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message("a@a.com", "b@b.com", "s", "b")
        assert msg["To"] == "b@b.com"

    def test_accepts_list_recipients(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message("a@a.com", ["b@b.com", "c@c.com"], "s", "b")
        assert "b@b.com" in msg["To"]
        assert "c@c.com" in msg["To"]

    def test_adds_cc_header(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message("a@a.com", "b@b.com", "s", "b", cc=["cc@cc.com"])
        assert msg["Cc"] == "cc@cc.com"

    def test_omits_cc_when_empty(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message("a@a.com", "b@b.com", "s", "b", cc=[])
        assert msg.get("Cc") is None

    def test_plain_subtype(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message

        msg = build_message("a@a.com", "b@b.com", "s", "plain text", subtype="plain")
        # get_content() may include a trailing newline (MIME canonical form)
        assert msg.get_content().rstrip("\n") == "plain text"


class TestAttachFile:
    def test_creates_mime_image_for_png(self, tmp_path):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import attach_file

        img = tmp_path / "chart.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake png data")
        msg = EmailMessage()
        attach_file(msg, str(img))
        assert len(msg.get_payload()) == 1
        assert msg.get_payload()[0].get_content_type() == "image/png"

    def test_creates_mime_application_for_pdf(self, tmp_path):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import attach_file

        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake pdf data")
        msg = EmailMessage()
        attach_file(msg, str(pdf))
        assert len(msg.get_payload()) == 1
        assert msg.get_payload()[0].get_content_type() == "application/pdf"

    def test_preserves_filename(self, tmp_path):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import attach_file

        f = tmp_path / "myfile.txt"
        f.write_text("content")
        msg = EmailMessage()
        attach_file(msg, str(f))
        disp = msg.get_payload()[0].get("Content-Disposition", "")
        assert "myfile.txt" in disp


class TestSendEmail:
    def test_uses_starttls_and_login(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import build_message, send_email

        msg = build_message("a@a.com", "b@b.com", "s", "b")
        mock_server = MagicMock()
        with patch("mail_qq.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value = mock_server
            send_email("smtp.example.com", 587, "a@a.com", "password", msg)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("a@a.com", "password")
            mock_server.sendmail.assert_called_once()


class TestSend:
    def test_send_constructs_and_sends(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import send

        with patch("mail_qq.send_email") as mock_send:
            send(
                subject="Daily Report",
                body="<p>Report content</p>",
                to_addrs=["team@example.com"],
                from_addr="noreply@example.com",
                password="secret",
            )
            mock_send.assert_called_once()
            msg = mock_send.call_args[0][4]
            assert msg["Subject"] == "Daily Report"
            assert "Report content" in msg.get_body().get_content()

    def test_send_with_attachments(self, tmp_path):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import send

        att = tmp_path / "report.txt"
        att.write_text("data")
        with patch("mail_qq.send_email"):
            send(
                subject="With Attachment",
                body="body",
                to_addrs=["a@a.com"],
                from_addr="a@a.com",
                password="p",
                attachments=[str(att)],
            )

    def test_send_with_cc(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import send

        with patch("mail_qq.send_email") as mock_send:
            send(
                subject="CC Test",
                body="body",
                to_addrs=["to@example.com"],
                from_addr="from@example.com",
                password="p",
                cc=["cc@example.com"],
            )
            msg = mock_send.call_args[0][4]
            assert msg["Cc"] == "cc@example.com"


class TestCLIFailsGracefully:
    """Test that CLI exits with non-zero when required args are missing."""

    def test_exits_without_subject(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import _main

        with patch("mail_qq.send"):
            with patch.object(sys, "argv", ["mail_qq.py"]):
                with pytest.raises(SystemExit) as exc_info:
                    _main()
        # argparse exits 2 when a required arg is missing
        assert exc_info.value.code in (1, 2)

    def test_exits_without_to(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import _main

        with patch.dict(os.environ, {
            "FROM_ADDR": "a@a.com",
            "FROM_PASSWORD": "p",
            "SUBJECT": "test",
        }):
            with patch("mail_qq.send"):
                with patch.object(sys, "argv", ["mail_qq.py", "--subject", "test"]):
                    with pytest.raises(SystemExit) as exc_info:
                        _main()
        assert exc_info.value.code in (1, 2)

    def test_exits_without_credentials(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "mail-qq" / "scripts"))
        from mail_qq import _main

        with patch.dict(os.environ, {}, clear=True):
            with patch("mail_qq.send"):
                with patch.object(sys, "argv", ["mail_qq.py", "--subject", "test", "--to", "a@a.com"]):
                    with pytest.raises(SystemExit) as exc_info:
                        _main()
        assert exc_info.value.code in (1, 2)
