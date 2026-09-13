import re


DUMMY_PATTERNS = [
    # Lorem Ipsum
    (r"\blorem\s+ipsum\b", "Lorem Ipsum placeholder text"),
    (r"\bdolor\s+sit\s+amet\b", "Standard Latin placeholder phrase"),
    (r"\bconsectetur\s+adipiscing\b", "Standard Latin template text"),

    # Generic Business Placeholders
    (r"\[your\s+company(?:\s+name)?\]", "Template placeholder: [Your Company Name]"),
    (r"\[company\s+name\]", "Template placeholder: [Company Name]"),
    (r"\byour\s+company\s+name\b", "Unedited placeholder: 'Your Company Name'"),
    (r"\bcompany\s+name\s+here\b", "Unedited placeholder: 'Company Name Here'"),
    (r"\binsert\s+(?:title|text|name|description)\s+here\b", "Unedited template prompt ('Insert text here')"),
    (r"\badd\s+(?:your\s+)?description\s+here\b", "Unfinished description prompt"),

    # Fictional Persona Names
    (r"\bjohn\s+doe\b", "Fictional persona placeholder: 'John Doe'"),
    (r"\bjane\s+doe\b", "Fictional persona placeholder: 'Jane Doe'"),

    # Default Template / Demo Wording
    (r"\bwebsite\s+under\s+construction\b", "Under construction notice"),
    (r"\bcoming\s+soon\b", "Coming soon placeholder notice"),
    (r"\bdemo\s+version\b", "Explicit 'Demo Version' notice"),
    (r"\bsample\s+website\b", "Template sample label"),
    (r"\bthis\s+is\s+a\s+demo\b", "Explicit demo statement"),
    (r"\bplaceholder\s+text\b", "Explicit placeholder wording"),
]

PLACEHOLDER_EMAILS = [
    "user@example.com",
    "email@example.com",
    "name@example.com",
    "contact@example.com",
    "info@yourcompany.com",
    "john.doe@example.com",
    "support@domain.com",
    "test@test.com",
]

PLACEHOLDER_PHONES = [
    "123-456-7890",
    "(123) 456-7890",
    "+1 123 456 7890",
    "555-555-5555",
    "(555) 555-5555",
    "1234567890",
    "0123456789",
]

BUSINESS_KEYWORDS = [
    "services", "products", "solutions", "clients", "portfolio", "about us",
    "contact us", "privacy policy", "terms of service", "careers", "pricing",
    "features", "customer", "mission", "leadership", "overview", "consulting",
    "support", "industry", "guarantee", "compliance"
]


def analyze_content_quality(homepage_data, crawled_pages=None):
    """
    Evaluates text richness, heading hierarchy, placeholder/dummy phrases,
    and business terminology.
    """
    full_text = homepage_data.get("full_text", "")
    headings = homepage_data.get("headings", {})
    images = homepage_data.get("images", [])
    nav_items = homepage_data.get("nav_items", [])

    # Include crawled pages text if available
    if crawled_pages:
        for page_url, pdata in crawled_pages.items():
            full_text += " " + pdata.get("full_text", "")

    full_text_lower = full_text.lower()
    word_count = len(full_text.split())

    # 1. Detect Dummy / Placeholder Signals
    dummy_signals = []
    for pattern, label in DUMMY_PATTERNS:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            dummy_signals.append({
                "type": "text_placeholder",
                "label": label,
                "occurrences": len(matches),
            })

    # Check placeholder images
    placeholder_img_count = 0
    for img in images:
        src = img.get("src", "").lower()
        if any(ph in src for ph in ["via.placeholder.com", "dummyimage.com", "placekitten.com", "placeholder.com"]):
            placeholder_img_count += 1
    if placeholder_img_count > 0:
        dummy_signals.append({
            "type": "image_placeholder",
            "label": f"Found {placeholder_img_count} generic placeholder image(s) (e.g., via.placeholder.com)",
            "occurrences": placeholder_img_count,
        })

    # 2. Analyze Heading Hierarchy
    h1_list = headings.get("h1", [])
    h2_list = headings.get("h2", [])
    has_h1 = len(h1_list) > 0
    heading_structure_score = 0
    if has_h1:
        heading_structure_score += 5
    if len(h2_list) >= 2:
        heading_structure_score += 5

    # 3. Analyze Business Terminology
    found_business_keywords = []
    for kw in BUSINESS_KEYWORDS:
        if kw in full_text_lower:
            found_business_keywords.append(kw)

    # 4. Navigation Completeness
    nav_completeness = "Good"
    if len(nav_items) == 0:
        nav_completeness = "Missing navigation menu"
    elif len(nav_items) < 3:
        nav_completeness = "Minimal navigation links"

    # 5. Content Quality Level
    dummy_severity = "LOW"
    if len(dummy_signals) >= 3 or any(d["occurrences"] > 3 for d in dummy_signals):
        dummy_severity = "HIGH"
    elif len(dummy_signals) >= 1:
        dummy_severity = "MEDIUM"

    content_rating = "High"
    if word_count < 100 or dummy_severity == "HIGH":
        content_rating = "Low"
    elif word_count < 300 or dummy_severity == "MEDIUM":
        content_rating = "Moderate"

    # Careful notes
    observations = []
    if dummy_severity == "HIGH":
        observations.append("Potential demo/template indicators detected: website contains substantial placeholder or Latin dummy text.")
    elif dummy_severity == "MEDIUM":
        observations.append("Potential demo/template indicators detected: isolated placeholder phrases found.")

    if word_count < 150:
        observations.append("Low text content volume across indexed pages.")
    else:
        observations.append(f"Substantive content volume ({word_count} total words analyzed).")

    if len(found_business_keywords) >= 5:
        observations.append("Strong business and professional terminology detected.")

    return {
        "word_count": word_count,
        "content_rating": content_rating,
        "dummy_severity": dummy_severity,
        "dummy_signals": dummy_signals,
        "has_h1": has_h1,
        "h1_samples": h1_list[:2],
        "h2_count": len(h2_list),
        "business_keywords_found": found_business_keywords,
        "nav_completeness": nav_completeness,
        "observations": observations,
    }
