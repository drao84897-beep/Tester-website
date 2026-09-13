let currentScanResult = null;
let scanProgressInterval = null;

// Handle URL Submission
async function handleAnalyzeSubmit(event) {
  if (event) event.preventDefault();
  
  const urlInput = document.getElementById("url-input");
  const rawUrl = urlInput.value.trim();
  const alertBox = document.getElementById("alert-box");
  const progressBox = document.getElementById("scan-progress-box");
  const resultsDash = document.getElementById("results-dashboard");
  const analyzeBtn = document.getElementById("analyze-btn");

  alertBox.classList.add("d-none");
  alertBox.innerHTML = "";

  if (!rawUrl) {
    showAlert("Please enter a website URL.", "warning");
    return;
  }

  // UI State: Scanning in progress
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Analyzing...';
  resultsDash.classList.add("d-none");
  progressBox.classList.remove("d-none");
  document.getElementById("progress-target-url").textContent = `Target: ${rawUrl}`;

  startProgressStepsAnimation();

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: rawUrl }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Server error (${response.status})`);
    }

    // Success: Stop progress & Render
    stopProgressStepsAnimation();
    progressBox.classList.add("d-none");
    currentScanResult = data;
    renderResults(data);

  } catch (err) {
    stopProgressStepsAnimation();
    progressBox.classList.add("d-none");
    showAlert(err.message, "danger");
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = '<span>ANALYZE WEBSITE</span><i class="fa-solid fa-arrow-right ms-2"></i>';
  }
}

// Sample Click Handler
function fillAndScan(sampleUrl) {
  const urlInput = document.getElementById("url-input");
  urlInput.value = sampleUrl;
  handleAnalyzeSubmit(null);
}

// Reset UI to scan another
function resetToScanAnother() {
  document.getElementById("results-dashboard").classList.add("d-none");
  document.getElementById("landing-educational-sections").classList.remove("d-none");
  const urlInput = document.getElementById("url-input");
  urlInput.value = "";
  urlInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Progress Steps Simulation Animation
function startProgressStepsAnimation() {
  const steps = [
    document.getElementById("step-1"),
    document.getElementById("step-2"),
    document.getElementById("step-3"),
    document.getElementById("step-4"),
    document.getElementById("step-5"),
    document.getElementById("step-6"),
    document.getElementById("step-7"),
  ];

  // Reset steps
  steps.forEach((step) => {
    if (!step) return;
    step.className = "step-item py-1";
    step.querySelector("i").className = "fa-regular fa-circle me-2";
  });

  let currentStep = 0;
  if (steps[0]) {
    steps[0].className = "step-item active py-1";
    steps[0].querySelector("i").className = "fa-solid fa-circle-notch fa-spin me-2";
  }

  scanProgressInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      if (!steps[currentStep] || !steps[currentStep + 1]) return;
      steps[currentStep].className = "step-item done py-1";
      steps[currentStep].querySelector("i").className = "fa-solid fa-check me-2";
      currentStep++;
      steps[currentStep].className = "step-item active py-1";
      steps[currentStep].querySelector("i").className = "fa-solid fa-circle-notch fa-spin me-2";
    }
  }, 900);
}

function stopProgressStepsAnimation() {
  if (scanProgressInterval) {
    clearInterval(scanProgressInterval);
    scanProgressInterval = null;
  }
}

// Render Results Dashboard
function renderResults(data) {
  const dash = document.getElementById("results-dashboard");
  dash.classList.remove("d-none");

  // Populate Target URL & Timestamp
  document.getElementById("res-target-url").textContent = data.url;
  document.getElementById("res-normalized-url").textContent = `Resolved destination: ${data.normalized_url}`;
  document.getElementById("scan-timestamp").textContent = data.created_at || "Just now";

  // Score & Gauge
  const score = data.score;
  const scoreBar = document.getElementById("score-circle-bar");
  const scoreNum = document.getElementById("score-num");
  const badge = document.getElementById("classification-badge");

  // Animate counter
  animateScoreCounter(scoreNum, score);

  // SVG Circumference for radius 70 is 2 * PI * 70 ≈ 439.82
  const circumference = 440;
  const offset = circumference - (circumference * score) / 100;
  scoreBar.style.strokeDashoffset = offset;

  // Set colors based on score
  const classification = data.classification || "NEEDS VERIFICATION";
  if (classification === "LIKELY REAL BUSINESS") {
    scoreBar.style.stroke = "#10b981";
    badge.className = "badge-classification badge-real";
    badge.textContent = "PROFESSIONAL WEBSITE";
  } else if (classification === "LIKELY DEMO / DUMMY") {
    scoreBar.style.stroke = "#ef4444";
    badge.className = "badge-classification badge-demo";
    badge.textContent = "DUMMY / UNFINISHED WEBSITE";
  } else {
    scoreBar.style.stroke = "#f59e0b";
    badge.className = "badge-classification badge-verify";
    badge.textContent = "PARTIALLY PROFESSIONAL / VERIFY";
  }

  // Quick Summary Cards
  const sec = data.security || {};
  const dom = data.domain || {};
  const content = data.content_quality || {};
  const contacts = data.contacts || {};
  const tech = data.technology || {};

  setSummaryPill("sum-https", sec.https_enabled ? "PASS" : "FAIL", sec.https_enabled ? "pill-pass" : "pill-fail");
  setSummaryPill("sum-ssl", sec.ssl_valid ? "PASS" : (sec.https_enabled ? "CHECK" : "FAIL"), sec.ssl_valid ? "pill-pass" : "pill-fail");
  setSummaryPill("sum-identity", contacts.business_name && !contacts.is_placeholder_company ? "PASS" : "CHECK", "pill-pass");
  setSummaryPill("sum-contact", contacts.has_email || contacts.has_phone ? "PASS" : "CHECK", contacts.has_email ? "pill-pass" : "pill-check");
  setSummaryPill("sum-domain", dom.age_days >= 365 ? "PASS" : "CHECK", dom.age_days >= 365 ? "pill-pass" : "pill-check");
  setSummaryPill("sum-content", content.content_rating === "High" ? "PASS" : (content.content_rating === "Moderate" ? "CHECK" : "LOW"), content.content_rating === "High" ? "pill-pass" : "pill-check");
  setSummaryPill("sum-social", contacts.social_presence_count > 0 ? "PASS" : "LOW", contacts.social_presence_count > 0 ? "pill-pass" : "pill-check");
  setSummaryPill("sum-dummy", content.dummy_severity || "LOW", content.dummy_severity === "LOW" ? "pill-pass" : (content.dummy_severity === "MEDIUM" ? "pill-check" : "pill-fail"));
  
  document.getElementById("sum-hosting").textContent = tech.hosting || "Standard";
  document.getElementById("hosting-interpretation-text").textContent = tech.hosting_interpretation || "Hosting platform alone does not determine authenticity.";

  // AI Analysis Section
  const ai = data.ai_analysis || {};
  document.getElementById("ai-provider-badge").textContent = ai.provider || "Rule-Based Intelligence";
  document.getElementById("ai-summary-text").textContent = ai.summary || "No summary available.";
  document.getElementById("ai-recommendation-text").textContent = ai.recommendation || "Proceed with standard verification.";

  const verdictExplanation = document.getElementById("verdict-explanation");
  if (verdictExplanation) {
    const verdictLabel = classification === "LIKELY REAL BUSINESS" ? "Professional website" : (classification === "LIKELY DEMO / DUMMY" ? "Dummy or unfinished website" : "Partially professional, but verification required");
    const reasons = [...(data.warnings || []), ...(data.signals || [])].slice(0, 6);
    const reasonText = reasons.length > 0
      ? reasons.map(reason => `- ${reason}`).join("\n")
      : "- No detailed signals were returned by the scan.";
    verdictExplanation.style.whiteSpace = "pre-line";
    verdictExplanation.textContent = `${verdictLabel}\n${ai.summary || "The result is based on the technical, domain, content, contact, and business signals found during the scan."}\n\nWhy this result:\n${reasonText}`;
  }

  const strengthsList = document.getElementById("ai-strengths-list");
  strengthsList.innerHTML = (ai.strengths || []).map(s => `<li class="py-1"><i class="fa-solid fa-check text-success me-2"></i>${s}</li>`).join("");

  const warningsList = document.getElementById("ai-warnings-list");
  warningsList.innerHTML = (ai.warnings || []).map(w => `<li class="py-1"><i class="fa-solid fa-triangle-exclamation text-warning me-2"></i>${w}</li>`).join("");

  // TAB 1: Verified Signals & Warnings
  const sigContainer = document.getElementById("verified-signals-list");
  sigContainer.innerHTML = (data.signals || []).map(sig => `
    <div class="signal-item">
      <i class="fa-solid fa-circle-check signal-icon-pass"></i>
      <span class="text-white-50 small">${sig}</span>
    </div>
  `).join("");

  const warnContainer = document.getElementById("detected-warnings-list");
  warnContainer.innerHTML = (data.warnings || []).map(wrn => `
    <div class="signal-item">
      <i class="fa-solid fa-triangle-exclamation signal-icon-warn"></i>
      <span class="text-white-50 small">${wrn}</span>
    </div>
  `).join("");

  // TAB 2: Scoring Breakdown Table
  const breakdownTbody = document.getElementById("score-breakdown-tbody");
  breakdownTbody.innerHTML = (data.breakdown || []).map(row => {
    let badgeClass = "bg-success";
    if (row.status === "CHECK") badgeClass = "bg-warning text-dark";
    else if (row.status === "FAIL" || row.status === "LOW") badgeClass = "bg-danger";

    const pointsPrefix = row.points > 0 ? `+${row.points}` : `${row.points}`;
    return `
      <tr>
        <td class="fw-bold text-white small">${row.category}</td>
        <td class="text-white-50 small">${row.detail}</td>
        <td class="fw-bold ${row.points >= 0 ? 'text-success' : 'text-danger'} small">${pointsPrefix}</td>
        <td><span class="badge ${badgeClass} small">${row.status}</span></td>
      </tr>
    `;
  }).join("");

  // TAB 3: Domain & RDAP
  document.getElementById("dom-name").textContent = dom.domain || data.hostname;
  document.getElementById("dom-age").textContent = dom.age_formatted || "Not available";
  document.getElementById("dom-registrar").textContent = dom.registrar || "Not available — external verification required";
  document.getElementById("dom-created").textContent = dom.creation_date ? dom.creation_date.split("T")[0] : "Not available";
  document.getElementById("dom-nameservers").textContent = (dom.nameservers && dom.nameservers.length > 0) ? dom.nameservers.join(", ") : "Standard DNS records";

  // TAB 4: Technologies
  document.getElementById("tech-hosting-name").textContent = tech.hosting || "Standard";
  document.getElementById("tech-hosting-desc").textContent = tech.hosting_interpretation || "";
  const techBadges = document.getElementById("tech-badges-list");
  techBadges.innerHTML = (tech.technologies || []).map(t => `<span class="tech-pill"><i class="fa-solid fa-check text-info"></i> ${t}</span>`).join("");

  // TAB 5: Content Quality & Dummy Checks
  document.getElementById("content-word-count").textContent = content.word_count || 0;
  document.getElementById("content-rating-val").textContent = content.content_rating || "Standard";
  document.getElementById("content-heading-val").textContent = content.has_h1 ? "H1 Structure Present" : "Missing H1 Tag";

  const dummyBox = document.getElementById("dummy-signals-container");
  if (content.dummy_signals && content.dummy_signals.length > 0) {
    dummyBox.innerHTML = content.dummy_signals.map(ds => `
      <div class="alert alert-warning bg-warning bg-opacity-10 border-warning text-warning p-2 small mb-2">
        <i class="fa-solid fa-triangle-exclamation me-1"></i> ${ds.label} (${ds.occurrences} instance${ds.occurrences > 1 ? 's' : ''})
      </div>
    `).join("");
  } else {
    dummyBox.innerHTML = '<div class="text-success small"><i class="fa-solid fa-shield-check me-1"></i> No Lorem Ipsum or unedited placeholder strings detected.</div>';
  }

  // TAB 6: Contacts & Identity
  document.getElementById("contact-biz-name").textContent = contacts.business_name || "Unspecified";
  document.getElementById("contact-emails").textContent = (contacts.emails && contacts.emails.length > 0) ? contacts.emails.join(", ") : "No public email detected";
  document.getElementById("contact-phones").textContent = (contacts.phones && contacts.phones.length > 0) ? contacts.phones.join(", ") : "No public telephone detected";
  document.getElementById("contact-address").textContent = contacts.has_address ? (contacts.address_sample || "Detected") : "None detected";

  const socialsBox = document.getElementById("contact-socials");
  if (contacts.social_links && Object.keys(contacts.social_links).length > 0) {
    socialsBox.innerHTML = Object.entries(contacts.social_links).map(([platform, link]) => `
      <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn btn-outline-info btn-sm rounded-pill px-3">
        <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> ${platform}
      </a>
    `).join("");
  } else {
    socialsBox.textContent = "No verified social links detected.";
  }

  // TAB 7: Broken Links
  const linksData = data.broken_links || {};
  document.getElementById("links-summary-badge").textContent = `${linksData.links_checked || 0} Links Sampled (${linksData.broken_count || 0} Broken)`;
  const linksTbody = document.getElementById("broken-links-tbody");
  if (linksData.details && linksData.details.length > 0) {
    linksTbody.innerHTML = linksData.details.map(ld => `
      <tr>
        <td class="text-white-50 small text-truncate" style="max-width: 320px;">${ld.url}</td>
        <td class="text-info small">${ld.status_code}</td>
        <td><span class="badge ${ld.classification === 'Working' ? 'bg-success' : (ld.classification === 'Redirect' ? 'bg-warning text-dark' : 'bg-danger')}">${ld.classification}</span></td>
      </tr>
    `).join("");
  } else {
    linksTbody.innerHTML = '<tr><td colspan="3" class="text-muted small text-center py-3">No crawlable internal routes sampled.</td></tr>';
  }

  // Smooth scroll to results
  dash.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Utility: Set mini card pill text and color
function setSummaryPill(id, text, className) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `summary-val ${className}`;
}

// Animate score counter
function animateScoreCounter(element, target) {
  let current = 0;
  const step = Math.max(1, Math.floor(target / 30));
  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = current;
    }
  }, 30);
}

// Show Alert
function showAlert(message, type = "danger") {
  const alertBox = document.getElementById("alert-box");
  alertBox.className = `alert alert-${type} bg-${type} bg-opacity-20 border-${type} text-white mt-4`;
  alertBox.innerHTML = `<i class="fa-solid fa-circle-exclamation me-2"></i>${message}`;
  alertBox.classList.remove("d-none");
  alertBox.scrollIntoView({ behavior: "smooth" });
}

// Print / PDF Report
function printReport() {
  if (currentScanResult && currentScanResult.id) {
    window.open(`/report/${currentScanResult.id}`, "_blank");
  } else {
    window.print();
  }
}

// History Management
async function openHistoryModal() {
  const modal = new bootstrap.Modal(document.getElementById("historyModal"));
  modal.show();
  await loadHistoryItems();
}

async function loadHistoryItems() {
  const container = document.getElementById("history-items-container");
  try {
    const res = await fetch("/api/history");
    const list = await res.json();

    if (!list || list.length === 0) {
      container.innerHTML = '<div class="text-center text-muted py-4">No scan history recorded yet.</div>';
      return;
    }

    container.innerHTML = list.map(item => `
      <div class="history-item d-flex flex-wrap align-items-center justify-content-between gap-3">
        <div>
          <h6 class="text-white mb-0 fw-bold">${item.domain || item.url}</h6>
          <small class="text-muted">${item.created_at} · Hosting: ${item.hosting || 'Standard'}</small>
        </div>
        <div class="d-flex align-items-center gap-3">
          <div class="text-end">
            <span class="badge ${item.score >= 75 ? 'badge-real' : (item.score >= 45 ? 'badge-verify' : 'badge-demo')}">${item.score}/100</span>
            <div class="small text-white-50" style="font-size: 0.75rem;">${item.classification}</div>
          </div>
          <button class="btn btn-outline-info btn-sm rounded-pill" onclick="viewHistoricalReport(${item.id})">
            <i class="fa-solid fa-eye me-1"></i> View
          </button>
          <button class="btn btn-outline-danger btn-sm rounded-circle" onclick="deleteHistoryItem(${item.id})" title="Delete scan">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = '<div class="text-danger small py-3">Failed to load scan history.</div>';
  }
}

async function viewHistoricalReport(scanId) {
  const modalEl = document.getElementById("historyModal");
  const modalInstance = bootstrap.Modal.getInstance(modalEl);
  if (modalInstance) modalInstance.hide();

  try {
    const res = await fetch(`/api/report/${scanId}`);
    if (!res.ok) throw new Error("Report not found");
    const scan = await res.json();
    currentScanResult = scan.report_data || scan;
    currentScanResult.id = scan.id;
    currentScanResult.created_at = scan.created_at;
    renderResults(currentScanResult);
  } catch (err) {
    showAlert("Unable to load report: " + err.message, "danger");
  }
}

async function deleteHistoryItem(scanId) {
  try {
    await fetch(`/api/history/${scanId}`, { method: "DELETE" });
    await loadHistoryItems();
  } catch (err) {
    console.error("Delete failed:", err);
  }
}

async function clearAllHistory() {
  if (confirm("Are you sure you want to clear all scan history?")) {
    try {
      await fetch("/api/history", { method: "DELETE" });
      await loadHistoryItems();
    } catch (err) {
      console.error("Clear failed:", err);
    }
  }
}
