"""
Web fetch service for candidate portfolio URL.
Includes strict SSRF protection against private, loopback, link-local, and cloud metadata IPs,
including verification before request and following redirects.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
import trafilatura

TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 1 * 1024 * 1024  # 1 MB


class SSRFSecurityError(Exception):
    pass


def is_ip_disallowed(ip_str: str) -> bool:
    """Check if an IP address falls into loopback, private, link-local, or cloud metadata."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback:
            return True
        if ip.is_private:
            return True
        if ip.is_link_local:
            return True
        if ip.is_reserved:
            return True
        if ip.is_multicast:
            return True
        # Explicit check for AWS/GCP/Azure link-local metadata IP
        if ip_str == "169.254.169.254":
            return True
        return False
    except ValueError:
        return True


def validate_url_safety(url: str):
    """Ensure URL is http/https and does not resolve to an unsafe IP address."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ["http", "https"]:
        raise SSRFSecurityError(f"Disallowed scheme: {parsed.scheme}. Only HTTP/HTTPS permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("URL missing hostname.")

    # Avoid localhost / local patterns
    if hostname.lower() in ["localhost", "127.0.0.1", "::1", "metadata.google.internal"]:
        raise SSRFSecurityError("Localhost or metadata domain disallowed.")

    try:
        # Resolve all IPs
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip = entry[4][0]
            if is_ip_disallowed(ip):
                raise SSRFSecurityError(f"Host {hostname} resolved to disallowed IP {ip}.")
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Failed to resolve hostname {hostname}: {e}")


def fetch_portfolio_text(url: str) -> str:
    """
    Fetch a single candidate portfolio web page safely with SSRF protection.
    Follows redirects while validating each target URL's IP.
    """
    validate_url_safety(url)

    current_url = url
    max_redirects = 3

    for _ in range(max_redirects + 1):
        with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
            response = client.get(current_url)

            if response.is_redirect:
                redirect_url = response.headers.get("location")
                if not redirect_url:
                    break
                # Handle relative redirects
                parsed = urlparse(redirect_url)
                if not parsed.netloc:
                    base = urlparse(current_url)
                    redirect_url = f"{base.scheme}://{base.netloc}/{redirect_url.lstrip('/')}"
                validate_url_safety(redirect_url)
                current_url = redirect_url
                continue

            response.raise_for_status()
            content = response.content
            if len(content) > MAX_RESPONSE_BYTES:
                content = content[:MAX_RESPONSE_BYTES]

            html_text = content.decode("utf-8", errors="replace")
            extracted = trafilatura.extract(html_text)
            if not extracted:
                # Basic fallback if trafilatura extracts nothing
                extracted = trafilatura.html2txt(html_text)
            return extracted or ""

    return ""
