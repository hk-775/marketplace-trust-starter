"use strict";

const runtimeMode =
  document.querySelector('meta[name="mts-runtime"]')?.content || "service";

const state = {
  metrics: null,
  assessments: [],
  cases: [],
  policies: [],
  insights: null,
  audit: null,
  scenarios: [],
  caseFilter: "active",
  policyFilter: "all",
  currentView: "overview",
  staticMode: runtimeMode === "static",
};

const viewTitles = {
  overview: "Overview",
  assessments: "Live assessments",
  cases: "Review queue",
  policies: "Policy controls",
  insights: "Signal insights",
  audit: "Audit trail",
  demo: "Guided demo",
};

const assessmentPresets = {
  profile: {
    subject_id: "lab-profile-001",
    bio: "New maker account for weekend market listings.",
    account_age_days: 2,
    profile_completeness: 0.3,
    verified_contact: true,
    media_count: 2,
    outbound_messages_1h: 4,
    unique_recipients_1h: 3,
    bio_reuse_count_7d: 0,
    linked_accounts_30d: 0,
    prior_reports_30d: 0,
    successful_transactions_90d: 0,
    chargebacks_90d: 0,
  },
  content: {
    subject_id: "lab-content-001",
    content_id: "lab-message-001",
    content_type: "message",
    text: "Your order is ready for pickup at the community desk.",
    account_age_days: 120,
    previous_similar_posts_1h: 0,
    unique_recipients_1h: 1,
    reports_24h: 0,
    successful_transactions_90d: 8,
  },
  "coordinated-abuse": {
    cluster_id: "lab-cluster-001",
    participating_accounts: 8,
    new_account_ratio: 0.75,
    duplicate_content_ratio: 0.8,
    shared_device_ratio: 0.65,
    events_10m: 110,
    target_concentration: 0.7,
    independent_reports: 4,
    established_account_ratio: 0.1,
  },
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function titleize(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatPercent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatError(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => `${item.loc?.slice(1).join(".") || "request"}: ${item.msg}`)
      .join("; ");
  }
  if (typeof detail === "string") return detail;
  return "Request failed";
}

async function api(path, options = {}) {
  const request = {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  };
  const response = await fetch(path, request);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(formatError(payload.detail || payload.error || response.statusText));
  }
  return payload;
}

