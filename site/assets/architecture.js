"use strict";

const flows = [
  {
    id: "profile",
    name: "Profile assessment",
    code: "POST /assess/profile",
    summary: "Behavioral profile context becomes a versioned, explainable assessment.",
    steps: [
      {
        lane: "ingress",
        title: "Validated API request",
        short: "Typed profile behavior enters the service.",
        description:
          "Pydantic rejects unknown fields and explicitly blocks protected-attribute, biometric, face, and appearance inputs before any score is calculated.",
        boundary: "FastAPI",
        output: "Validated payload",
        state: "Ephemeral",
      },
      {
        lane: "state",
        title: "Policy snapshot",
        short: "Read enabled rules, weights, and thresholds.",
        description:
          "The service loads one durable policy version. Locked ethical and review boundaries remain visible alongside editable signal controls.",
        boundary: "Service → SQLite",
        output: "Policy version",
        state: "Read only",
      },
      {
        lane: "engine",
        title: "Profile signals",
        short: "Evaluate compound, precision-first rules.",
        description:
          "Sparse profiles, outreach velocity, content reuse, reports, and payment history contribute bounded points only when their documented conditions are met.",
        boundary: "Pure Python",
        output: "Signals + counters",
        state: "No writes",
      },
      {
        lane: "engine",
        title: "Risk tier and explanation",
        short: "Clamp score and separate risk from confidence.",
        description:
          "The engine returns a 0–100 priority score, tier, confidence in available evidence, named point contributions, counter-signals, and limitations.",
        boundary: "Signal engine",
        output: "Assessment",
        state: "No writes",
      },
      {
        lane: "state",
        title: "Durable evidence snapshot",
        short: "Persist exactly what the operator saw.",
        description:
          "SQLite stores the complete response with its policy version. A later policy edit affects new assessments, not this historical explanation.",
        boundary: "Service → SQLite",
        output: "Assessment row",
        state: "Durable",
      },
      {
        lane: "human",
        title: "Conditional review route",
        short: "High scores create work, not punishment.",
        description:
          "At the locked review threshold, the service creates an open case with a priority and evidence snapshot. Low and guarded results create no case.",
        boundary: "Review router",
        output: "Case or standard flow",
        state: "Durable",
      },
    ],
  },
  {
    id: "content",
    name: "Content assessment",
    code: "POST /assess/content",
    summary: "High-precision content and distribution signals remain independently inspectable.",
    steps: [
      {
        lane: "ingress",
        title: "Content contract",
        short: "Receive text plus bounded behavioral context.",
        description:
          "The endpoint accepts message, listing, post, or comment text with account age, repetition, recipient, report, and transaction context.",
        boundary: "FastAPI",
        output: "Validated content",
        state: "Ephemeral",
      },
      {
        lane: "engine",
        title: "Scam intent pattern",
        short: "Require instrument plus requested action.",
        description:
          "A payment word or link alone does not score. Financial solicitation requires a payment instrument paired with an action or a guaranteed-return claim.",
        boundary: "Pure Python",
        output: "Scam signal",
        state: "No writes",
      },
      {
        lane: "engine",
        title: "Malicious pattern check",
        short: "Inspect credential theft and direct threats.",
        description:
          "Credential harvesting requires account-verification context plus a secret or login prompt. Threat patterns are deliberately narrow to avoid ordinary phrases such as “kill the process.”",
        boundary: "Pure Python",
        output: "Malicious signal",
        state: "No writes",
      },
      {
        lane: "engine",
        title: "Distribution context",
        short: "Corroborate repetition, recipients, and reports.",
        description:
          "Spam requires repeated content and multiple recipients. Reports add limited supporting points and cannot establish a violation by themselves.",
        boundary: "Pure Python",
        output: "Behavior signals",
        state: "No writes",
      },
      {
        lane: "state",
        title: "Assessment transaction",
        short: "Write assessment, case, and audit atomically.",
        description:
          "The service stores the assessment and—if required—the review case in one SQLite transaction, then appends linked audit events.",
        boundary: "Service → SQLite",
        output: "Durable records",
        state: "Transactional",
      },
      {
        lane: "human",
        title: "Operator review",
        short: "A person interprets context and records outcome.",
        description:
          "The dashboard exposes the exact evidence and requires an identified reviewer, a valid workflow transition, an outcome, and resolution notes.",
        boundary: "Human review",
        output: "Documented decision",
        state: "Durable",
      },
    ],
  },
  {
    id: "coordination",
    name: "Coordinated abuse",
    code: "POST /assess/coordinated-abuse",
    summary: "Cluster evidence must corroborate; shared infrastructure never stands alone.",
    steps: [
      {
        lane: "ingress",
        title: "Cluster summary",
        short: "Receive aggregate, privacy-minimized measurements.",
        description:
          "The API accepts counts and ratios for participating accounts, account age mix, duplicate content, shared devices, velocity, targets, and reports.",
        boundary: "FastAPI",
        output: "Validated aggregates",
        state: "Ephemeral",
      },
      {
        lane: "engine",
        title: "Similarity evidence",
        short: "Require duplication across multiple accounts.",
        description:
          "Content similarity fires only above the policy threshold and with at least four participating accounts.",
        boundary: "Pure Python",
        output: "Similarity signal",
        state: "No writes",
      },
      {
        lane: "engine",
        title: "Velocity and targeting",
        short: "Check synchronized bursts and concentrated pressure.",
        description:
          "Velocity requires enough events across enough accounts. Target concentration contributes only when independent reports corroborate it.",
        boundary: "Pure Python",
        output: "Coordination signals",
        state: "No writes",
      },
      {
        lane: "engine",
        title: "Infrastructure corroboration",
        short: "Shared devices can support, never trigger.",
        description:
          "A shared-device ratio contributes points only after content similarity or synchronized velocity has independently triggered.",
        boundary: "Pure Python",
        output: "Supporting signal",
        state: "No writes",
      },
      {
        lane: "state",
        title: "Cluster assessment",
        short: "Persist evidence with a policy version.",
        description:
          "The explanation records which independent signals fired, how many points they added, and which limitations an investigator should consider.",
        boundary: "Service → SQLite",
        output: "Assessment snapshot",
        state: "Durable",
      },
      {
        lane: "human",
        title: "Priority investigation",
        short: "Urgent queues still require human judgment.",
        description:
          "Critical clusters receive urgent review priority and a reversible-friction recommendation, never an automatic irreversible action.",
        boundary: "Human review",
        output: "Investigation case",
        state: "Durable",
      },
    ],
  },
  {
    id: "review",
    name: "Human review",
    code: "PATCH /cases/{id}",
    summary: "State transitions make human accountability concrete rather than decorative.",
    steps: [
      {
        lane: "human",
        title: "Prioritized queue",
        short: "Operators see risk, evidence, and age—not a verdict.",
        description:
          "Open cases are ordered by urgent, high, then standard priority. The queue preserves the assessment’s original evidence snapshot.",
        boundary: "Dashboard → API",
        output: "Open case",
        state: "Read only",
      },
      {
        lane: "human",
        title: "Named claim",
        short: "Open becomes in review with a reviewer.",
        description:
          "Claiming a case requires a reviewer name. The transaction records assignment and review start time and appends an audit event.",
        boundary: "Review API",
        output: "In-review case",
        state: "Durable",
      },
      {
        lane: "state",
        title: "Immutable evidence",
        short: "Review cannot edit score or signal history.",
        description:
          "The review endpoint permits workflow fields only. It cannot rewrite the assessment, score, policy version, or evidence attached to the case.",
        boundary: "SQLite schema",
        output: "Evidence snapshot",
        state: "Immutable via API",
      },
      {
        lane: "human",
        title: "Documented outcome",
        short: "Resolve with outcome and meaningful notes.",
        description:
          "A case must be in review before resolution. Confirmed abuse, false positive, insufficient evidence, and no action are explicit outcomes.",
        boundary: "Review API",
        output: "Resolved case",
        state: "Terminal",
      },
      {
        lane: "state",
        title: "Hash-linked audit",
        short: "Append canonical event to the chain.",
        description:
          "Each event includes the previous event hash. Reads recompute the entire SHA-256 chain and surface whether it remains valid.",
        boundary: "Audit store",
        output: "Verified event",
        state: "Append only in API",
      },
      {
        lane: "state",
        title: "Operational feedback",
        short: "Outcomes update metrics, not hidden training.",
        description:
          "The dashboard reports review outcomes and false-positive rate. This starter does not silently retrain or mutate policy from reviewer decisions.",
        boundary: "Metrics query",
        output: "Transparent KPI",
        state: "Derived",
      },
    ],
  },
];

