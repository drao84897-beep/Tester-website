# WebVerify AI — Website Authenticity Analyzer

**WebVerify AI** is an AI-powered website authenticity analysis platform designed to inspect technical, domain, content, and business signals to determine whether a website represents an active, genuine business, an unfinished development template, or requires further verification.

> **Honest Verification Guarantee**: WebVerify AI never claims 100% mathematical certainty that a website is real or fake. It produces an explainable **Authenticity Score (0–100)** and categorizes websites into probabilistic classifications:
> - **LIKELY REAL BUSINESS** (Score: 75–100)
> - **NEEDS VERIFICATION** (Score: 45–74)
> - **LIKELY DEMO / DUMMY** (Score: 0–44)

---

## Key Features

1. **Robust SSRF Defense & Safe Crawling**:
   - Sandboxes user-supplied URLs against private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`, `::1`), link-local, multicast, and cloud metadata endpoints (`169.254.169.254`).
   - Validates every hop in redirect chains before issuing requests.
   - Enforces strict request timeouts and maximum response size (3MB) limits to prevent memory exhaustion and zip bombs.

2. **Domain RDAP & Longevity Analysis (Zero Paid APIs)**:
   - Queries standard open ICANN RDAP endpoints (`https://rdap.org/domain/{domain}`) without requiring paid subscriptions or API keys.
   - Computes domain age in years, months, and days.
   - Transparently flags domains younger than 6 months as: *"New domain — requires additional verification"* (never falsely accusing a new business of being fake).
   - Resolves A, AAAA, MX, and NS records via DNS.

3. **SSL/TLS & HTTPS Enforcement**:
   - Analyzes peer SSL certificates (Subject, Issuer, Validity window, Expiration countdown, SAN).
   - Verifies automatic HTTP-to-HTTPS redirect enforcement.

4. **Hosting Platform & Jamstack Transparency**:
   - Detects platforms such as Vercel, Netlify, GitHub Pages, Cloudflare Pages, AWS Amplify, Render, Firebase, and Heroku.
   - **Signal, Not Proof**: Clearly displays: *"Hosting platform alone does not determine authenticity. Many legitimate startups and tech companies deploy production apps here."*

5. **Deep Content Quality & Dummy Signal Detection**:
   - Scans for Lorem Ipsum, placeholder business names (`[Your Company Name]`, `Insert Title Here`), persona names (`John Doe`, `Jane Doe`), placeholder emails (`user@example.com`), and dummy phone numbers (`123-456-7890`).
   - Analyzes heading structure (H1, H2, H3 hierarchy), word count volume, and business terminology density.

6. **Contact Information & Identity Extraction**:
   - Extracts and validates email addresses, international phone numbers, physical headquarters addresses, and social profile links (Facebook, Instagram, LinkedIn, X/Twitter, YouTube, TikTok, GitHub).

7. **Sample Broken Link Verification**:
   - Tests internal links with safe lightweight HEAD/GET requests.
   - Explicitly bypasses sensitive routes (`/login`, `/admin`, `/auth`, `/checkout`).

8. **Transparent Weighted Scoring Engine**:
   - Fully explainable positive weights and negative deductions with an itemized breakdown.

9. **Modular AI Analysis Layer**:
   - **Works 100% Out of the Box**: Ships with a built-in multi-factor rule-based intelligence synthesizer that requires no external API keys or subscriptions.
   - **Optional External LLMs**: Easily toggle Google Gemini, OpenAI, or Groq via `.env` by providing your own key.
   - Strictly programmed to avoid definitive claims ("100% real" or "100% fake").

10. **SaaS Results Dashboard & Printable Reports**:
    - Dark mode UI with glassmorphism, glowing SVG score circle gauge, and deep-dive inspection tabs.
    - Exportable and printable report format (`/report/<id>`) containing official platform disclaimers.
    - Persistent scan history stored in SQLite (ready for MySQL).

---

## Technology Stack

- **Frontend**: HTML5, CSS3 (Custom Dark Mode & Glassmorphism), Bootstrap 5.3.3, Vanilla JavaScript, Font Awesome 6.
- **Backend**: Python 3.11, Flask, REST API.
- **HTML & DOM Parsing**: BeautifulSoup4, lxml.
- **Network & DNS**: Requests, dnspython, socket, ssl, urllib.parse, ipaddress.
- **Database**: SQLite (default), structured for seamless MySQL configuration via `DATABASE_URI`.
- **AI Layer**: Modular heuristic synthesizer with optional external LLM adapter.

---

## Free & Public Services Used

- **ICANN RDAP / rdap.org**: Free open standard protocol (RFC 7480/7481/7482/7483) for domain registration lookup. Zero keys needed.
- **Standard Internet DNS**: Free public name resolution for A, MX, NS records.
- **Native OS SSL/TLS**: Standard X.509 handshake verification.
- **Font Awesome & Google Fonts**: Free public CDNs.

---

## Project Structure

