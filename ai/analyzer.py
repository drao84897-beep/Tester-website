import json
import requests
from config import Config


def generate_rule_based_ai_summary(payload):
    """
    High-fidelity heuristic intelligence synthesizer.
    Produces balanced, probabilistic, and explainable authenticity assessments
    without requiring any external paid API or key.
    """
    score = payload.get("score", 50)
    classification = payload.get("classification", "NEEDS VERIFICATION")
    domain_info = payload.get("domain", {})
    security_info = payload.get("security", {})
    content_info = payload.get("content_quality", {})
    contacts_info = payload.get("contacts", {})
    tech_info = payload.get("technology", {})

    # 1. Summary Formulation
    if classification == "LIKELY REAL BUSINESS":
        summary = (
            f"The analyzed domain demonstrates consistent corporate signals, valid SSL/TLS encryption, "
            f"and established technical infrastructure. Business identity markers for '{contacts_info.get('business_name', 'the entity')}' "
            f"are present across multiple pages with coherent contact avenues. Observed indicators are consistent "
            f"with an active enterprise, though public web analysis cannot replace formal statutory register verification."
        )
    elif classification == "NEEDS VERIFICATION":
        summary = (
            f"The website displays moderate authenticity indicators but lacks several key credibility signals. "
            f"While baseline technical elements are functional, factors such as "
            f"{'recent domain registration, ' if domain_info.get('new_domain_flag') else 'incomplete contact disclosures, '}"
            f"limited page depth, or missing corporate credentials indicate that additional verification is recommended before engaging in commercial transactions."
        )
    else:
        summary = (
            f"Multiple indicators characteristic of an early development template, prototype, or dummy deployment were detected. "
            f"The presence of {'placeholder/Lorem Ipsum content, ' if content_info.get('dummy_severity') != 'LOW' else 'minimal business information, '}"
            f"unfinished navigation routes, or missing operational identity suggests this website does not currently represent a fully verified, actively trading commercial entity."
        )

    # 2. Strengths Formulation
    strengths = []
    if security_info.get("https_enabled") and security_info.get("ssl_valid"):
        strengths.append(f"Valid HTTPS/TLS security enabled (Issuer: {security_info.get('issuer', 'Standard CA')})")
    if security_info.get("http_to_https_redirect"):
        strengths.append("Enforces automatic HTTP to HTTPS redirect for transport layer security")
    if contacts_info.get("has_email") and not contacts_info.get("is_placeholder_email"):
        strengths.append("Publicly accessible corporate contact email address identified")
    if contacts_info.get("has_phone") and not contacts_info.get("is_placeholder_phone"):
        strengths.append("Direct operational telephone contact number provided")
    if contacts_info.get("has_address"):
        strengths.append("Physical location or postal address indicators detected")
    if contacts_info.get("social_presence_count", 0) > 0:
        strengths.append(f"Linked social media presence across {contacts_info['social_presence_count']} major platform(s)")
    if domain_info.get("age_days") and domain_info["age_days"] >= 365:
        strengths.append(f"Established domain history with continuous registration ({domain_info.get('age_formatted')})")
    if content_info.get("word_count", 0) >= 300:
        strengths.append(f"Substantive written content and detailed service offerings ({content_info['word_count']} words)")
    if len(tech_info.get("technologies", [])) >= 3:
        strengths.append(f"Cohesive modern web technology stack ({', '.join(tech_info['technologies'][:3])})")

    if not strengths:
        strengths.append("Standard web server response received without immediate transport failures")

    # 3. Warnings Formulation
    warnings = []
    if not security_info.get("ssl_valid"):
        warnings.append("Absence of trusted SSL certificate or active HTTPS transport encryption")
    if domain_info.get("new_domain_flag"):
        warnings.append("Recently registered domain (< 6 months) — requires additional background verification")
    elif domain_info.get("is_platform_subdomain"):
        warnings.append(f"Deployed on a shared developer subdomain ({domain_info.get('platform_name')})")
    if content_info.get("dummy_severity") == "HIGH":
        warnings.append("Significant volume of Latin dummy text (Lorem Ipsum) or unedited template placeholders detected")
    elif content_info.get("dummy_severity") == "MEDIUM":
        warnings.append("Isolated template sample phrases detected within published text")
    if contacts_info.get("is_placeholder_email") or contacts_info.get("is_placeholder_phone"):
        warnings.append("Contact details appear to utilize default template values (e.g. user@example.com or 123-456-7890)")
    if not contacts_info.get("has_address"):
        warnings.append("No verifiable physical office address or corporate headquarters found")
    if content_info.get("word_count", 0) < 150:
        warnings.append("Sparse text content across indexed public pages")

    if not warnings:
        warnings.append("No critical negative flags detected on publicly crawlable pages")

    # 4. Probabilistic Recommendation
    if classification == "LIKELY REAL BUSINESS":
        recommendation = (
            "The technical and content footprint is consistent with an active business. "
            "For significant financial or contractual engagements, standard due diligence (such as verifying statutory corporate filings) is always prudent."
        )
    elif classification == "NEEDS VERIFICATION":
        recommendation = (
            "Cross-reference stated contact channels directly and inspect external customer reviews or government corporate registrations before providing sensitive information or payments."
        )
    else:
        recommendation = (
            "Exercise heightened caution. The website exhibits substantial characteristics of a development prototype or template. "
            "Independent verification of identity and business registration is strongly advised before transacting."
        )

    return {
        "status": "completed",
        "provider": "Built-in Rule-Based Intelligence Engine",
        "is_ai_api_used": False,
        "summary": summary,
        "strengths": strengths[:6],
        "warnings": warnings[:6],
        "recommendation": recommendation,
        "disclaimer": "This analysis provides probabilistic indicators based on publicly accessible data, not legal proof of business legitimacy.",
    }