let activeFlowIndex = 0;
let activeStepIndex = 0;
let timer = null;

function activeFlow() {
  return flows[activeFlowIndex];
}

function renderTabs() {
  const container = document.querySelector("#architectureTabs");
  container.innerHTML = "";
  flows.forEach((flow, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `architecture-tab ${index === activeFlowIndex ? "active" : ""}`;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(index === activeFlowIndex));
    button.innerHTML = `<strong>${flow.name}</strong><span>${flow.code}</span>`;
    button.addEventListener("click", () => {
      stopPlayback();
      activeFlowIndex = index;
      activeStepIndex = 0;
      render();
    });
    container.append(button);
  });
}

function renderFlow() {
  const flow = activeFlow();
  document.querySelector("#flowTitle").textContent = flow.name;
  document.querySelector("#flowSummary").textContent = flow.summary;
  const track = document.querySelector("#flowTrack");
  track.innerHTML = "";
  flow.steps.forEach((step, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "flow-node";
    if (index < activeStepIndex) button.classList.add("complete");
    if (index === activeStepIndex) button.classList.add("active");
    button.innerHTML =
      `<span class="lane ${step.lane}">${step.lane}</span>` +
      `<strong>${step.title}</strong><span>${step.short}</span>`;
    button.addEventListener("click", () => {
      stopPlayback();
      activeStepIndex = index;
      renderFlow();
      renderDetail();
    });
    track.append(button);
    if (index < flow.steps.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = `flow-arrow ${index === activeStepIndex ? "active" : ""}`;
      arrow.setAttribute("aria-hidden", "true");
      track.append(arrow);
    }
  });
  track.querySelector(".flow-node.active")?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
    inline: "center",
  });
}

