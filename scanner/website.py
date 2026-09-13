import re
import socket
import ipaddress
import urllib.parse
import requests
from bs4 import BeautifulSoup
from config import Config


def is_safe_ip(ip_str):
    """
    Validates that an IP address is a public, routable internet address.
    Strictly blocks loopback, private RFC1918, link-local, multicast, and cloud metadata.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False

        # Explicitly guard against AWS / GCP / Azure metadata endpoint (169.254.169.254)
        if ip_str == "169.254.169.254":
            return False

        # Guard against IPv4-mapped IPv6 loopback/private
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return is_safe_ip(str(ip.ipv4_mapped))

        return True
    except ValueError:
        return False


def validate_and_normalize_url(raw_url):
    """
    Validates and normalizes user-provided URL.
    Enforces HTTP/HTTPS only and verifies DNS against SSRF threats.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("Please provide a valid website URL.")

    raw_url = raw_url.strip()
    if not raw_url.startswith(("http://", "https://")):
        # Default to https://
        raw_url = "https://" + raw_url

    parsed = urllib.parse.urlparse(raw_url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS protocols are supported.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: Missing domain or hostname.")

    hostname = hostname.lower().strip(".")
    if hostname in Config.BLOCKED_HOSTS:
        raise ValueError(f"Access to '{hostname}' is restricted for security reasons (SSRF Protection).")

    # Check for direct numeric IP representation
    try:
        ip = ipaddress.ip_address(hostname)
        if not is_safe_ip(str(ip)):
            raise ValueError("Direct access to private, local, or internal IP addresses is forbidden.")
    except ValueError:
        # Not a raw IP literal, resolve hostname via DNS
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            resolved_ips = {item[4][0] for item in addr_info}
            if not resolved_ips:
                raise ValueError(f"Could not resolve host '{hostname}'. Website may be offline or nonexistent.")

            for ip_candidate in resolved_ips:
                if not is_safe_ip(ip_candidate):
                    raise ValueError(f"Host '{hostname}' resolves to an internal/private address. Access denied.")
        except socket.gaierror:
            raise ValueError(f"Domain '{hostname}' could not be resolved. Please verify the domain name.")

    # Return normalized canonical URL
    normalized_path = parsed.path if parsed.path else "/"
    normalized = urllib.parse.urlunparse(
        (scheme, parsed.netloc, normalized_path, parsed.params, parsed.query, "")
    )
    return normalized, hostname


def safe_fetch(url, timeout=None, max_bytes=None, max_redirects=5):
    """
    Performs safe HTTP GET with SSRF protection on every redirect hop,
    response size limits, and configurable timeout.
    """
    if timeout is None:
        timeout = Config.SCAN_TIMEOUT
    if max_bytes is None:
        max_bytes = Config.MAX_RESPONSE_SIZE

    current_url = url
    redirect_count = 0
    redirect_history = []
    final_response = None

    headers = {
        "User-Agent": Config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    }

    session = requests.Session()

    while redirect_count <= max_redirects:
        # Validate URL at each step (including redirects)
        validate_and_normalize_url(current_url)

        try:
            resp = session.get(
                current_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                verify=True,
            )
        except requests.exceptions.SSLError:
            # Fallback for SSL issues to inspect content while flagging SSL error
            resp = session.get(
                current_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                verify=False,
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to '{current_url}' timed out after {timeout} seconds.")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Unable to connect to '{current_url}': {str(e)}")

        redirect_history.append((current_url, resp.status_code))

        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            redirect_count += 1
            location = resp.headers.get("Location")
            if not location:
                final_response = resp
                break
            current_url = urllib.parse.urljoin(current_url, location)
            resp.close()
            continue
        else:
            final_response = resp
            break

    if redirect_count > max_redirects:
        raise ValueError("Too many redirects detected. Possible redirect loop.")

    # Read up to max_bytes safely
    content_chunks = []
    total_bytes = 0
    for chunk in final_response.iter_content(chunk_size=8192):
        total_bytes += len(chunk)
        content_chunks.append(chunk)
        if total_bytes > max_bytes:
            break
    final_response.close()

    raw_bytes = b"".join(content_chunks)
    encoding = final_response.encoding or "utf-8"
    try:
        html_text = raw_bytes.decode(encoding, errors="replace")
    except Exception:
        html_text = raw_bytes.decode("utf-8", errors="replace")

    return {
        "final_url": current_url,
        "status_code": final_response.status_code,
        "headers": dict(final_response.headers),
        "html": html_text,
        "redirect_history": redirect_history,
        "size_bytes": total_bytes,
    }


def parse_page_content(html, base_url):
    """
    Parses HTML content and extracts structured metadata, navigation, forms, headings,
    paragraphs, images, and internal links.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements for clean text analysis
    for s in soup(["script", "style", "noscript"]):
        s.extract()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
               soup.find("meta", attrs={"property": "og:description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    og_site_name = ""
    og_tag = soup.find("meta", attrs={"property": "og:site_name"})
    if og_tag and og_tag.get("content"):
        og_site_name = og_tag["content"].strip()

    headings = {
        "h1": [h.get_text().strip() for h in soup.find_all("h1") if h.get_text().strip()],
        "h2": [h.get_text().strip() for h in soup.find_all("h2") if h.get_text().strip()],
        "h3": [h.get_text().strip() for h in soup.find_all("h3") if h.get_text().strip()],
    }

    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    full_text = soup.get_text(separator=" ", strip=True)

    # Extract internal and external links
    base_domain = urllib.parse.urlparse(base_url).netloc.lower()
    internal_links = set()
    external_links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_href = urllib.parse.urljoin(base_url, href)
        parsed_link = urllib.parse.urlparse(full_href)
        link_domain = parsed_link.netloc.lower()

        if link_domain == base_domain:
            # Strip fragment
            clean_link = urllib.parse.urlunparse(
                (parsed_link.scheme, parsed_link.netloc, parsed_link.path, "", parsed_link.query, "")
            )
            internal_links.add(clean_link)
        else:
            external_links.add(full_href)

    # Extract forms
    forms = []
    for form in soup.find_all("form"):
        form_action = form.get("action", "")
        inputs = [inp.get("name") or inp.get("type", "input") for inp in form.find_all(["input", "textarea", "button"])]
        forms.append({"action": form_action, "inputs": inputs})

    # Images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        images.append({"src": src, "alt": alt})

    # Navigation items
    nav_items = []
    nav = soup.find("nav") or soup.find(class_=re.compile(r"nav|menu|header", re.I))
    if nav:
        for a in nav.find_all("a"):
            txt = a.get_text().strip()
            if txt:
                nav_items.append(txt)

    return {
        "title": title,
        "meta_description": meta_desc,
        "og_site_name": og_site_name,
        "headings": headings,
        "paragraphs": paragraphs,
        "full_text": full_text,
        "word_count": len(full_text.split()),
        "internal_links": list(internal_links),
        "external_links": list(external_links),
        "forms": forms,
        "images": images,
        "nav_items": nav_items[:15],
    }


def crawl_key_pages(base_url, internal_links, max_pages=None):
    """
    Performs shallow crawl on critical business authenticity pages
    (e.g., about, contact, privacy, terms, services, faq).
    """
    if max_pages is None:
        max_pages = Config.MAX_CRAWL_PAGES

    priority_keywords = ["about", "contact", "privacy", "terms", "faq", "service", "pricing"]
    priority_urls = []
    remaining_urls = []

    for link in internal_links:
        if link == base_url:
            continue
        path = urllib.parse.urlparse(link).path.lower()
        if any(kw in path for kw in priority_keywords):
            if link not in priority_urls:
                priority_urls.append(link)
        elif link not in remaining_urls:
            remaining_urls.append(link)

    # Scan authenticity-critical routes first, then use remaining crawl budget
    # for other internal pages so the content verdict is not based on the homepage alone.
    candidate_urls = priority_urls + remaining_urls

    crawled_pages = {}
    for url in candidate_urls[:max_pages]:
        try:
            fetched = safe_fetch(url, timeout=4)
            if fetched["status_code"] == 200:
                parsed = parse_page_content(fetched["html"], url)
                crawled_pages[url] = {
                    "title": parsed["title"],
                    "word_count": parsed["word_count"],
                    "headings": parsed["headings"],
                    "forms": parsed["forms"],
                    "full_text": parsed["full_text"][:5000],  # truncated for safety
                }
        except Exception:
            continue

    return crawled_pages
