import ipaddress
import socket
from urllib.parse import urlsplit


def validate_public_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        hostname = parsed.hostname

        if hostname.lower() == "localhost":
            return False

        port = parsed.port

        if port not in (None, 80, 443):
            return False

        addresses = socket.getaddrinfo(
            hostname,
            port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM
        )

        if not addresses:
            return False

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                return False

        return True

    except (ValueError, OSError):
        return False