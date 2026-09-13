def calculate_authenticity_score(
    security_data,
    domain_data,
    content_data,
    contacts_data,
    tech_data,
    links_data,
    crawled_pages,
    homepage_data
):
    """
    Computes a transparent, explainable authenticity score (0-100) and classification.
    Produces an itemized breakdown of positive weights and negative deductions.
    """
    score = 0
    breakdown = []
    signals = []
    warnings = []

    # 1. HTTPS & Security (up to +15 pts)
    sec_points = 0
    if security_data.get("https_enabled"):
        sec_points += 7
    if security_data.get("ssl_valid"):
        sec_points += 5
    if security_data.get("http_to_https_redirect"):
        sec_points += 3

    if sec_points >= 12:
        signals.append("Modern SSL/TLS encryption active with automatic HTTPS redirection")
    elif sec_points == 0:
        warnings.append("Insecure HTTP connection — no valid SSL certificate detected")
    else:
        warnings.append("Incomplete HTTPS enforcement or certificate notice")

    score += sec_points
    breakdown.append({
        "category": "Security & SSL",
        "points": sec_points,
        "max_points": 15,
        "status": "PASS" if sec_points >= 12 else ("CHECK" if sec_points > 0 else "FAIL"),
        "detail": f"{security_data.get('issuer', 'Standard CA')} · Valid to {security_data.get('valid_to', 'N/A')}"
    })

    # 2. Business Identity (up to +15 pts)
    biz_points = 0
    biz_name = contacts_data.get("business_name", "")
    is_dummy_company = contacts_data.get("is_placeholder_company", False)

    if biz_name and not is_dummy_company:
        biz_points += 10
        signals.append(f"Clear business branding established: '{biz_name}'")
    elif is_dummy_company:
        warnings.append("Generic company placeholder detected ('Your Company Name')")

    if homepage_data.get("title") and len(homepage_data["title"]) >= 5:
        biz_points += 5

    score += biz_points
    breakdown.append({
        "category": "Business Identity",
        "points": biz_points,
        "max_points": 15,
        "status": "PASS" if biz_points >= 12 else "CHECK",
        "detail": f"Branding: {biz_name if biz_name else 'Unspecified'}"
    })

    # 3. Contact Information (up to +15 pts)
    contact_points = 0
    has_email = contacts_data.get("has_email", False)
    has_phone = contacts_data.get("has_phone", False)
    has_addr = contacts_data.get("has_address", False)
    dummy_email = contacts_data.get("is_placeholder_email", False)
    dummy_phone = contacts_data.get("is_placeholder_phone", False)

    if has_email and not dummy_email:
        contact_points += 5
        signals.append("Operational contact email address detected")
    elif dummy_email:
        warnings.append("Placeholder/template email address detected (e.g. user@example.com)")

    if has_phone and not dummy_phone:
        contact_points += 5
        signals.append("Direct telephone contact number provided")
    elif dummy_phone:
        warnings.append("Placeholder phone number detected (e.g. 123-456-7890)")

    if has_addr:
        contact_points += 5
        signals.append("Physical headquarters / address indicators found")
    else:
        warnings.append("No physical business address detected on public pages")

    score += contact_points
    breakdown.append({
        "category": "Contact Information",
        "points": contact_points,
        "max_points": 15,
        "status": "PASS" if contact_points >= 10 else ("CHECK" if contact_points > 0 else "LOW"),
        "detail": f"{len(contacts_data.get('emails', []))} email(s), {len(contacts_data.get('phones', []))} phone(s), address: {'Yes' if has_addr else 'None'}"
    })

    # 4. Domain History & Reputation (up to +15 pts)
    domain_points = 0
    age_days = domain_data.get("age_days")
    is_platform = domain_data.get("is_platform_subdomain", False)

    if age_days is not None:
        if age_days >= 730:  # 2+ years
            domain_points += 15
            signals.append(f"Established domain longevity: {domain_data.get('age_formatted')}")
        elif age_days >= 365:  # 1+ year
            domain_points += 10
            signals.append(f"Mature domain: {domain_data.get('age_formatted')}")
        elif age_days >= 90:  # 3+ months
            domain_points += 5
            warnings.append(f"Moderate domain age: {domain_data.get('age_formatted')}")
        else:
            domain_points += 2
            warnings.append("Recently registered domain (< 3 months) — requires additional verification")
    elif is_platform:
        domain_points += 7  # Neutral allocation for platform subdomains
        signals.append(f"Hosted on modern developer platform: {domain_data.get('platform_name')}")
    else:
        domain_points += 5
        warnings.append("Public domain RDAP creation records restricted or private")

    score += domain_points
    breakdown.append({
        "category": "Domain Longevity",
        "points": domain_points,
        "max_points": 15,
        "status": "PASS" if domain_points >= 10 else "CHECK",
        "detail": f"Age: {domain_data.get('age_formatted', 'N/A')} ({domain_data.get('note', '')})"
    })

    # 5. Content Quality & Services (up to +15 pts)
    content_points = 0
    word_count = content_data.get("word_count", 0)
    biz_kw = content_data.get("business_keywords_found", [])

    if word_count >= 500:
        content_points += 7
        signals.append("Substantive and detailed business content volume")
    elif word_count >= 200:
        content_points += 4
    else:
        warnings.append("Limited text content across indexed pages")

    if len(biz_kw) >= 5:
        content_points += 5
        signals.append("Comprehensive professional service/product descriptions")
    elif len(biz_kw) >= 2:
        content_points += 3

    if content_data.get("has_h1"):
        content_points += 3

    score += content_points
    breakdown.append({
        "category": "Content & Services",
        "points": content_points,
        "max_points": 15,
        "status": "PASS" if content_points >= 10 else "CHECK",
        "detail": f"{word_count} words analyzed, {len(biz_kw)} service keywords"
    })

    # 6. Multi-Page Structure & Legal Pages (up to +15 pts)
    pages_points = 0
    crawled_count = len(crawled_pages)
    internal_links_count = len(homepage_data.get("internal_links", []))

    if internal_links_count >= 5:
        pages_points += 5
        signals.append("Well-connected multi-page website architecture")
    elif internal_links_count >= 2:
        pages_points += 3

    # Check for About page
    has_about = any("about" in url.lower() for url in crawled_pages.keys())
    if has_about:
        pages_points += 5
        signals.append("Dedicated Company About page found")

    # Check for Legal (Privacy or Terms)
    has_legal = any(any(k in url.lower() for k in ["privacy", "terms"]) for url in crawled_pages.keys())
    if has_legal:
        pages_points += 5
        signals.append("Formal legal compliance pages detected (Privacy Policy / Terms)")
    else:
        warnings.append("No explicit Privacy Policy or Terms of Service links identified")

    score += pages_points
    breakdown.append({
        "category": "Page Structure & Legal",
        "points": pages_points,
        "max_points": 15,
        "status": "PASS" if pages_points >= 10 else "CHECK",
        "detail": f"{internal_links_count} internal routes, About: {'Yes' if has_about else 'No'}, Legal: {'Yes' if has_legal else 'No'}"
    })

    # 7. Social Presence (up to +5 pts)
    social_points = 0
    social_count = contacts_data.get("social_presence_count", 0)
    if social_count >= 3:
        social_points = 5
        signals.append(f"Multi-channel social media footprint ({social_count} platforms)")
    elif social_count >= 1:
        social_points = 3
        signals.append(f"Linked social media channels ({social_count} platform)")
    else:
        warnings.append("No verified social media profile links detected")

    score += social_points
    breakdown.append({
        "category": "Social Presence",
        "points": social_points,
        "max_points": 5,
        "status": "PASS" if social_points >= 3 else "LOW",
        "detail": f"{social_count} social platform(s) linked"
    })

    # 8. Technology Stack Consistency (up to +5 pts)
    tech_points = 5
    tech_list = tech_data.get("technologies", [])
    breakdown.append({
        "category": "Technology Consistency",
        "points": tech_points,
        "max_points": 5,
        "status": "PASS",
        "detail": f"{len(tech_list)} components detected ({', '.join(tech_list[:4])})"
    })
    score += tech_points

    # ================= DEDUCTIONS =================
    deductions = 0

    # Dummy text deduction (-20 max)
    dummy_signals = content_data.get("dummy_signals", [])
    if content_data.get("dummy_severity") == "HIGH":
        deductions += 20
        warnings.append("Major penalty: High concentration of Lorem Ipsum / placeholder text detected")
        breakdown.append({
            "category": "Dummy Content Deduction",
            "points": -20,
            "max_points": 0,
            "status": "FAIL",
            "detail": f"Extensive template dummy signals ({len(dummy_signals)} patterns matched)"
        })
    elif content_data.get("dummy_severity") == "MEDIUM":
        deductions += 10
        warnings.append("Template penalty: Isolated placeholder phrases detected")
        breakdown.append({
            "category": "Placeholder Content Deduction",
            "points": -10,
            "max_points": 0,
            "status": "CHECK",
            "detail": "Some template sample text detected"
        })

    # Broken links deduction (-10 max)
    broken_count = links_data.get("broken_count", 0)
    if broken_count >= 3:
        deductions += 10
        warnings.append("Quality penalty: Multiple broken internal links detected")
        breakdown.append({
            "category": "Broken Links Deduction",
            "points": -10,
            "max_points": 0,
            "status": "FAIL",
            "detail": f"{broken_count} broken internal routes"
        })
    elif broken_count >= 1:
        deductions += 5
        breakdown.append({
            "category": "Broken Links Deduction",
            "points": -5,
            "max_points": 0,
            "status": "CHECK",
            "detail": f"{broken_count} unreachable link(s)"
        })

    # Incomplete company identity (-10)
    if is_dummy_company:
        deductions += 10
        breakdown.append({
            "category": "Generic Template Deduction",
            "points": -10,
            "max_points": 0,
            "status": "FAIL",
            "detail": "Unfilled template business placeholders"
        })

    score -= deductions

    # Normalize strictly to 0-100
    final_score = max(0, min(100, round(score)))

    # A low score alone is not proof of a dummy website. Require direct
    # template evidence before using the dummy classification.
    explicit_dummy_evidence = (
        content_data.get("dummy_severity") == "HIGH"
        or is_dummy_company
        or dummy_email
        or dummy_phone
    )
    if explicit_dummy_evidence:
        classification = "LIKELY DEMO / DUMMY"
    elif final_score >= 75:
        classification = "LIKELY REAL BUSINESS"
    else:
        classification = "NEEDS VERIFICATION"

    return {
        "score": final_score,
        "classification": classification,
        "signals": signals,
        "warnings": warnings,
        "breakdown": breakdown,
        "dummy_evidence_found": explicit_dummy_evidence,
        "dummy_evidence_count": len(dummy_signals),
    }
