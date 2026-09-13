import re


def detect_technologies_and_hosting(html, headers, hostname):
    """
    Detects frontend libraries, frameworks, CMS, backend signals, and hosting platforms.
    """
    html_lower = html.lower()
    headers_lower = {k.lower(): v.lower() for k, v in headers.items()}

    detected_tech = []
    hosting_platform = "Standard Web Hosting"
    hosting_interpretation = "Hosting platform alone does not determine authenticity."

    # 1. Hosting / Platform Detection
    if hostname.endswith(".vercel.app") or "x-vercel-id" in headers_lower or "x-vercel-cache" in headers_lower:
        hosting_platform = "Vercel"
        hosting_interpretation = "Modern serverless frontend platform. Many legitimate startups and tech companies deploy production apps here."
    elif hostname.endswith(".netlify.app") or "x-nf-request-id" in headers_lower or "netlify" in headers_lower.get("server", ""):
        hosting_platform = "Netlify"
        hosting_interpretation = "Jamstack & serverless web platform. Frequently used for modern landing pages, documentation, and SaaS websites."
    elif hostname.endswith(".github.io"):
        hosting_platform = "GitHub Pages"
        hosting_interpretation = "Static site hosting by GitHub. Frequently used for open-source projects, developer portfolios, and documentation."
    elif hostname.endswith(".pages.dev") or "cf-ray" in headers_lower or "cloudflare" in headers_lower.get("server", ""):
        hosting_platform = "Cloudflare"
        hosting_interpretation = "Enterprise edge network and CDN. Highly reputable infrastructure used globally."
    elif hostname.endswith(".onrender.com") or "x-render-origin-server" in headers_lower:
        hosting_platform = "Render"
        hosting_interpretation = "Modern unified cloud platform for web services and static sites."
    elif hostname.endswith(".web.app") or hostname.endswith(".firebaseapp.com"):
        hosting_platform = "Google Firebase"
        hosting_interpretation = "Google Cloud developer platform."
    elif hostname.endswith(".amplifyapp.com") or any(k.startswith("x-amz-") for k in headers_lower):
        hosting_platform = "Amazon Web Services (AWS)"
        hosting_interpretation = "Enterprise cloud infrastructure."
    elif "x-powered-by" in headers_lower:
        powered_by = headers_lower["x-powered-by"]
        if "wp engine" in powered_by:
            hosting_platform = "WP Engine"
        elif "express" in powered_by:
            hosting_platform = "Node.js (Express)"
        elif "next.js" in powered_by:
            hosting_platform = "Next.js Hosting"

    # 2. Technology Signatures
    tech_signatures = [
        # CMS
        ("WordPress", r"wp-content|wp-includes|meta\s+name=[\"']generator[\"']\s+content=[\"'][^\"']*wordpress"),
        ("Shopify", r"cdn\.shopify\.com|shopify-section"),
        ("Webflow", r"uploads-ssl\.webflow\.com|webflow\.js"),
        ("Squarespace", r"static1\.squarespace\.com"),
        ("Wix", r"static\.wixstatic\.com|wix\.com"),

        # Modern Frameworks
        ("Next.js", r"/_next/static|__next|data-reactroot"),
        ("React", r"react\.production\.min\.js|data-reactroot|react-dom"),
        ("Vue.js", r"vue\.runtime|data-v-[a-f0-9]+|vue\.min\.js"),
        ("Nuxt.js", r"/_nuxt/|__nuxt"),
        ("Angular", r"ng-version|ng-app"),
        ("Svelte", r"svelte-[a-z0-9]+"),

        # UI & Styling
        ("Bootstrap", r"bootstrap(?:\.min)?\.(?:css|js)|class=[\"'][^\"']*\b(?:btn-(?:primary|secondary)|container-fluid|col-md-)\b"),
        ("Tailwind CSS", r"class=[\"'][^\"']*\b(?:flex|grid|hidden|text-center|bg-blue-|p-[0-9]|mx-auto)\b"),
        ("Font Awesome", r"font-awesome|fa-[a-z0-9-]+"),

        # JavaScript & Bundlers
        ("jQuery", r"jquery(?:\.min)?\.js|\$\(document\)\.ready"),
        ("Vite", r"/@vite/client|<script type=\"module\" src=\"/src/"),

        # Backend Hints
        ("PHP", r"\.php(?:\?|\"|')|x-powered-by:\s*php"),
        ("Laravel", r"laravel|xsrf-token"),
        ("Django", r"csrfmiddlewaretoken"),
        ("Flask", r"flask|session="),
        ("ASP.NET", r"aspnetcore|viewstate|__VIEWSTATE"),
    ]

    for name, pattern in tech_signatures:
        if re.search(pattern, html, re.IGNORECASE):
            if name not in detected_tech:
                detected_tech.append(name)

    # Check headers for additional tech
    server_header = headers.get("Server", "")
    if "nginx" in server_header.lower():
        detected_tech.append("Nginx")
    elif "apache" in server_header.lower():
        detected_tech.append("Apache")
    elif "caddy" in server_header.lower():
        detected_tech.append("Caddy")

    powered = headers.get("X-Powered-By", "")
    if "php" in powered.lower() and "PHP" not in detected_tech:
        detected_tech.append("PHP")

    return {
        "hosting": hosting_platform,
        "hosting_interpretation": hosting_interpretation,
        "technologies": detected_tech if detected_tech else ["HTML5", "CSS3", "JavaScript"],
    }