function renderDetail() {
  const step = activeFlow().steps[activeStepIndex];
  document.querySelector("#stepLabel").textContent =
    `Step ${activeStepIndex + 1} of ${activeFlow().steps.length}`;
  document.querySelector("#stepTitle").textContent = step.title;
  document.querySelector("#stepDescription").textContent = step.description;
  document.querySelector("#stepBoundary").textContent = step.boundary;
  document.querySelector("#stepOutput").textContent = step.output;
  document.querySelector("#stepState").textContent = step.state;
  document.querySelector("#flowPrevious").disabled = activeStepIndex === 0;
  document.querySelector("#flowNext").disabled =
    activeStepIndex === activeFlow().steps.length - 1;
}

function render() {
  renderTabs();
  renderFlow();
  renderDetail();
}

function nextStep() {
  if (activeStepIndex < activeFlow().steps.length - 1) {
    activeStepIndex += 1;
    renderFlow();
    renderDetail();
    return true;
  }
  return false;
}

function previousStep() {
  if (activeStepIndex > 0) {
    activeStepIndex -= 1;
    renderFlow();
    renderDetail();
  }
}

function startPlayback() {
  if (timer) return;
  document.querySelector("#flowPlay").textContent = "Ⅱ";
  document.querySelector("#flowPlay").setAttribute("aria-label", "Pause scenario");
  if (activeStepIndex === activeFlow().steps.length - 1) {
    activeStepIndex = 0;
    renderFlow();
    renderDetail();
  }
  timer = window.setInterval(() => {
    if (!nextStep()) stopPlayback();
  }, 1450);
}

function stopPlayback() {
  if (timer) window.clearInterval(timer);
  timer = null;
  const button = document.querySelector("#flowPlay");
  button.textContent = "▶";
  button.setAttribute("aria-label", "Play scenario");
}

function setupNavigation() {
  const button = document.querySelector("#mobileMenu");
  const links = document.querySelector("#navLinks");
  button?.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
}

async function detectLocalApp() {
  try {
    const response = await fetch("api/v1/health", { cache: "no-store" });
    if (!response.ok) throw new Error("static");
  } catch {
    document.querySelectorAll(".local-only-link").forEach((link) => {
      link.href = link.dataset.staticHref;
      link.textContent = link.dataset.staticLabel;
    });
  }
}

document.querySelector("#flowPrevious").addEventListener("click", () => {
  stopPlayback();
  previousStep();
});
document.querySelector("#flowNext").addEventListener("click", () => {
  stopPlayback();
  nextStep();
});
document.querySelector("#flowPlay").addEventListener("click", () => {
  if (timer) stopPlayback();
  else startPlayback();
});

setupNavigation();
detectLocalApp();
render();
