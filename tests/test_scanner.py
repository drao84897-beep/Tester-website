import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scanner.website import is_safe_ip, validate_and_normalize_url, parse_page_content
from scanner.content import analyze_content_quality
from scanner.contacts import extract_contacts_and_identity
from scanner.technology import detect_technologies_and_hosting
from scanner.domain import calculate_domain_age
from scanner.scoring import calculate_authenticity_score
from ai.analyzer import generate_rule_based_ai_summary


class TestSSRFAndSecurity(unittest.TestCase):
    """Tests for SSRF prevention, IP validation, and URL normalization."""

    def test_private_ips_blocked(self):
        self.assertFalse(is_safe_ip("127.0.0.1"))
        self.assertFalse(is_safe_ip("10.0.0.1"))
        self.assertFalse(is_safe_ip("192.168.1.100"))
        self.assertFalse(is_safe_ip("172.16.0.1"))
        self.assertFalse(is_safe_ip("169.254.169.254"))  # Cloud metadata
        self.assertFalse(is_safe_ip("0.0.0.0"))
        self.assertFalse(is_safe_ip("::1"))

    def test_public_ips_allowed(self):
        self.assertTrue(is_safe_ip("8.8.8.8"))
        self.assertTrue(is_safe_ip("1.1.1.1"))
        self.assertTrue(is_safe_ip("93.184.216.34"))

    def test_dangerous_schemes_rejected(self):
        with self.assertRaises(ValueError):
            validate_and_normalize_url("file:///etc/passwd")
        with self.assertRaises(ValueError):
            validate_and_normalize_url("gopher://127.0.0.1:70")
        with self.assertRaises(ValueError):
            validate_and_normalize_url("ftp://example.com")
        with self.assertRaises(ValueError):
            validate_and_normalize_url("javascript:alert(1)")

    def test_localhost_and_internal_hosts_rejected(self):
        with self.assertRaises(ValueError):
            validate_and_normalize_url("http://localhost:8080")
        with self.assertRaises(ValueError):
            validate_and_normalize_url("http://127.0.0.1")
        with self.assertRaises(ValueError):
            validate_and_normalize_url("http://169.254.169.254/latest/meta-data/")

    def test_url_normalization(self):
        norm, host = validate_and_normalize_url("example.com")
        self.assertEqual(norm, "https://example.com/")
        self.assertEqual(host, "example.com")


class TestContentAndDummyDetection(unittest.TestCase):
    """Tests for placeholder and dummy content detection."""

    def test_lorem_ipsum_detected(self):
        sample_html = """
        <html>
            <body>
                <h1>Welcome to our site</h1>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <p>John Doe is our CEO.</p>
            </body>
        </html>
        """
        homepage_data = parse_page_content(sample_html, "https://example.com")
        result = analyze_content_quality(homepage_data)

        self.assertGreater(len(result["dummy_signals"]), 0)
        labels = [d["label"] for d in result["dummy_signals"]]
        self.assertTrue(any("Lorem Ipsum" in l for l in labels))
        self.assertTrue(any("John Doe" in l for l in labels))

    def test_clean_business_content(self):
        sample_html = """
        <html>
            <body>
                <h1>Enterprise Cloud Solutions</h1>
                <p>We provide comprehensive software engineering, IT consulting, and automated security solutions for global clients.</p>
                <h2>Our Services & Products</h2>
                <p>Cloud migration, database architecture, and compliance monitoring with 24/7 dedicated customer support.</p>
            </body>
        </html>
        """
        homepage_data = parse_page_content(sample_html, "https://example.com")
        result = analyze_content_quality(homepage_data)
        self.assertEqual(result["dummy_severity"], "LOW")
        self.assertIn("services", result["business_keywords_found"])


class TestContactsAndIdentity(unittest.TestCase):
    """Tests for business identity, email, phone, and social detection."""

    def test_contact_extraction(self):
        html = """
        <html>
            <head><title>Acme Corporation | Innovations</title></head>
            <body>
                <h1>Contact Acme Corp</h1>
                <p>Email our team at contact@acme.com or reach us by telephone at +1 (555) 234-5678.</p>
                <p>Visit our headquarters: 450 Lexington Avenue, Suite 1200, New York, NY 10017.</p>
                <a href="https://linkedin.com/company/acme">LinkedIn</a>
                <a href="https://twitter.com/acme">Twitter</a>
            </body>
        </html>
        """
        data = parse_page_content(html, "https://acme.com")
        contacts = extract_contacts_and_identity(data, base_hostname="acme.com")

        self.assertIn("contact@acme.com", contacts["emails"])
        self.assertTrue(contacts["has_address"])
        self.assertIn("LinkedIn", contacts["social_links"])
        self.assertIn("X (Twitter)", contacts["social_links"])
        self.assertEqual(contacts["social_presence_count"], 2)