```
tester/
│
├── app.py                      # Flask REST application & routing
├── config.py                   # Centralized configuration & SSRF controls
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Complete documentation
├── webverify.db                # SQLite database (auto-generated on startup)
│
├── scanner/                    # Website scanner engine modules
│   ├── __init__.py             # Scanner package exports
│   ├── website.py              # SSRF validation, safe fetcher & DOM parser
│   ├── security.py             # SSL certificate & HTTPS redirect check
│   ├── domain.py               # Free public RDAP & DNS domain age analyzer
│   ├── technology.py           # Tech stack & cloud hosting detector
│   ├── content.py              # Content completeness & Lorem Ipsum detector
│   ├── contacts.py             # Email, phone, address & social extractor
│   ├── links.py                # Safe internal link health sample verifier
│   └── scoring.py              # Transparent weighted scoring engine (0-100)
│
├── ai/                         # Modular AI analysis layer
│   ├── __init__.py             # AI package exports
│   └── analyzer.py             # Rule-based synthesizer + optional LLM adapter
│
├── database/                   # Data persistence layer
│   ├── __init__.py             # Database package exports
│   └── models.py               # SQLite schema, CRUD operations & MySQL compatibility
│
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Landing page & interactive dashboard
│   └── report.html             # Printable PDF export report view
│
├── static/                     # Static frontend assets
│   ├── css/
│   │   └── style.css           # Custom dark mode, glassmorphism & print CSS
│   └── js/
│       └── app.js              # Interactive UI, scan animations & history
│
└── tests/                      # Automated test suite
    ├── test_scanner.py         # Unit tests (SSRF, content, scoring, AI)
    └── test_live_api.py        # Integration tests (Flask client, live scan, DB)
```

---

## Installation & Setup (Windows)

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Clone / Open Directory
Open PowerShell or Command Prompt and navigate to the project directory:
```powershell
cd c:\Users\ali\Desktop\tester
```

### 3. Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(The application runs 100% out of the box with default settings without needing to edit `.env`.)*

### 6. Run the Application
```powershell
python app.py
```
The application will launch on:
```
http://127.0.0.1:5000
```

### 7. Deploy on Render

The repository includes `render.yaml` and `Procfile` for deployment on Render:

1. Connect the GitHub repository to Render.
2. Choose **New > Blueprint**.
3. Select this repository and deploy the detected `webverify-ai` service.

Render supplies the `PORT` environment variable automatically, and the app listens on all interfaces for hosted traffic.

---

## Running the Automated Tests

Run the complete automated test suite (18 unit & integration tests):
```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests
```

---

## API Documentation

### 1. Analyze Website
- **Endpoint**: `POST /api/analyze`
- **Request Body**:
  ```json
  {
    "url": "https://example.com"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "url": "https://example.com",
    "normalized_url": "https://example.com/",
    "score": 87,
    "classification": "LIKELY REAL BUSINESS",
    "signals": [
      "Modern SSL/TLS encryption active with automatic HTTPS redirection",
      "Established domain longevity: 29 years / 8 months"
    ],
    "warnings": [
      "No verifiable physical office address found"
    ],
    "domain": {
      "domain": "example.com",
      "age_formatted": "29 years / 8 months",
      "registrar": "RESERVED-Internet Assigned Numbers Authority"
    },
    "security": {
      "https_enabled": true,
      "ssl_valid": true,
      "issuer": "DigiCert Global Root G2"
    },
    "technology": {
      "hosting": "Standard Web Hosting",
      "technologies": ["HTML5", "CSS3", "JavaScript"]
    },
    "ai_analysis": {
      "summary": "The analyzed domain demonstrates consistent corporate signals...",
      "strengths": ["Valid HTTPS/TLS security enabled..."],
      "warnings": ["No verifiable physical office address..."],
      "recommendation": "The technical footprint is consistent with an active entity..."
    }
  }
  ```

### 2. Get Scan History
- **Endpoint**: `GET /api/history`
- **Response**: Array of recent scans with `id`, `domain`, `score`, `classification`, `created_at`.

### 3. Get Report by ID
- **Endpoint**: `GET /api/report/<id>`
- **Response**: Full JSON report data.

### 4. Delete Scan
- **Endpoint**: `DELETE /api/history/<id>`

### 5. Clear All History
- **Endpoint**: `DELETE /api/history`

### 6. Printable Report View
- **Endpoint**: `GET /report/<id>`
- Standalone HTML page with print-to-PDF formatting and disclaimer.

---

## Security & SSRF Protections

WebVerify AI strictly verifies every submitted hostname and redirect target:
1. Resolves domain names via DNS and verifies that resolved IP addresses do not belong to:
   - Loopback (`127.0.0.0/8`, `::1`)
   - Private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
   - Link-local addresses (`169.254.0.0/16`)
   - Cloud metadata servers (`169.254.169.254`, `metadata.google.internal`)
   - Multicast and reserved ranges
2. Blocks dangerous URI schemes (`file://`, `gopher://`, `ftp://`, `javascript:`).
3. Safe redirect follower prevents SSRF via redirect chaining.
4. Response stream cap at 3MB prevents resource starvation.

---

## Limitations

- **Public Web Footprint Only**: WebVerify AI analyzes publicly accessible web signals. It cannot access password-protected intranet sites, private portals, or paywalled databases.
- **Domain Privacy**: If a domain registrar redacts RDAP records under GDPR/domain privacy, domain age is estimated from public registration events, or clearly noted as restricted.
- **Probabilistic Indicators**: Technical signals (such as hosting on modern platforms or holding an SSL certificate) are indicators and do not constitute statutory legal proof of business standing.
