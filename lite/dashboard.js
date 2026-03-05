const asinInput = document.getElementById("asinInput");
const loadByAsinBtn = document.getElementById("loadByAsinBtn");
const fileInput = document.getElementById("fileInput");
const statusText = document.getElementById("statusText");

const metaPanel = document.getElementById("metaPanel");
const gradesPanel = document.getElementById("gradesPanel");
const metaAsin = document.getElementById("metaAsin");
const metaMarket = document.getElementById("metaMarket");
const metaCategory = document.getElementById("metaCategory");
const metaProduct = document.getElementById("metaProduct");
const overallGrade = document.getElementById("overallGrade");
const gradesGrid = document.getElementById("gradesGrid");

const GRADE_TO_SCORE = { A: 95, B: 82, C: 67, D: 50, F: 20 };
const GRADE_COLOR = {
  A: "var(--a)",
  B: "var(--b)",
  C: "var(--c)",
  D: "var(--d)",
  F: "var(--f)",
};

loadByAsinBtn.addEventListener("click", async () => {
  const asin = (asinInput.value || "").trim();
  if (!asin) {
    setStatus("Please enter an ASIN.", true);
    return;
  }

  const path = `../results/${asin}_pipeline.json`;
  setStatus(`Loading ${path} ...`, false);

  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`File not found (${res.status})`);
    }

    const payload = await res.json();
    renderDashboard(payload);
    setStatus(`Loaded ${asin}_pipeline.json`, false);
  } catch (err) {
    setStatus(`Load failed: ${err.message}`, true);
  }
});

fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }

  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    renderDashboard(payload);
    setStatus(`Loaded file: ${file.name}`, false);
  } catch (err) {
    setStatus(`Invalid JSON file: ${err.message}`, true);
  }
});

function renderDashboard(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Payload is not a JSON object.");
  }

  const summary = payload.grades_summary;
  if (!summary || typeof summary !== "object") {
    throw new Error("grades_summary is missing.");
  }

  metaAsin.textContent = payload.asin || payload.pipeline_meta?.asin || "-";
  metaMarket.textContent = payload.market || payload.pipeline_meta?.market || "-";
  metaCategory.textContent = payload.category_path || payload.pipeline_meta?.category_path || "-";
  metaProduct.textContent = payload.product || "-";

  const entries = Object.entries(summary);
  if (!entries.length) {
    throw new Error("grades_summary is empty.");
  }

  const gradePoints = entries
    .map(([, grade]) => GRADE_TO_SCORE[normalizeGrade(grade)] || 0)
    .filter((v) => v > 0);
  const average = gradePoints.reduce((a, b) => a + b, 0) / gradePoints.length;
  const overall = scoreToLetter(average);
  overallGrade.textContent = `Overall ${overall}`;
  overallGrade.style.color = GRADE_COLOR[overall] || "var(--bg-ink)";

  gradesGrid.innerHTML = "";
  entries.forEach(([key, grade]) => {
    const letter = normalizeGrade(grade);
    const score = GRADE_TO_SCORE[letter] || 0;
    const color = GRADE_COLOR[letter] || "#666";

    const card = document.createElement("article");
    card.className = "grade-card";

    const title = document.createElement("h3");
    title.textContent = prettifySkillKey(key);

    const top = document.createElement("div");
    top.className = "grade-top";

    const scoreLabel = document.createElement("span");
    scoreLabel.textContent = `Score proxy ${Math.round(score)}`;

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.style.background = color;
    badge.textContent = letter;

    top.append(scoreLabel, badge);

    const bar = document.createElement("div");
    bar.className = "bar";

    const fill = document.createElement("div");
    fill.className = "fill";
    fill.style.width = `${score}%`;
    fill.style.background = color;

    bar.appendChild(fill);

    card.append(title, top, bar);
    gradesGrid.appendChild(card);
  });

  metaPanel.hidden = false;
  gradesPanel.hidden = false;
}

function normalizeGrade(grade) {
  return String(grade || "").trim().toUpperCase();
}

function scoreToLetter(score) {
  if (score >= 90) return "A";
  if (score >= 75) return "B";
  if (score >= 60) return "C";
  if (score >= 40) return "D";
  return "F";
}

function prettifySkillKey(key) {
  return String(key)
    .replace(/^skill_\d+_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function setStatus(message, isError) {
  statusText.textContent = message;
  statusText.className = isError ? "status error" : "status ok";
}
