const form = document.querySelector("#investigation-form");
const questionInput = document.querySelector("#question");
const submitButton = document.querySelector("#submit-button");
const loadingCard = document.querySelector("#loading-card");
const results = document.querySelector("#results");
const errorBanner = document.querySelector("#error-banner");

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question || "";
    questionInput.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  errorBanner.hidden = true;
  results.hidden = true;
  loadingCard.hidden = false;
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/investigate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The investigation could not be completed.");
    renderResults(payload);
  } catch (error) {
    errorBanner.textContent = error instanceof Error ? error.message : "Unable to reach the ARGUS server.";
    errorBanner.hidden = false;
  } finally {
    loadingCard.hidden = true;
    submitButton.disabled = false;
  }
});

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function value(value, fallback = "Not available") {
  return value === undefined || value === null || value === "" ? fallback : value;
}

function addScoreCard(container, label, score, suffix = "", primary = false, level = "") {
  const card = element("div", `score-card${primary ? " primary-score" : ""}`);
  card.append(element("div", "score-label", label));
  const scoreLine = element("div", "score-value");
  scoreLine.append(document.createTextNode(`${score}${suffix}`));
  if (level) scoreLine.append(element("span", "score-level", level));
  card.append(scoreLine);
  container.append(card);
}

function addDimension(container, label, rawScore) {
  const score = Number(rawScore);
  const dimension = element("div", "dimension");
  const heading = element("div", "dimension-head");
  heading.append(element("span", "", label));
  heading.append(element("strong", "", `${Number.isFinite(score) ? score.toFixed(1) : "—"} / 10`));
  const meter = element("div", "meter");
  const fill = element("span");
  fill.style.width = `${Math.max(0, Math.min(100, score * 10))}%`;
  meter.append(fill);
  dimension.append(heading, meter);
  container.append(dimension);
}

function addEmpty(container, message) {
  container.append(element("div", "empty-note", message));
}

function renderResults(data) {
  const scores = data.scores || {};
  const scoreGrid = document.querySelector("#score-grid");
  scoreGrid.replaceChildren();
  const risk = Number(scores.risk || 0);
  const riskText = Number.isFinite(risk) ? risk.toFixed(2) : "—";
  addScoreCard(scoreGrid, "OVERALL RISK", riskText, " / 10", true, value(scores.risk_level, "unknown"));
  addScoreCard(scoreGrid, "ASSESSMENT CONFIDENCE", `${Math.round(Number(scores.confidence || 0) * 100)}%`);
  addScoreCard(scoreGrid, "EVIDENCE QUALITY", `${Math.round(Number(scores.evidence_quality || 0) * 100)}%`);
  addScoreCard(scoreGrid, "RESEARCH CYCLES", value(data.iterations, 0));

  const gate = document.querySelector("#gate-badge");
  gate.textContent = value(data.gate, "Completed").replaceAll("_", " ");
  document.querySelector("#report-text").textContent = value(data.report, "ARGUS did not return a report.");
  document.querySelector("#formula-text").textContent = value(scores.formula);

  const dimensions = document.querySelector("#dimensions-list");
  dimensions.replaceChildren();
  addDimension(dimensions, "Impact", scores.impact);
  addDimension(dimensions, "Probability", scores.probability);
  addDimension(dimensions, "Urgency", scores.urgency);

  const actions = document.querySelector("#actions-list");
  actions.replaceChildren();
  document.querySelector("#action-count").textContent = `${(data.actions || []).length} ACTIONS`;
  for (const action of data.actions || []) {
    const card = element("article", "item-card");
    const top = element("div", "item-top");
    top.append(element("div", "item-title", value(action.action, "Action")));
    top.append(element("span", "item-meta", value(action.owner, "Team")));
    card.append(top);
    card.append(element("p", "item-copy", value(action.rationale, "")));
    const tags = element("div", "item-tags");
    tags.append(element("span", "tag", `Priority ${value(action.priority, "—")}`));
    tags.append(element("span", action.requires_human_approval ? "tag warning" : "tag",
      action.requires_human_approval ? "Human approval required" : "No approval flagged"));
    if ((action.evidence_ids || []).length) tags.append(element("span", "tag", `Sources: ${action.evidence_ids.join(", ")}`));
    card.append(tags);
    actions.append(card);
  }
  if (!actions.children.length) addEmpty(actions, "No actions were returned.");

  const evidence = document.querySelector("#evidence-list");
  evidence.replaceChildren();
  document.querySelector("#evidence-count").textContent = `${(data.evidence || []).length} SOURCES`;
  for (const source of data.evidence || []) {
    const card = element("article", "item-card");
    const top = element("div", "item-top");
    top.append(element("div", "item-title", value(source.title, "Evidence")));
    top.append(element("span", "item-meta", value(source.category, "Source")));
    card.append(top);
    card.append(element("p", "item-copy", value(source.summary, "No excerpt supplied.")));
    const tags = element("div", "item-tags");
    tags.append(element("span", "tag", value(source.source_id, "Source ID")));
    if (source.date) tags.append(element("span", "tag", source.date));
    if (source.authority) tags.append(element("span", "tag", source.authority));
    card.append(tags);
    evidence.append(card);
  }
  if (!evidence.children.length) addEmpty(evidence, "No source items were returned for this investigation.");

  const conflicts = document.querySelector("#conflicts-list");
  conflicts.replaceChildren();
  document.querySelector("#conflict-count").textContent = `${(data.conflicts || []).length} FOUND`;
  for (const conflict of data.conflicts || []) {
    const card = element("article", "item-card");
    card.append(element("div", "item-title", value(conflict.description, conflict.text || "Sources disagree.")));
    const tags = element("div", "item-tags");
    tags.append(element("span", "tag alert", value(conflict.status, "Unresolved")));
    if ((conflict.source_ids || []).length) tags.append(element("span", "tag", conflict.source_ids.join(", ")));
    card.append(tags);
    conflicts.append(card);
  }
  if (!conflicts.children.length) addEmpty(conflicts, "No unresolved conflicts were reported.");

  const limitations = document.querySelector("#limitations-list");
  limitations.replaceChildren();
  for (const limitation of data.limitations || []) limitations.append(element("div", "limitation", limitation));
  for (const error of data.errors || []) limitations.append(element("div", "limitation", error));

  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}
