import urllib.parse
import requests
from config import Config
from .website import validate_and_normalize_url


SENSITIVE_KEYWORDS = [
    "admin", "login", "signin", "logout", "signout", "register",
    "password", "reset", "cart", "checkout", "auth", "oauth", "api/",
    "wp-admin", "user/login", "dashboard", "billing"
]


def check_sample_links(base_url, internal_links, max_links=6):
    """
    Safely verifies a sample of internal links, filtering out private/sensitive paths
    and applying SSRF checks.
    """
    safe_candidates = []
    base_domain = urllib.parse.urlparse(base_url).netloc.lower()

    for link in internal_links:
        parsed = urllib.parse.urlparse(link)
        if parsed.netloc.lower() != base_domain:
            continue

        path_lower = parsed.path.lower()
        # Skip sensitive/private endpoints
        if any(sk in path_lower for sk in SENSITIVE_KEYWORDS):
            continue

        # Skip anchor links or static assets
        if path_lower.endswith((".pdf", ".zip", ".tar", ".gz", ".exe", ".png", ".jpg", ".svg", ".css", ".js")):
            continue

        if link != base_url and link not in safe_candidates:
            safe_candidates.append(link)

    sampled = safe_candidates[:max_links]
    results = []
    broken_count = 0
    working_count = 0
    redirect_count = 0

    headers = {"User-Agent": Config.USER_AGENT}

    for target_url in sampled:
        try:
            # Enforce SSRF validation
            validate_and_normalize_url(target_url)

            # Fast HEAD request, fallback to GET
            try:
                resp = requests.head(target_url, headers=headers, timeout=3, allow_redirects=False)
                status = resp.status_code
                if status == 405:  # Method Not Allowed for HEAD, try GET
                    resp = requests.get(target_url, headers=headers, timeout=3, allow_redirects=False, stream=True)
                    status = resp.status_code
                    resp.close()
            except requests.RequestException:
                resp = requests.get(target_url, headers=headers, timeout=3, allow_redirects=False, stream=True)
                status = resp.status_code
                resp.close()

            if 200 <= status < 300:
                classification = "Working"
                working_count += 1
            elif 300 <= status < 400:
                classification = "Redirect"
                redirect_count += 1
            else:
                classification = "Broken"
                broken_count += 1

            results.append({
                "url": target_url,
                "status_code": status,
                "classification": classification,
            })
        except Exception:
            results.append({
                "url": target_url,
                "status_code": "Error / Unreachable",
                "classification": "Broken",
            })
            broken_count += 1

    return {
        "links_checked": len(results),
        "working_count": working_count,
        "redirect_count": redirect_count,
        "broken_count": broken_count,
        "details": results,
    }
