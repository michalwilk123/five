import json
import os
import socket
import urllib.request


def is_proxy_healthy(port):
    url = 'https://api.anthropic.com/custom-proxy-health-check'
    proxy_url = f'http://127.0.0.1:{port}'
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(url, timeout=2) as response:
            data = json.loads(response.read().decode())
            return bool(
                data.get('status') == 'running' and 'claude-mitm-proxy' in data.get('proxy', '')
            )
    except Exception:
        return False


def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


def find_free_port(start_port, max_attempts):
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
            return port
        except OSError:
            continue
    return None


def find_running_proxy(start_port, scan_count):
    for port in range(start_port, start_port + scan_count):
        if is_port_open(port) and is_proxy_healthy(port):
            return port
    return None


def proxy_env_vars(port):
    proxy_url = f'http://127.0.0.1:{port}'
    cert_path = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.pem')
    return {
        'HTTP_PROXY': proxy_url,
        'HTTPS_PROXY': proxy_url,
        'http_proxy': proxy_url,
        'https_proxy': proxy_url,
        'CURL_CA_BUNDLE': cert_path,
        'REQUESTS_CA_BUNDLE': cert_path,
        'SSL_CERT_FILE': cert_path,
        'NODE_EXTRA_CA_CERTS': cert_path,
    }
