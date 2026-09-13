import ssl
import socket
import datetime
import requests
from config import Config
from .website import is_safe_ip


def check_ssl_and_https(hostname, port=443, timeout=5):
    """
    Analyzes SSL/TLS certificate details and HTTPS redirect behavior.
    """
    security_report = {
        "https_enabled": False,
        "ssl_valid": False,
        "http_to_https_redirect": False,
        "issuer": "Not Available",
        "subject": "Not Available",
        "valid_from": None,
        "valid_to": None,
        "days_remaining": None,
        "san_domains": [],
        "warnings": [],
        "status_summary": {
            "https": "FAIL",
            "ssl": "FAIL",
            "redirect": "FAIL",
        },
    }

    # 1. Test direct SSL connection
    try:
        # Resolve IP to verify safety first
        addr_info = socket.getaddrinfo(hostname, port)
        if not addr_info:
            security_report["warnings"].append("Failed to resolve hostname for SSL check.")
            return security_report

        ip_addr = addr_info[0][4][0]
        if not is_safe_ip(ip_addr):
            security_report["warnings"].append("Host resolves to internal network; SSL connection aborted.")
            return security_report

        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                security_report["https_enabled"] = True
                security_report["ssl_valid"] = True
                security_report["status_summary"]["https"] = "PASS"
                security_report["status_summary"]["ssl"] = "PASS"

                # Extract Issuer
                issuer_dict = dict(x[0] for x in cert.get("issuer", ()))
                issuer_name = issuer_dict.get("organizationName") or issuer_dict.get("commonName") or "Unknown Authority"
                security_report["issuer"] = issuer_name

                # Extract Subject
                subject_dict = dict(x[0] for x in cert.get("subject", ()))
                security_report["subject"] = subject_dict.get("commonName", hostname)

                # Extract Validity Dates
                not_before_str = cert.get("notBefore")
                not_after_str = cert.get("notAfter")

                if not_before_str and not_after_str:
                    date_fmt = r"%b %d %H:%M:%S %Y %Z"
                    not_before = datetime.datetime.strptime(not_before_str, date_fmt)
                    not_after = datetime.datetime.strptime(not_after_str, date_fmt)

                    security_report["valid_from"] = not_before.strftime("%Y-%m-%d")
                    security_report["valid_to"] = not_after.strftime("%Y-%m-%d")

                    now = datetime.datetime.utcnow()
                    days_remaining = (not_after - now).days
                    security_report["days_remaining"] = days_remaining

                    if days_remaining < 0:
                        security_report["ssl_valid"] = False
                        security_report["status_summary"]["ssl"] = "EXPIRED"
                        security_report["warnings"].append("SSL certificate has expired.")
                    elif days_remaining < 15:
                        security_report["warnings"].append(f"SSL certificate expires soon ({days_remaining} days).")

                # Extract SAN
                san = [item[1] for item in cert.get("subjectAltName", ()) if item[0] == "DNS"]
                security_report["san_domains"] = san[:10]

    except ssl.SSLCertVerificationError as e:
        security_report["warnings"].append(f"SSL certificate validation error: {e.verify_message}")
        security_report["status_summary"]["ssl"] = "UNTRUSTED"
    except socket.timeout:
        security_report["warnings"].append("SSL handshake connection timed out.")
    except Exception as e:
        security_report["warnings"].append(f"SSL connection error: {str(e)}")

    # 2. Check HTTP -> HTTPS redirect
    try:
        http_url = f"http://{hostname}/"
        headers = {"User-Agent": Config.USER_AGENT}
        r = requests.get(http_url, headers=headers, timeout=4, allow_redirects=False)
        if r.status_code in (301, 302, 307, 308):
            loc = r.headers.get("Location", "")
            if loc.lower().startswith("https://"):
                security_report["http_to_https_redirect"] = True
                security_report["status_summary"]["redirect"] = "PASS"
    except Exception:
        pass

    return security_report
