#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# generate_pcap.py - Helper script for PCAP generation via web app API
# Reads configuration from settings.ini

import configparser
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = SCRIPT_DIR / "settings.ini"


def load_config() -> configparser.ConfigParser:
    """Load settings from settings.ini, with cross-platform defaults."""
    config = configparser.ConfigParser()
    if SETTINGS_FILE.exists():
        config.read(SETTINGS_FILE)
    else:
        config["webapp"] = {
            "host": "localhost",
            "port": "9900",
            "base_url": "http://localhost:9900",
        }
        config["output"] = {
            "default_dir": str(Path(tempfile.gettempdir())),
            "pcap_dir": "pcaps",
        }
    return config


def check_webapp(config: configparser.ConfigParser) -> tuple[bool, str]:
    """Check if web app is running."""
    base_url = config.get("webapp", "base_url")
    health_url = f"{base_url}/health"

    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            if response.status == 200:
                return True, base_url
    except urllib.error.URLError as e:
        return False, str(e)

    return False, "Cannot connect to web app"


def _get_default_dir(config: configparser.ConfigParser) -> Path:
    """Get default output directory, cross-platform safe."""
    configured = config.get("output", "default_dir", fallback="")
    if configured:
        p = Path(configured)
    else:
        p = Path(tempfile.gettempdir())
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_pcap(request_body: str, response_body: str, filename: str | None = None, config: configparser.ConfigParser | None = None) -> tuple[bool, str, str | None]:
    """
    Generate PCAP file via web app API.

    Args:
        request_body: Raw HTTP request string
        response_body: Raw HTTP response string
        filename:      Output filename (optional, auto-generated if not provided)
        config:        ConfigParser object (optional, loads from settings.ini if not provided)

    Returns:
        Tuple of (success, message, filepath)
    """
    if config is None:
        config = load_config()

    is_running, base_url = check_webapp(config)
    if not is_running:
        return False, f"Web app not running: {base_url}", None

    if not filename:
        from datetime import datetime
        filename = datetime.now().strftime("%H%M%S")

    # Generate a unique boundary to avoid mismatch with web app
    import secrets
    boundary = secrets.token_hex(16)

    # Build multipart form data
    data_parts = []
    data_parts.append(f"--{boundary}\r\n")
    data_parts.append('Content-Disposition: form-data; name="request_body"\r\n\r\n')
    data_parts.append(request_body + "\r\n")
    data_parts.append(f"--{boundary}\r\n")
    data_parts.append('Content-Disposition: form-data; name="response_body"\r\n\r\n')
    data_parts.append(response_body + "\r\n")
    data_parts.append(f"--{boundary}\r\n")
    data_parts.append('Content-Disposition: form-data; name="file_name"\r\n\r\n')
    data_parts.append(filename + "\r\n")
    data_parts.append(f"--{boundary}--\r\n")

    body = "".join(data_parts)

    try:
        req = urllib.request.Request(
            f"{base_url}/generate_pcap",
            data=body.encode("utf-8"),
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            output_dir = _get_default_dir(config)
            filepath = output_dir / f"{filename}.pcap"

            with open(filepath, "wb") as f:
                f.write(response.read())

            return True, f"PCAP saved to {filepath}", str(filepath)

    except urllib.error.HTTPError as e:
        return False, f"HTTP error {e.code}: {e.reason}", None
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}", None
    except OSError as e:
        return False, f"File write error: {e}", None


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: generate_pcap.py <request_file> <response_file> [filename]")
        print("  Or use stdin for request/response:")
        print("  cat request.txt | python generate_pcap.py - response.txt")
        sys.exit(1)

    request_file = sys.argv[1]
    response_file = sys.argv[2]
    filename = sys.argv[3] if len(sys.argv) > 3 else None

    config = load_config()

    if request_file == "-":
        request_body = sys.stdin.read()
    else:
        request_body = Path(request_file).read_text(encoding="utf-8")

    if response_file == "-":
        response_body = sys.stdin.read()
    else:
        response_body = Path(response_file).read_text(encoding="utf-8")

    success, message, filepath = generate_pcap(request_body, response_body, filename, config)

    print(message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