class TestTechnologyAndHosting(unittest.TestCase):
    """Tests for technology and cloud hosting platform detection."""

    def test_hosting_platform_signals(self):
        res_vercel = detect_technologies_and_hosting("<html></html>", {"x-vercel-id": "iad1::123"}, "app.vercel.app")
        self.assertEqual(res_vercel["hosting"], "Vercel")
        self.assertIn("serverless", res_vercel["hosting_interpretation"].lower())

        res_netlify = detect_technologies_and_hosting("<html></html>", {"x-nf-request-id": "abc"}, "site.netlify.app")
        self.assertEqual(res_netlify["hosting"], "Netlify")

    def test_framework_detection(self):
        html = '<div id="__next"><script src="/_next/static/main.js"></script><div class="btn-primary flex"></div></div>'
        res = detect_technologies_and_hosting(html, {}, "example.com")
        self.assertIn("Next.js", res["technologies"])
        self.assertIn("Bootstrap", res["technologies"])
        self.assertIn("Tailwind CSS", res["technologies"])


class TestDomainLongevity(unittest.TestCase):
    """Tests for domain age computation."""

    def test_domain_age_calculation(self):
        days, age_str = calculate_domain_age("2020-01-01T00:00:00Z")
        self.assertIsNotNone(days)
        self.assertGreater(days, 365)
        self.assertIn("year", age_str)


class TestScoringEngine(unittest.TestCase):
    """Tests for transparent weighted scoring and classification."""

    def test_likely_real_business_score(self):
        sec = {"https_enabled": True, "ssl_valid": True, "http_to_https_redirect": True, "issuer": "DigiCert"}
        dom = {"age_days": 1200, "age_formatted": "3 years / 3 months", "is_platform_subdomain": False, "new_domain_flag": False}
        content = {"word_count": 850, "business_keywords_found": ["services", "products", "about us", "support", "pricing"], "dummy_severity": "LOW", "has_h1": True}
        contacts = {"business_name": "Apex Cloud Systems", "is_placeholder_company": False, "has_email": True, "has_phone": True, "has_address": True, "social_presence_count": 3}
        tech = {"technologies": ["React", "Bootstrap", "Nginx"], "hosting": "Standard Web Hosting"}
        links = {"broken_count": 0, "working_count": 5}
        crawled = {"https://apex.com/about": {}, "https://apex.com/privacy": {}}
        home = {"title": "Apex Cloud Systems - Official Enterprise Portal", "internal_links": ["/about", "/services", "/contact", "/privacy", "/terms"]}

        res = calculate_authenticity_score(sec, dom, content, contacts, tech, links, crawled, home)
        self.assertGreaterEqual(res["score"], 75)
        self.assertEqual(res["classification"], "LIKELY REAL BUSINESS")
        self.assertGreater(len(res["signals"]), 3)

    def test_likely_demo_dummy_score(self):
        sec = {"https_enabled": False, "ssl_valid": False, "http_to_https_redirect": False}
        dom = {"age_days": 10, "age_formatted": "10 days", "is_platform_subdomain": True, "new_domain_flag": True}
        content = {"word_count": 80, "business_keywords_found": [], "dummy_severity": "HIGH", "has_h1": False, "dummy_signals": [{"label": "Lorem Ipsum", "occurrences": 5}]}
        contacts = {"business_name": "Your Company Name", "is_placeholder_company": True, "has_email": False, "has_phone": False, "has_address": False, "social_presence_count": 0}
        tech = {"technologies": ["HTML5"], "hosting": "Vercel"}
        links = {"broken_count": 3, "working_count": 1}
        crawled = {}
        home = {"title": "Home", "internal_links": []}

        res = calculate_authenticity_score(sec, dom, content, contacts, tech, links, crawled, home)
        self.assertLess(res["score"], 45)
        self.assertEqual(res["classification"], "LIKELY DEMO / DUMMY")


class TestAIAnalysis(unittest.TestCase):
    """Tests for modular rule-based intelligence synthesizer."""

    def test_ai_synthesis_output_structure(self):
        payload = {
            "score": 82,
            "classification": "LIKELY REAL BUSINESS",
            "domain": {"age_formatted": "2 years", "note": "Established domain"},
            "security": {"https_enabled": True, "ssl_valid": True, "issuer": "Let's Encrypt"},
            "content_quality": {"word_count": 500, "dummy_severity": "LOW"},
            "contacts": {"business_name": "Tech Corp", "has_email": True, "has_phone": True, "social_presence_count": 2},
            "technology": {"hosting": "Netlify", "technologies": ["Next.js", "Tailwind CSS"]},
        }
        res = generate_rule_based_ai_summary(payload)
        self.assertIn("summary", res)
        self.assertIn("strengths", res)
        self.assertIn("warnings", res)
        self.assertIn("recommendation", res)
        self.assertFalse(res["is_ai_api_used"])
        # Verify careful probabilistic language (no 100% certainty)
        self.assertNotIn("100% real", res["summary"].lower())
        self.assertNotIn("100% fake", res["summary"].lower())


if __name__ == "__main__":
    unittest.main()
