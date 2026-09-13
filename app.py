import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort

from config import Config
from database import init_db, save_scan, get_all_scans, get_scan_by_id, delete_scan, clear_history
from scanner import (
    validate_and_normalize_url,
    safe_fetch,
    parse_page_content,
    crawl_key_pages,
    check_ssl_and_https,
    analyze_domain,
    detect_technologies_and_hosting,
    analyze_content_quality,
    extract_contacts_and_identity,
    check_sample_links,
    calculate_authenticity_score,
)
from ai import run_ai_analysis

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLite database on startup
with app.app_context():
    init_db()


@app.route("/")
def index():
    """Landing Page and Interactive Analysis Dashboard."""
    return render_template("index.html")


@app.route("/robots.txt")
def robots():
    """Allow search engines to crawl the public analyzer page only."""
    return app.response_class(
        "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /report/\n",
        mimetype="text/plain",
    )


@app.route("/report/<int:scan_id>")
def view_report(scan_id):
    """Clean, standalone printable report page for PDF generation or export."""
    scan = get_scan_by_id(scan_id)
    if not scan:
        abort(404, description="Analysis report not found.")
    return render_template("report.html", report=scan)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Main website authenticity analysis endpoint.
    Performs multi-vector inspection: SSRF validation, DOM analysis, SSL, RDAP,
    technology profiling, content quality, dummy text detection, broken links,
    explainable scoring, and modular AI synthesis.
    """
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url", "").strip()

    if not raw_url:
        return jsonify({"error": "Please enter a valid website URL to analyze."}), 400

    # 1. URL Validation & SSRF Protection
    try:
        normalized_url, hostname = validate_and_normalize_url(raw_url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Invalid URL structure: {str(e)}"}), 400

    # 2. Fetch Homepage Content Safely
    try:
        fetched_home = safe_fetch(normalized_url)
    except TimeoutError:
        return jsonify({
            "error": "Unable to analyze this website because the server did not respond within the allowed time (Timeout)."
        }), 504
    except ConnectionError as e:
        return jsonify({
            "error": f"Unable to establish connection with '{hostname}'. The website may be offline or blocking automated requests."
        }), 502
    except ValueError as e:
        return jsonify({"error": f"Security restriction: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve website: {str(e)}"}), 500

    final_url = fetched_home["final_url"]
    headers = fetched_home["headers"]
    html = fetched_home["html"]

    # 3. DOM & Metadata Parsing
    homepage_data = parse_page_content(html, final_url)

    # 4. Safe Shallow Crawling (About, Contact, Privacy, Services)
    crawled_pages = crawl_key_pages(final_url, homepage_data["internal_links"], max_pages=Config.MAX_CRAWL_PAGES)

    # 5. Security & SSL Inspection
    security_data = check_ssl_and_https(hostname)

    # 6. Domain RDAP & DNS Longevity Analysis
    domain_data = analyze_domain(hostname)

    # 7. Technology & Hosting Platform Detection
    tech_data = detect_technologies_and_hosting(html, headers, hostname)

    # 8. Content Quality & Placeholder / Dummy Text Analysis
    content_data = analyze_content_quality(homepage_data, crawled_pages)

    # 9. Contact Details, Business Name & Social Profiles
    contacts_data = extract_contacts_and_identity(homepage_data, crawled_pages, hostname)

    # 10. Sample Internal & Broken Link Verification
    links_data = check_sample_links(final_url, homepage_data["internal_links"], max_links=6)

    # 11. Transparent Explainable Authenticity Scoring Engine
    scoring_result = calculate_authenticity_score(
        security_data=security_data,
        domain_data=domain_data,
        content_data=content_data,
        contacts_data=contacts_data,
        tech_data=tech_data,
        links_data=links_data,
        crawled_pages=crawled_pages,
        homepage_data=homepage_data,
    )

    # 12. Aggregate Payload for AI Analysis
    analysis_payload = {
        "url": raw_url,
        "normalized_url": final_url,
        "hostname": hostname,
        "score": scoring_result["score"],
        "classification": scoring_result["classification"],
        "signals": scoring_result["signals"],
        "warnings": scoring_result["warnings"],
        "breakdown": scoring_result["breakdown"],
        "security": security_data,
        "domain": domain_data,
        "technology": tech_data,
        "content_quality": content_data,
        "contacts": contacts_data,
        "broken_links": links_data,
        "pages_crawled_count": len(crawled_pages) + 1,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 13. Modular AI Synthesis (Rule-Based Heuristic or Optional Provider)
    ai_result = run_ai_analysis(analysis_payload)
    analysis_payload["ai_analysis"] = ai_result

    # 14. Persist to Database for History & Export
    try:
        scan_id = save_scan(analysis_payload)
        analysis_payload["id"] = scan_id
    except Exception as e:
        analysis_payload["id"] = None

    return jsonify(analysis_payload)


@app.route("/api/history", methods=["GET"])
def api_get_history():
    """Returns list of past scan reports."""
    scans = get_all_scans(limit=30)
    return jsonify(scans)


@app.route("/api/history/<int:scan_id>", methods=["DELETE"])
def api_delete_scan(scan_id):
    """Deletes a specific scan from history."""
    deleted = delete_scan(scan_id)
    if deleted:
        return jsonify({"message": f"Scan {scan_id} deleted successfully."})
    return jsonify({"error": "Scan record not found."}), 404


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    """Clears all scan history."""
    clear_history()
    return jsonify({"message": "Scan history cleared successfully."})


@app.route("/api/report/<int:scan_id>", methods=["GET"])
def api_get_report(scan_id):
    """Returns detailed JSON report for a specific scan."""
    scan = get_scan_by_id(scan_id)
    if not scan:
        return jsonify({"error": "Report not found."}), 404
    return jsonify(scan)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("FLASK_PORT", 5000)))
    app.run(host="0.0.0.0", port=port, debug=False)
