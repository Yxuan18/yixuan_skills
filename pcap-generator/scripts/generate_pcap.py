#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# generate_pcap.py - Helper script for PCAP generation via web app API
# Reads configuration from settings.ini

import os
import sys
import configparser
import urllib.request
import urllib.parse
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, 'settings.ini')

def load_config():
    """Load settings from settings.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(SETTINGS_FILE):
        config.read(SETTINGS_FILE)
        return config
    else:
        # Return defaults if settings.ini not found
        config['webapp'] = {
            'host': 'localhost',
            'port': '9900',
            'base_url': 'http://localhost:9900'
        }
        config['output'] = {
            'default_dir': '/tmp',
            'pcap_dir': 'pcaps'
        }
        return config

def check_webapp(config):
    """Check if web app is running"""
    base_url = config.get('webapp', 'base_url')
    health_url = f"{base_url}/health"

    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            if response.status == 200:
                return True, base_url
    except Exception as e:
        return False, str(e)

    return False, "Cannot connect to web app"

def generate_pcap(request_body, response_body, filename=None, config=None):
    """
    Generate PCAP file via web app API.

    Args:
        request_body: Raw HTTP request string
        response_body: Raw HTTP response string
        filename: Output filename (optional, auto-generated if not provided)
        config: ConfigParser object (optional, loads from settings.ini if not provided)

    Returns:
        Tuple of (success, message, filepath)
    """
    if config is None:
        config = load_config()

    # Check web app status
    is_running, base_url = check_webapp(config)
    if not is_running:
        return False, f"Web app not running: {base_url}", None

    # Generate filename if not provided
    if not filename:
        from datetime import datetime
        filename = datetime.now().strftime('%H%M%S')

    # Prepare form data
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

    # Build multipart form data
    data_parts = []

    # Request body field
    data_parts.append(f'--{boundary}\r\n')
    data_parts.append('Content-Disposition: form-data; name="request_body"\r\n\r\n')
    data_parts.append(request_body + '\r\n')

    # Response body field
    data_parts.append(f'--{boundary}\r\n')
    data_parts.append('Content-Disposition: form-data; name="response_body"\r\n\r\n')
    data_parts.append(response_body + '\r\n')

    # Filename field
    data_parts.append(f'--{boundary}\r\n')
    data_parts.append('Content-Disposition: form-data; name="file_name"\r\n\r\n')
    data_parts.append(filename + '\r\n')

    data_parts.append(f'--{boundary}--\r\n')

    body = ''.join(data_parts)

    try:
        # Send request
        req = urllib.request.Request(
            f"{base_url}/generate_pcap",
            data=body.encode('utf-8'),
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            # Follow redirect to download
            final_url = response.url
            output_dir = config.get('output', 'default_dir')
            filepath = os.path.join(output_dir, f"{filename}.pcap")

            with open(filepath, 'wb') as f:
                f.write(response.read())

            return True, f"PCAP saved to {filepath}", filepath

    except Exception as e:
        return False, f"Error: {str(e)}", None

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_pcap.py <request_file> <response_file> [filename]")
        print("  Or use stdin for request/response:")
        print("  cat request.txt | python generate_pcap.py - response.txt")
        sys.exit(1)

    request_file = sys.argv[1]
    response_file = sys.argv[2]
    filename = sys.argv[3] if len(sys.argv) > 3 else None

    config = load_config()

    # Read request body
    if request_file == '-':
        request_body = sys.stdin.read()
    else:
        with open(request_file, 'r') as f:
            request_body = f.read()

    # Read response body
    if response_file == '-':
        response_body = sys.stdin.read()
    else:
        with open(response_file, 'r') as f:
            response_body = f.read()

    success, message, filepath = generate_pcap(request_body, response_body, filename, config)

    print(message)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()