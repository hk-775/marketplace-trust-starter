"use strict";

const feedItems = [
  {
    score: 0,
    tier: "low",
    title: "Established local seller",
    detail: "Positive history · no rule fired",
  },
  {
    score: 40,
    tier: "guarded",
    title: "Repeated listing burst",
    detail: "2 explainable spam signals",
  },
  {
    score: 56,
    tier: "high",
    title: "Gift-card solicitation",
    detail: "Human review case created",
  },
  {
    score: 100,
    tier: "critical",
    title: "Coordinated target burst",
    detail: "5 corroborating signals",
  },
  {
    score: 12,
    tier: "low",
    title: "Sparse new profile",
    detail: "Weak signal stays below review",
  },
  {
    score: 58,
    tier: "high",
    title: "Credential-harvesting pattern",
    detail: "Review required · no auto action",
  },
];

let feedOffset = 0;

function assessmentCard(item) {
  const card = document.createElement("article");
  card.className = "assessment-card";

  const score = document.createElement("span");
  score.className = `score-orb ${item.tier}`;
  score.textContent = String(item.score);

  const meta = document.createElement("div");
  meta.className = "assessment-meta";
  const title = document.createElement("strong");
  title.textContent = item.title;
  const detail = document.createElement("span");
  detail.textContent = item.detail;
  meta.append(title, detail);

  const tier = document.createElement("span");
  tier.className = "tier-chip";
  tier.textContent = item.tier;

  card.append(score, meta, tier);
  return card;
}

function renderFeed(animate = false) {
  const feed = document.querySelector("#liveFeed");
  if (!feed) return;
  const visible = Array.from({ length: 4 }, (_, index) => {
    return feedItems[(feedOffset + index) % feedItems.length];
  });
  feed.replaceChildren(...visible.map(assessmentCard));
  if (animate) {
    const last = feed.lastElementChild;
    last?.classList.add("entering");
    requestAnimationFrame(() => last?.classList.remove("entering"));
  }
}

function setupNavigation() {
  const button = document.querySelector("#mobileMenu");
  const links = document.querySelector("#navLinks");
  if (!button || !links) return;
  button.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("open");
      button.setAttribute("aria-expanded", "false");
    });
  });
}

function setupReveals() {
  const elements = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    elements.forEach((element) => element.classList.add("visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 },
  );
  elements.forEach((element) => observer.observe(element));
}

function setupCounters() {
  const counters = document.querySelectorAll("[data-counter]");
  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const element = entry.target;
        const target = Number(element.dataset.counter || "0");
        const startedAt = performance.now();
        const duration = 850;
        const tick = (now) => {
          const progress = Math.min((now - startedAt) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          element.textContent = String(Math.round(target * eased));
          if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
        observer.unobserve(element);
      });
    },
    { threshold: 0.5 },
  );
  counters.forEach((counter) => observer.observe(counter));
}

async function detectLocalApp() {
  try {
    const response = await fetch("api/v1/health", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error("not local");
  } catch {
    document.querySelectorAll(".local-only-link").forEach((link) => {
      if (link.dataset.staticHref) link.setAttribute("href", link.dataset.staticHref);
      if (link.dataset.staticLabel) link.textContent = link.dataset.staticLabel;
    });
  }
}

renderFeed();
setupNavigation();
setupReveals();
setupCounters();
detectLocalApp();

window.setInterval(() => {
  feedOffset = (feedOffset + 1) % feedItems.length;
  renderFeed(true);
}, 2800);