function showToast(message, type = "success") {
  const region = document.querySelector("#toastRegion");
  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "error" : ""}`;
  toast.textContent = message;
  region.append(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

function setView(view) {
  if (!viewTitles[view]) return;
  state.currentView = view;
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === view);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelector("#topbarTitle").textContent = viewTitles[view];
  const sidebar = document.querySelector("#dashboardSidebar");
  const sidebarToggle = document.querySelector("#sidebarToggle");
  sidebar.classList.remove("open");
  sidebarToggle?.setAttribute("aria-expanded", "false");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadAll({ silent = false } = {}) {
  if (state.staticMode) {
    try {
      const response = await fetch("assets/demo-data.json", { cache: "no-store" });
      if (!response.ok) throw new Error("static snapshot unavailable");
      const snapshot = await response.json();
      state.metrics = snapshot.metrics;
      state.assessments = snapshot.assessments.items;
      state.cases = snapshot.cases.items;
      state.policies = snapshot.policies;
      state.insights = snapshot.insights;
      state.audit = snapshot.audit;
      state.scenarios = snapshot.scenarios.items;
      document.querySelector(".environment-pill").textContent = "Static preview";
      document.querySelector(".local-mode").textContent =
        "Static seeded preview · run locally to mutate";
      document.querySelectorAll('a[href="api/docs"]').forEach((link) => {
        link.href = "index.html#quickstart";
        link.textContent = "Run the local API";
      });
      renderAll();
      return;
    } catch (error) {
      if (!silent) showToast(error.message, "error");
      document.querySelectorAll(".loading-state").forEach((element) => {
        element.className = "error-state";
        element.textContent = `Unable to load static snapshot: ${error.message}`;
      });
      return;
    }
  }
  try {
    const [metrics, assessments, cases, policies, insights, audit, scenarios] =
      await Promise.all([
        api("api/v1/metrics"),
        api("api/v1/assessments?limit=250"),
        api("api/v1/cases?limit=250"),
        api("api/v1/policies"),
        api("api/v1/insights"),
        api("api/v1/audit?limit=250"),
        api("api/v1/demo/scenarios"),
      ]);
    state.metrics = metrics;
    state.assessments = assessments.items;
    state.cases = cases.items;
    state.policies = policies;
    state.insights = insights;
    state.audit = audit;
    state.scenarios = scenarios.items;
    renderAll();
  } catch (error) {
    if (!silent) showToast(error.message, "error");
    document.querySelectorAll(".loading-state").forEach((element) => {
      element.className = "error-state";
      element.textContent = `Unable to load local API: ${error.message}`;
    });
  }
}

function requireLiveDemo() {
  if (!state.staticMode) return true;
  showToast("This is a read-only static preview. Run ./scripts/demo.sh for live controls.", "error");
  return false;
}

function renderAll() {
  renderOverview();
  renderAssessments();
  renderCases();
  renderPolicies();
  renderInsights();
  renderAudit();
  renderScenarios();
}

function animateNumber(element, target, suffix = "") {
  if (!element) return;
  const start = Number.parseFloat(element.textContent) || 0;
  const startedAt = performance.now();
  const duration = 380;
  const tick = (now) => {
    const progress = Math.min((now - startedAt) / duration, 1);
    const current = start + (target - start) * (1 - Math.pow(1 - progress, 3));
    element.textContent = `${Math.round(current)}${suffix}`;
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function assessmentRow(assessment, compact = false) {
  const evidence = assessment.signals.length
    ? assessment.signals
        .slice(0, compact ? 1 : 2)
        .map((signal) => signal.label)
        .join(", ")
    : "No risk rule fired";
  return `
    <tr>
      <td class="subject-cell">
        <strong>${escapeHtml(assessment.assessment_id)}</strong>
        <span>${escapeHtml(formatTime(assessment.created_at))}</span>
      </td>
      <td class="mono">${escapeHtml(assessment.subject_id)}</td>
      <td><span class="category-badge">${escapeHtml(titleize(assessment.assessment_type))}</span></td>
      <td>${escapeHtml(evidence)}</td>
      <td><span class="risk-badge ${escapeHtml(assessment.risk_tier)}">${escapeHtml(assessment.risk_tier)}</span></td>
      <td class="score-cell">${escapeHtml(assessment.risk_score)}</td>
      <td>${
        assessment.case_id
          ? `<span class="mono">${escapeHtml(assessment.case_id)}</span>`
          : "<span class=\"category-badge\">not queued</span>"
      }</td>
    </tr>
  `;
}

function renderOverview() {
  if (!state.metrics) return;
  const kpis = state.metrics.kpis;
  animateNumber(document.querySelector("#kpiAssessments"), kpis.total_assessments);
  animateNumber(document.querySelector("#kpiQueue"), kpis.review_queue);
  animateNumber(
    document.querySelector("#kpiHighRate"),
    Math.round(kpis.high_or_critical_rate * 100),
    "%",
  );
  animateNumber(document.querySelector("#kpiMedian"), kpis.median_risk_score);
  document.querySelector("#policyVersionLabel").textContent =
    `policy v${state.metrics.policy_version}`;

  const distribution = state.metrics.tier_distribution;
  const max = Math.max(1, ...Object.values(distribution));
  document.querySelector("#tierDistribution").innerHTML = Object.entries(distribution)
    .map(
      ([tier, count]) => `
        <div class="distribution-row">
          <span>${escapeHtml(tier)}</span>
          <div class="bar-track"><div class="bar-fill ${escapeHtml(tier)}" style="width:${Math.max(
            2,
            (count / max) * 100,
          )}%"></div></div>
          <strong>${escapeHtml(count)}</strong>
        </div>
      `,
    )
    .join("");

  const activeCases = state.cases
    .filter((item) => item.status !== "resolved")
    .slice(0, 4);
  document.querySelector("#queuePreview").innerHTML = activeCases.length
    ? activeCases
        .map(
          (item) => `
            <div class="case-mini">
              <span class="case-priority-dot ${escapeHtml(item.priority)}"></span>
              <div>
                <strong>${escapeHtml(item.case_id)} · ${escapeHtml(item.subject_id)}</strong>
                <span>${escapeHtml(titleize(item.assessment_type))} · ${escapeHtml(item.status)}</span>
              </div>
              <strong class="mono">${escapeHtml(item.risk_score)}</strong>
            </div>
          `,
        )
        .join("")
    : '<div class="empty-state">The review queue is clear.</div>';

  document.querySelector("#overviewAssessmentRows").innerHTML = state.assessments
    .slice(0, 6)
    .map((item) => assessmentRow(item, true))
    .join("");
}

function renderAssessments() {
  const rows = document.querySelector("#assessmentRows");
  if (!state.assessments.length) {
    rows.innerHTML = '<tr><td colspan="7"><div class="empty-state">No assessments yet.</div></td></tr>';
    return;
  }
  rows.innerHTML = state.assessments.map((item) => assessmentRow(item)).join("");
}

function caseMatchesFilter(item) {
  if (state.caseFilter === "all") return true;
  if (state.caseFilter === "active") return item.status !== "resolved";
  return item.status === state.caseFilter;
}

function renderCases() {
  const visible = state.cases.filter(caseMatchesFilter);
  document.querySelectorAll("[data-case-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.caseFilter === state.caseFilter);
  });
  const grid = document.querySelector("#caseGrid");
  if (!visible.length) {
    grid.innerHTML = '<div class="empty-state">No cases match this filter.</div>';
    return;
  }
  grid.innerHTML = visible
    .map((item) => {
      const evidence = item.evidence
        .slice(0, 4)
        .map((signal) => `<span class="evidence-chip">${escapeHtml(signal.label)} +${escapeHtml(signal.points)}</span>`)
        .join("");
      let action = "";
      if (item.status === "open") {
        action = `<button class="button primary small" type="button" data-case-action="start" data-case-id="${escapeHtml(item.case_id)}">Start review</button>`;
      } else if (item.status === "in_review") {
        action = `<button class="button primary small" type="button" data-case-action="resolve" data-case-id="${escapeHtml(item.case_id)}">Resolve case</button>`;
      } else {
        action = `<span class="category-badge">${escapeHtml(titleize(item.outcome || "resolved"))}</span>`;
      }
      return `
        <article class="case-card">
          <div class="case-card-head">
            <div>
              <span class="status-badge ${escapeHtml(item.status)}">${escapeHtml(titleize(item.status))}</span>
              <h3>${escapeHtml(item.case_id)} · ${escapeHtml(item.subject_id)}</h3>
              <p>${escapeHtml(item.summary)}</p>
            </div>
            <span class="case-score">${escapeHtml(item.risk_score)}</span>
          </div>
          <div class="evidence-list">${evidence}</div>
          <div class="case-card-footer">
            <small>${escapeHtml(item.assigned_to || `${titleize(item.priority)} priority · unassigned`)}</small>
            ${action}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderPolicies() {
  if (!state.metrics) return;
  document.querySelector("#policyVersionBadge").textContent =
    `Policy version ${state.metrics.policy_version}`;

  const categories = ["all", ...new Set(state.policies.map((policy) => policy.category))];
  document.querySelector("#policyFilters").innerHTML = categories
    .map(
      (category) => `
        <button class="filter-button ${category === state.policyFilter ? "active" : ""}"
          type="button" data-policy-filter="${escapeHtml(category)}">
          ${escapeHtml(titleize(category))}
        </button>
      `,
    )
    .join("");

  const visible = state.policies.filter(
    (policy) => state.policyFilter === "all" || policy.category === state.policyFilter,
  );
  document.querySelector("#policyGrid").innerHTML = visible
    .map(
      (policy) => `
        <article class="policy-card">
          <div class="policy-card-head">
            <div>
              <span class="category-badge">${escapeHtml(titleize(policy.category))}</span>
              <h3>${escapeHtml(policy.name)}</h3>
            </div>
            <span class="toggle ${policy.enabled ? "on" : ""}" role="img"
              aria-label="${policy.enabled ? "Enabled" : "Disabled"}"></span>
          </div>
          <p>${escapeHtml(policy.description)}</p>
          <div class="policy-value-row">
            <div class="policy-value"><span>Weight</span><strong>${escapeHtml(policy.weight.toFixed(2))}×</strong></div>
            <div class="policy-value"><span>Threshold</span><strong>${escapeHtml(policy.threshold)}</strong></div>
            <div class="policy-value"><span>Rule version</span><strong>v${escapeHtml(policy.version)}</strong></div>
          </div>
          <div class="policy-card-footer">
            ${
              policy.editable
                ? `<small>Changed ${escapeHtml(formatTime(policy.updated_at))}</small>
                   <button class="button small" type="button" data-policy-edit="${escapeHtml(policy.policy_id)}">Edit rule</button>`
                : `<span class="lock-note">◆ Locked safety boundary</span>`
            }
          </div>
        </article>
      `,
    )
    .join("");
}

