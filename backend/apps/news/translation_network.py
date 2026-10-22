"""Narrow loopback-only HTTP transport for an explicitly configured local translator.

Does not relax the news/utility HTTPS public-address client. No proxies, redirects,
DNS lookup or arbitrary user-controlled destination. No provider response is logged.
"""
import ipaddress
import json
from http.client import HTTPConnection
from urllib.parse import urlsplit


def fetch_local_json(base, path, data=None, timeout=15, max_bytes=1_000_000):
    parts = urlsplit(base)
    if parts.scheme != 'http' or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('Local translation endpoint requires a plain loopback HTTP URL without credentials or query parameters.')
    host = parts.hostname
    if host == 'localhost':
        host = '127.0.0.1'  # Do not trust mutable DNS for the privileged local exception.
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError('Not loopback')
    except (ValueError, TypeError):
        raise ValueError('HTTP translation is allowed only on literal loopback addresses or localhost.') from None
    if path not in ('/languages', '/translate'):
        raise ValueError('Unsupported translation operation.')
    port = parts.port or 80
    if not 1 <= port <= 65535:
        raise ValueError('Invalid local translation port.')
    connection = HTTPConnection(host, port, timeout=timeout)
    body = None if data is None else json.dumps(data).encode('utf-8')
    headers = {'Accept':'application/json'}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    try:
        connection.request('GET' if body is None else 'POST', parts.path.rstrip('/') + path, body, headers)
        response = connection.getresponse()
        # Never follow a redirect from the privileged endpoint, even to another loopback host.
        if response.status != 200:
            raise ValueError('Local translation service returned a non-success status; check its health and access configuration.')
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError('Translation response exceeds the configured safety limit.')
        return json.loads(raw)
    finally:
        connection.close()
