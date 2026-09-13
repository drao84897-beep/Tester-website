import re
import urllib.parse

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
# Phone regex matching international & US/UK formats
PHONE_REGEX = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"

SOCIAL_PLATFORMS = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "linkedin.com": "LinkedIn",
    "twitter.com": "X (Twitter)",
    "x.com": "X (Twitter)",
    "youtube.com": "YouTube",
    "tiktok.com": "TikTok",
    "github.com": "GitHub",
}

ADDRESS_PATTERNS = [
    r"\b\d{1,5}\s+[A-Za-z0-9\s.,]{3,35}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Suite|Ste|Floor|Fl|Building|Bldg|Way|Lane|Ln)\b",
    r"\b(?:P\.?O\.?\s*Box\s+\d+)\b",
    r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b",  # UK Postcode
    r"\b\d{5}(?:-\d{4})?\b",  # US Zip Code pattern near address keywords
]


def extract_contacts_and_identity(homepage_data, crawled_pages=None, base_hostname=""):
    """
    Extracts emails, phone numbers, address indicators, business identity, and social links.
    """
    full_text = homepage_data.get("full_text", "")
    external_links = homepage_data.get("external_links", [])
    title = homepage_data.get("title", "")
    og_site_name = homepage_data.get("og_site_name", "")

    # Combine text from crawled pages
    if crawled_pages:
        for p_url, p_data in crawled_pages.items():
            full_text += " " + p_data.get("full_text", "")

    # 1. Emails
    raw_emails = re.findall(EMAIL_REGEX, full_text)
    # Filter out common file extensions erroneously caught by email regex
    invalid_endings = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".js", ".css")
    valid_emails = set()
    is_placeholder_email = False

    for em in raw_emails:
        em_lower = em.lower()
        if any(em_lower.endswith(ext) for ext in invalid_endings):
            continue
        valid_emails.add(em)
        if any(ph in em_lower for ph in ["user@example.com", "email@example.com", "name@example.com", "info@yourcompany.com", "test@test.com"]):
            is_placeholder_email = True

    # 2. Phones
    raw_phones = re.findall(PHONE_REGEX, full_text)
    valid_phones = set()
    is_placeholder_phone = False
    for ph in raw_phones:
        cleaned = re.sub(r"[^\d+]", "", ph)
        if 8 <= len(cleaned) <= 15:
            # Check for dummy phone like 123456789 or 5555555555
            if cleaned in ("1234567890", "0123456789", "5555555555", "1111111111", "0000000000"):
                is_placeholder_phone = True
            else:
                valid_phones.add(ph.strip())

    # 3. Physical Address
    address_detected = False
    address_sample = None
    address_keywords = ["suite", "floor", "headquarters", "street", "avenue", "road", "building", "postal code", "zip code"]
    if any(ak in full_text.lower() for ak in address_keywords):
        for pattern in ADDRESS_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                address_detected = True
                address_sample = match.group(0).strip()[:80]
                break

    # 4. Social Media Links
    detected_socials = {}
    for link in external_links:
        parsed = urllib.parse.urlparse(link)
        netloc = parsed.netloc.lower()
        for platform_domain, platform_name in SOCIAL_PLATFORMS.items():
            if platform_domain in netloc:
                # Avoid generic share links (e.g. facebook.com/sharer)
                if not any(sh in link.lower() for sh in ["sharer", "share?", "intent/tweet", "intent/post"]):
                    if platform_name not in detected_socials:
                        detected_socials[platform_name] = link

    # 5. Business Name Detection
    business_name = og_site_name
    if not business_name and title:
        # If title is "Example Inc - Official Website", split by separator
        separators = ["|", "—", "-", "•", ":"]
        for sep in separators:
            if sep in title:
                candidate = title.split(sep)[0].strip()
                if len(candidate) > 2 and len(candidate) < 40:
                    business_name = candidate
                    break
        if not business_name:
            business_name = title[:45]

    if not business_name:
        # Fallback to capitalized base hostname
        base_clean = base_hostname.replace("www.", "").split(".")[0]
        business_name = base_clean.capitalize()

    # Detect placeholder company name
    is_placeholder_company = False
    if re.search(r"your company name|company name here|insert title", business_name, re.IGNORECASE):
        is_placeholder_company = True

    return {
        "business_name": business_name,
        "is_placeholder_company": is_placeholder_company,
        "emails": list(valid_emails)[:5],
        "phones": list(valid_phones)[:3],
        "has_email": len(valid_emails) > 0,
        "has_phone": len(valid_phones) > 0,
        "has_address": address_detected,
        "address_sample": address_sample,
        "is_placeholder_email": is_placeholder_email,
        "is_placeholder_phone": is_placeholder_phone,
        "social_presence_count": len(detected_socials),
        "social_links": detected_socials,
    }