function renderInsights() {
  if (!state.insights) return;
  const engine = state.insights.engine;
  document.querySelector("#engineSummary").textContent =
    `${titleize(engine.type)} · ${engine.external_models} external models · ` +
    `${engine.network_calls} network calls · policy version ${engine.policy_version}.`;

  const signals = state.insights.top_signals;
  const maxHits = Math.max(1, ...signals.map((signal) => signal.hits));
  document.querySelector("#signalList").innerHTML = signals.length
    ? signals
        .map(
          (signal) => `
            <div class="signal-row">
              <div>
                <strong>${escapeHtml(signal.name)}</strong>
                <span>${escapeHtml(titleize(signal.category))}</span>
              </div>
              <div class="bar-track"><div class="bar-fill" style="width:${Math.max(
                2,
                (signal.hits / maxHits) * 100,
              )}%"></div></div>
              <strong>${escapeHtml(signal.hits)} hits</strong>
            </div>
          `,
        )
        .join("")
    : '<div class="empty-state">No risk signals have fired.</div>';

  document.querySelector("#safeguardList").innerHTML = state.insights.safeguards
    .map(
      (item) => `
        <div class="safeguard-item">
          <span class="safeguard-check">✓</span>
          <span>${escapeHtml(item)}</span>
        </div>
      `,
    )
    .join("");
}