def query_external_llm(payload):
    """
    Optionally queries an external LLM (Gemini, OpenAI, Groq) if an API key is configured.
    Falls back gracefully if the provider fails or times out.
    """
    provider = Config.AI_PROVIDER
    api_key = Config.AI_API_KEY
    if not api_key or provider in ("none", "", "disabled"):
        return None

    prompt = f"""
You are a senior website authenticity and cybersecurity auditor.
Analyze the following structured technical signals extracted from a website scan:
- Target Domain: {payload.get('url')}
- Authenticity Score: {payload.get('score')}/100
- Initial Classification: {payload.get('classification')}
- SSL / Security: {payload.get('security', {}).get('status_summary')} (Issuer: {payload.get('security', {}).get('issuer')})
- Domain Age: {payload.get('domain', {}).get('age_formatted')} (Note: {payload.get('domain', {}).get('note')})
- Hosting Platform: {payload.get('technology', {}).get('hosting')}
- Dummy Text Severity: {payload.get('content_quality', {}).get('dummy_severity')}
- Contact Signals: Emails={payload.get('contacts', {}).get('has_email')}, Phones={payload.get('contacts', {}).get('has_phone')}, Address={payload.get('contacts', {}).get('has_address')}
- Social Platforms: {payload.get('contacts', {}).get('social_presence_count')}

CRITICAL INSTRUCTIONS:
1. NEVER declare 100% certainty that a website is real or fake.
2. NEVER use absolute terms like 'definitely fraudulent' or 'guaranteed genuine'.
3. Use careful, probabilistic language.
4. Output STRICT JSON with keys:
   "summary": string,
   "strengths": list of strings,
   "warnings": list of strings,
   "recommendation": string
"""

    try:
        # OpenAI or Groq compatible endpoint
        if provider in ("openai", "groq"):
            endpoint = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "https://api.groq.com/openai/v1/chat/completions"
            model = Config.AI_MODEL or ("gpt-4o-mini" if provider == "openai" else "llama-3.1-8b-instant")
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"} if provider == "openai" else None
            }
            resp = requests.post(endpoint, headers=headers, json=body, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return {
                    "status": "completed",
                    "provider": f"External LLM ({provider.title()} / {model})",
                    "is_ai_api_used": True,
                    "summary": parsed.get("summary", ""),
                    "strengths": parsed.get("strengths", []),
                    "warnings": parsed.get("warnings", []),
                    "recommendation": parsed.get("recommendation", ""),
                    "disclaimer": "This analysis provides probabilistic indicators based on publicly accessible data, not legal proof of business legitimacy.",
                }
    except Exception:
        # Graceful fallback on network error or bad response
        pass

    return None


def run_ai_analysis(payload):
    """
    Main entry point for AI analysis layer.
    Checks for optional external AI credentials first; otherwise uses the comprehensive built-in intelligence engine.
    """
    external_result = query_external_llm(payload)
    if external_result:
        return external_result

    # Default to built-in rule-based intelligence synthesizer
    return generate_rule_based_ai_summary(payload)
