import datetime
import requests
import socket
from config import Config

# Free public RDAP endpoints (Zero API keys required)
RDAP_BASE_URL = "https://rdap.org/domain/"


def calculate_domain_age(creation_date_str):
    """
    Parses creation date and calculates formatted age in years, months, and days.
    """
    if not creation_date_str:
        return None, "Not available"

    try:
        # Handles ISO 8601 timestamps like 1995-08-14T04:00:00Z
        dt = datetime.datetime.fromisoformat(creation_date_str.replace("Z", "+00:00"))
        # Remove tzinfo for simple date arithmetic
        created_at = dt.replace(tzinfo=None)
        now = datetime.datetime.utcnow()

        delta_days = (now - created_at).days
        if delta_days < 0:
            return 0, "Registered today"

        years = delta_days // 365
        remaining_days = delta_days % 365
        months = remaining_days // 30
        days = remaining_days % 30

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months != 1 else ''}")
        if not parts or days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")

        age_str = " / ".join(parts)
        return delta_days, age_str
    except Exception:
        return None, "Not available"


def get_dns_records(domain):
    """
    Retrieves DNS information (A records, Nameservers) using standard socket or dnspython.
    """
    records = {"a_records": [], "nameservers": [], "mx_records": []}
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3.0
        resolver.lifetime = 3.0

        try:
            answers = resolver.resolve(domain, "A")
            records["a_records"] = [str(r) for r in answers]
        except Exception:
            pass

        try:
            answers = resolver.resolve(domain, "NS")
            records["nameservers"] = [str(r).rstrip(".") for r in answers]
        except Exception:
            pass

        try:
            answers = resolver.resolve(domain, "MX")
            records["mx_records"] = [str(r.exchange).rstrip(".") for r in answers]
        except Exception:
            pass
    except Exception:
        # Fallback to standard socket
        try:
            addrs = socket.getaddrinfo(domain, None)
            records["a_records"] = list({x[4][0] for x in addrs})
        except Exception:
            pass

    return records


def analyze_domain(hostname):
    """
    Performs domain information retrieval via free public RDAP and DNS analysis.
    Gracefully handles platforms (Vercel, Netlify, GitHub Pages) and ccTLDs.
    """
    # Extract base registrable domain if possible
    domain_parts = hostname.split(".")
    base_domain = hostname

    known_free_platforms = {
        "vercel.app": "Vercel Cloud Platform",
        "netlify.app": "Netlify Cloud Platform",
        "github.io": "GitHub Pages",
        "gitlab.io": "GitLab Pages",
        "pages.dev": "Cloudflare Pages",
        "onrender.com": "Render Cloud Platform",
        "web.app": "Google Firebase Hosting",
        "firebaseapp.com": "Google Firebase Hosting",
        "herokuapp.com": "Heroku Cloud",
        "amplifyapp.com": "AWS Amplify",
    }

    is_subdomain_platform = False
    platform_name = None
    for plat_domain, plat_desc in known_free_platforms.items():
        if hostname.endswith("." + plat_domain):
            is_subdomain_platform = True
            platform_name = plat_desc
            base_domain = plat_domain
            break

    if len(domain_parts) > 2 and not is_subdomain_platform:
        # Attempt to use primary domain for RDAP query (e.g., sub.example.com -> example.com)
        if domain_parts[-2] in ("co", "com", "org", "net", "edu", "gov") and len(domain_parts) >= 3:
            base_domain = ".".join(domain_parts[-3:])
        else:
            base_domain = ".".join(domain_parts[-2:])

    dns_info = get_dns_records(hostname)

    domain_data = {
        "domain": hostname,
        "base_domain": base_domain,
        "is_platform_subdomain": is_subdomain_platform,
        "platform_name": platform_name,
        "registrar": "Not available — external verification required",
        "creation_date": None,
        "updated_date": None,
        "expiration_date": None,
        "age_days": None,
        "age_formatted": "Not available",
        "nameservers": dns_info["nameservers"],
        "a_records": dns_info["a_records"],
        "mx_records": dns_info["mx_records"],
        "status": [],
        "note": "Standard domain",
        "new_domain_flag": False,
    }

    if is_subdomain_platform:
        domain_data["note"] = f"Hosted on shared developer subdomain ({platform_name}). Individual app age cannot be determined by domain RDAP."
        return domain_data

    # Query public RDAP
    try:
        resp = requests.get(
            f"{RDAP_BASE_URL}{base_domain}",
            headers={"Accept": "application/rdap+json, application/json", "User-Agent": Config.USER_AGENT},
            timeout=5,
        )
        if resp.status_code == 200:
            rdap = resp.json()

            # Parse Events (creation, expiration, last changed)
            events = rdap.get("events", [])
            for ev in events:
                action = ev.get("eventAction", "").lower()
                date_val = ev.get("eventDate")
                if "registration" in action or "created" in action:
                    domain_data["creation_date"] = date_val
                elif "expiration" in action:
                    domain_data["expiration_date"] = date_val
                elif "last changed" in action or "updated" in action:
                    domain_data["updated_date"] = date_val

            # Parse Registrar
            entities = rdap.get("entities", [])
            for ent in entities:
                roles = ent.get("roles", [])
                if "registrar" in roles:
                    # Look inside vcardArray
                    vcard = ent.get("vcardArray", [])
                    if len(vcard) > 1:
                        for entry in vcard[1]:
                            if entry[0] == "fn":
                                domain_data["registrar"] = entry[3]
                                break
                    if domain_data["registrar"].startswith("Not available"):
                        handle = ent.get("handle")
                        if handle:
                            domain_data["registrar"] = handle

            # Nameservers from RDAP if not found via DNS
            if not domain_data["nameservers"]:
                ns_list = rdap.get("nameservers", [])
                domain_data["nameservers"] = [ns.get("ldhName") for ns in ns_list if ns.get("ldhName")]

            # Statuses
            domain_data["status"] = rdap.get("status", [])

    except Exception:
        # RDAP failed or timeout; domain_data maintains honest "Not available" flags
        pass

    # Calculate domain age
    if domain_data["creation_date"]:
        days, formatted = calculate_domain_age(domain_data["creation_date"])
        domain_data["age_days"] = days
        domain_data["age_formatted"] = formatted

        if days is not None and days < 180:
            domain_data["new_domain_flag"] = True
            domain_data["note"] = "New domain (< 6 months) — requires additional verification"
        elif days is not None and days >= 365:
            domain_data["note"] = "Established domain history (> 1 year)"

    return domain_data