function renderAudit() {
  if (!state.audit) return;
  const status = document.querySelector("#auditChainStatus");
  status.textContent = state.audit.chain_valid
    ? `Chain verified · ${state.audit.total} events`
    : "Chain verification failed";
  status.classList.toggle("invalid", !state.audit.chain_valid);

  document.querySelector("#auditTimeline").innerHTML = state.audit.items
    .map(
      (event) => `
        <div class="audit-event">
          <span class="audit-time">${escapeHtml(formatTime(event.timestamp))}</span>
          <span class="audit-node"></span>
          <div class="audit-copy">
            <strong>${escapeHtml(titleize(event.action))} · ${escapeHtml(event.entity_id)}</strong>
            <span>${escapeHtml(event.actor)} · ${escapeHtml(titleize(event.entity_type))}</span>
          </div>
          <span class="audit-hash" title="${escapeHtml(event.event_hash)}">${escapeHtml(event.event_hash.slice(0, 16))}…</span>
        </div>
      `,
    )
    .join("");
}

function renderScenarios() {
  const grid = document.querySelector("#scenarioGrid");
  grid.innerHTML = state.scenarios
    .map(
      (scenario) => `
        <article class="scenario-card">
          <div class="scenario-meta">
            <span class="category-badge">${escapeHtml(titleize(scenario.assessment_type))}</span>
            <span class="risk-badge ${escapeHtml(scenario.expected)}">${escapeHtml(scenario.expected)}</span>
          </div>
          <h3>${escapeHtml(scenario.name)}</h3>
          <p>${escapeHtml(scenario.description)}</p>
          <div class="case-card-footer">
            <small>Creates a new durable assessment</small>
            <button class="button primary small" type="button"
              data-run-scenario="${escapeHtml(scenario.scenario_id)}">Run scenario</button>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderScenarioResult(result) {
  const signals = result.signals
    .map(
      (signal) =>
        `<span class="evidence-chip">${escapeHtml(signal.label)} +${escapeHtml(signal.points)}</span>`,
    )
    .join("");
  document.querySelector("#scenarioResult").innerHTML = `
    <article class="scenario-result">
      <div class="result-score">
        <span class="result-score-orb">${escapeHtml(result.risk_score)}</span>
        <div>
          <span class="risk-badge ${escapeHtml(result.risk_tier)}">${escapeHtml(result.risk_tier)}</span>
          <h3>${escapeHtml(result.summary)}</h3>
          <p>${escapeHtml(result.recommended_action)}${
            result.case_id ? ` · case ${escapeHtml(result.case_id)} created` : ""
          }</p>
        </div>
      </div>
      <div class="evidence-list">${signals || '<span class="evidence-chip">No risk rule fired</span>'}</div>
    </article>
  `;
}

function openAssessmentDialog() {
  if (!requireLiveDemo()) return;
  const type = document.querySelector("#assessmentType").value;
  document.querySelector("#assessmentPayload").value = JSON.stringify(
    assessmentPresets[type],
    null,
    2,
  );
  document.querySelector("#assessmentDialog").showModal();
}

function openReviewDialog(caseId, action) {
  if (!requireLiveDemo()) return;
  const reviewCase = state.cases.find((item) => item.case_id === caseId);
  if (!reviewCase) return;
  const resolving = action === "resolve";
  document.querySelector("#reviewCaseId").value = caseId;
  document.querySelector("#reviewTargetStatus").value = resolving ? "resolved" : "in_review";
  document.querySelector("#reviewDialogTitle").textContent = resolving
    ? `Resolve ${caseId}`
    : `Start review · ${caseId}`;
  document.querySelector("#reviewDialogSubtitle").textContent =
    `${reviewCase.risk_score} ${reviewCase.risk_tier} · ${reviewCase.subject_id}`;
  document.querySelector("#reviewerName").value = reviewCase.assigned_to || "Demo Operator";
  document.querySelector("#reviewOutcomeField").hidden = !resolving;
  document.querySelector("#reviewNotesField").hidden = !resolving;
  document.querySelector("#reviewNotes").required = resolving;
  document.querySelector("#reviewSubmit").textContent = resolving ? "Resolve case" : "Start review";
  document.querySelector("#reviewDialog").showModal();
}

function openPolicyDialog(policyId) {
  if (!requireLiveDemo()) return;
  const policy = state.policies.find((item) => item.policy_id === policyId);
  if (!policy || !policy.editable) return;
  document.querySelector("#policyId").value = policy.policy_id;
  document.querySelector("#policyDialogTitle").textContent = policy.name;
  document.querySelector("#policyEnabled").value = String(policy.enabled);
  document.querySelector("#policyWeight").value = policy.weight;
  document.querySelector("#policyThreshold").value = policy.threshold;
  document.querySelector("#policyReason").value = "";
  document.querySelector("#policyDialog").showModal();
}

function closeDialog(button) {
  button.closest("dialog")?.close();
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

document.querySelectorAll("[data-view-jump]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.viewJump));
});

document.querySelectorAll("[data-open-assessment]").forEach((button) => {
  button.addEventListener("click", openAssessmentDialog);
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", () => closeDialog(button));
});

document.querySelector("#sidebarToggle")?.addEventListener("click", () => {
  const sidebar = document.querySelector("#dashboardSidebar");
  const open = sidebar.classList.toggle("open");
  document.querySelector("#sidebarToggle").setAttribute("aria-expanded", String(open));
});

document.querySelector("#assessmentType").addEventListener("change", (event) => {
  document.querySelector("#assessmentPayload").value = JSON.stringify(
    assessmentPresets[event.target.value],
    null,
    2,
  );
});

document.querySelector("#assessmentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const type = document.querySelector("#assessmentType").value;
  try {
    const payload = JSON.parse(document.querySelector("#assessmentPayload").value);
    const result = await api(`api/v1/assess/${type}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    document.querySelector("#assessmentDialog").close();
    showToast(
      `Assessment ${result.assessment_id}: ${result.risk_score} ${result.risk_tier}${
        result.case_id ? ` · case ${result.case_id}` : ""
      }`,
    );
    await loadAll({ silent: true });
    setView("assessments");
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.querySelector("#reviewForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const caseId = document.querySelector("#reviewCaseId").value;
  const targetStatus = document.querySelector("#reviewTargetStatus").value;
  const body = {
    status: targetStatus,
    reviewer: document.querySelector("#reviewerName").value,
  };
  if (targetStatus === "resolved") {
    body.outcome = document.querySelector("#reviewOutcome").value;
    body.resolution_notes = document.querySelector("#reviewNotes").value;
  }
  try {
    await api(`api/v1/cases/${encodeURIComponent(caseId)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    document.querySelector("#reviewDialog").close();
    showToast(targetStatus === "resolved" ? `${caseId} resolved` : `${caseId} claimed`);
    await loadAll({ silent: true });
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.querySelector("#policyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const policyId = document.querySelector("#policyId").value;
  const body = {
    enabled: document.querySelector("#policyEnabled").value === "true",
    weight: Number(document.querySelector("#policyWeight").value),
    threshold: Number(document.querySelector("#policyThreshold").value),
    actor: document.querySelector("#policyActor").value,
    reason: document.querySelector("#policyReason").value,
  };
  try {
    await api(`api/v1/policies/${encodeURIComponent(policyId)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    document.querySelector("#policyDialog").close();
    showToast(`${policyId} updated for new assessments`);
    await loadAll({ silent: true });
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.querySelector("#resetButton").addEventListener("click", () => {
  if (!requireLiveDemo()) return;
  document.querySelector("#resetConfirmation").value = "";
  document.querySelector("#resetDialog").showModal();
});

document.querySelector("#resetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const confirmation = document.querySelector("#resetConfirmation").value;
  if (confirmation !== "RESET DEMO") {
    showToast("Type RESET DEMO exactly to reset local state.", "error");
    return;
  }
  try {
    const result = await api("api/v1/demo/reset", {
      method: "POST",
      body: JSON.stringify({
        actor: document.querySelector("#resetActor").value,
        confirmation,
      }),
    });
    document.querySelector("#resetDialog").close();
    document.querySelector("#scenarioResult").replaceChildren();
    showToast(
      `Reset complete: ${result.assessments} assessments and ${result.cases} cases restored`,
    );
    await loadAll({ silent: true });
    setView("overview");
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.addEventListener("click", async (event) => {
  const caseButton = event.target.closest("[data-case-action]");
  if (caseButton) {
    openReviewDialog(caseButton.dataset.caseId, caseButton.dataset.caseAction);
    return;
  }

  const policyButton = event.target.closest("[data-policy-edit]");
  if (policyButton) {
    openPolicyDialog(policyButton.dataset.policyEdit);
    return;
  }

  const caseFilter = event.target.closest("[data-case-filter]");
  if (caseFilter) {
    state.caseFilter = caseFilter.dataset.caseFilter;
    renderCases();
    return;
  }

  const policyFilter = event.target.closest("[data-policy-filter]");
  if (policyFilter) {
    state.policyFilter = policyFilter.dataset.policyFilter;
    renderPolicies();
    return;
  }

  const scenarioButton = event.target.closest("[data-run-scenario]");
  if (scenarioButton) {
    if (!requireLiveDemo()) return;
    scenarioButton.disabled = true;
    scenarioButton.textContent = "Running…";
    try {
      const result = await api(
        `api/v1/demo/scenarios/${encodeURIComponent(scenarioButton.dataset.runScenario)}`,
        { method: "POST" },
      );
      renderScenarioResult(result);
      showToast(
        `${result.risk_score} ${result.risk_tier}${
          result.case_id ? ` · case ${result.case_id} queued` : ""
        }`,
      );
      await loadAll({ silent: true });
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      scenarioButton.disabled = false;
      scenarioButton.textContent = "Run scenario";
    }
  }
});

loadAll();
window.setInterval(() => {
  if (!state.staticMode) loadAll({ silent: true });
}, 15000);
