# -*- coding: utf-8 -*-
"""
Tests for pcap-generator scripts.
All tests are offline — scapy import is deferred, so we test the pure-logic helpers.
"""
import pytest
import configparser
import os, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pcap-generator" / "scripts"))

from generate_pcap_direct import (
    parse_http_content,
    fix_content_length,
    fix_response_length,
    _get_output_dir,
    generate_from_template,
)
from generate_pcap import _get_default_dir, generate_pcap


# --- parse_http_content ---

def test_parse_rnrn_delimiter():
    header, body = parse_http_content("GET / HTTP/1.1\r\nHost: a\r\n\r\npayload")
    assert "GET / HTTP/1.1" in header
    assert body == "payload"


def test_parse_nn_delimiter():
    header, body = parse_http_content("GET / HTTP/1.1\nHost: a\n\npayload")
    assert body == "payload"
    assert "\r\n" in header


def test_parse_no_body():
    header, body = parse_http_content("GET / HTTP/1.1\r\nHost: a\r\n\r\n")
    assert body == ""


def test_parse_no_delimiter():
    header, body = parse_http_content("GET / HTTP/1.1")
    assert header == "GET / HTTP/1.1"
    assert body == ""


# --- fix_content_length ---

def test_fix_cl_correct():
    raw = "POST / HTTP/1.1\r\nContent-Length: 5\r\n\r\nhello"
    result = fix_content_length(raw)
    assert "Content-Length: 5" in result


def test_fix_cl_mismatch():
    raw = "POST / HTTP/1.1\r\nContent-Length: 100\r\n\r\nshort"
    result = fix_content_length(raw)
    assert "Content-Length: 5" in result


def test_fix_cl_adds_to_post():
    raw = "POST / HTTP/1.1\r\nHost: example.com\r\n\r\nbody123"
    result = fix_content_length(raw)
    assert "Content-Length: 7" in result


def test_fix_cl_no_add_to_get():
    raw = "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    result = fix_content_length(raw)
    assert "Content-Length" not in result


# --- fix_response_length ---

def test_fix_resp_cl_adds_when_missing():
    raw = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>hi</h1>"
    result = fix_response_length(raw)
    # "<h1>hi</h1>" is 11 bytes, not 9
    assert "Content-Length: 11" in result


def test_fix_resp_cl_mismatch():
    raw = "HTTP/1.1 200 OK\r\nContent-Length: 999\r\n\r\nhi"
    result = fix_response_length(raw)
    assert "Content-Length: 2" in result


# --- cross-platform paths ---

def test_output_dir_explicit(tmp_path):
    result = _get_output_dir(str(tmp_path))
    assert result == tmp_path


def test_output_dir_creates_missing(tmp_path):
    new_dir = tmp_path / "nested" / "dir"
    result = _get_output_dir(str(new_dir))
    assert result == new_dir
    assert new_dir.exists()


def test_output_dir_falls_back_to_system_temp():
    result = _get_output_dir(None)
    assert result == Path(tempfile.gettempdir())


# --- _get_default_dir with proper ConfigParser ---

def test_default_dir_respects_config(tmp_path):
    cfg = configparser.ConfigParser()
    cfg["output"] = {"default_dir": str(tmp_path)}
    result = _get_default_dir(cfg)
    assert result == tmp_path


def test_default_dir_falls_back_to_temp():
    cfg = configparser.ConfigParser()
    result = _get_default_dir(cfg)
    assert result == Path(tempfile.gettempdir())


# --- generate_from_template ---

def test_template_returns_path(tmp_path):
    out = generate_from_template(
        request_type="GET",
        path="/test",
        response_status="200 OK",
        body="ok",
        output_name="test_template",
        output_dir=str(tmp_path),
    )
    assert (tmp_path / "test_template.pcap").exists()
    assert out == str(tmp_path / "test_template.pcap")


# --- generate_pcap webapp not running ---

def test_generate_pcap_reports_webapp_not_running(monkeypatch):
    import generate_pcap as gp

    monkeypatch.setattr(gp, "check_webapp", lambda cfg: (False, "connection refused"))
    ok, msg, path = generate_pcap("req", "resp", "out", config=gp.load_config())
    assert ok is False
    assert "not running" in msg
    assert path is None
