// ---------- Theme toggle ----------
(function () {
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const stored = localStorage.getItem("crop-doctor-theme");
  if (stored) root.setAttribute("data-theme", stored);

  function syncIcons() {
    const isLight = root.getAttribute("data-theme") === "light";
    const moon = toggle.querySelector(".icon-moon");
    const sun = toggle.querySelector(".icon-sun");
    moon.style.display = isLight ? "none" : "block";
    sun.style.display = isLight ? "block" : "none";
  }
  if (toggle) {
    syncIcons();
    toggle.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      localStorage.setItem("crop-doctor-theme", next);
      syncIcons();
    });
  }
  document.getElementById("year") &&
    (document.getElementById("year").textContent = new Date().getFullYear());
})();

// ---------- Diagnosis flow (only runs on the home page) ----------
(function () {
  const dropzone = document.getElementById("upload-zone");
  if (!dropzone) return;

  const fileInput = document.getElementById("file-input");
  const previewWrap = document.getElementById("preview-wrap");
  const previewImg = document.getElementById("preview-img");
  const analyzeBtn = document.getElementById("analyze-btn");
  const resultCard = document.getElementById("result-card");
  const errorBox = document.getElementById("error-box");
  const analyzeSpinner = document.getElementById("analyze-spinner");

  const qform = document.getElementById("qform");
  const reportBtn = document.getElementById("report-btn");
  const reportCard = document.getElementById("report-card");
  const reportBody = document.getElementById("report-body");
  const reportSpinner = document.getElementById("report-spinner");
  const startOverBtn = document.getElementById("start-over-btn");

  let currentFile = null;
  let lastPrediction = null;

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.add("show");
  }
  function clearError() {
    errorBox.classList.remove("show");
    errorBox.textContent = "";
  }

  function setPreview(fileOrUrl) {
    clearError();
    resultCard.classList.remove("show");
    reportCard.classList.remove("show");
    if (typeof fileOrUrl === "string") {
      previewImg.src = fileOrUrl;
    } else {
      previewImg.src = URL.createObjectURL(fileOrUrl);
    }
    previewWrap.classList.add("show");
    analyzeBtn.disabled = false;
  }

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      currentFile = e.dataTransfer.files[0];
      setPreview(currentFile);
    }
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      currentFile = fileInput.files[0];
      setPreview(currentFile);
    }
  });

  document.querySelectorAll(".sample-tile").forEach((tile) => {
    tile.addEventListener("click", async () => {
      const url = tile.dataset.src;
      setPreview(url);
      const resp = await fetch(url);
      const blob = await resp.blob();
      currentFile = new File([blob], url.split("/").pop(), { type: blob.type });
    });
  });

  analyzeBtn.addEventListener("click", async () => {
    if (!currentFile) { showError("Please choose an image first."); return; }
    clearError();
    analyzeBtn.disabled = true;
    analyzeSpinner.classList.add("show");

    const formData = new FormData();
    formData.append("image", currentFile);

    try {
      const resp = await fetch("/api/predict", { method: "POST", body: formData });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Prediction failed.");

      lastPrediction = data;
      renderResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      analyzeSpinner.classList.remove("show");
      analyzeBtn.disabled = false;
    }
  });

  function renderResult(data) {
    document.getElementById("result-crop-condition").textContent = `${data.crop} — ${data.condition}`;
    const badge = document.getElementById("result-badge");
    badge.textContent = data.healthy ? "Healthy" : "Disease detected";
    badge.className = "result-badge " + (data.healthy ? "healthy" : "disease");
    document.getElementById("result-confidence-label").textContent = `${data.confidence}% confidence`;
    document.getElementById("confidence-fill").style.width = `${data.confidence}%`;

    const demoNotice = document.getElementById("demo-notice");
    demoNotice.style.display = data.demo_mode ? "block" : "none";

    resultCard.classList.add("show");
    resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  reportBtn.addEventListener("click", async () => {
    if (!lastPrediction) return;
    clearError();
    reportBtn.disabled = true;
    reportSpinner.classList.add("show");
    reportCard.classList.remove("show");

    const answers = {};
    new FormData(qform).forEach((value, key) => { answers[key] = value; });

    try {
      const resp = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          disease_key: lastPrediction.disease_key,
          confidence: lastPrediction.confidence,
          image_url: lastPrediction.image_url,
          history_id: lastPrediction.history_id,
          answers,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Report generation failed.");

      reportBody.innerHTML = markdownToHtml(data.report_markdown);
      reportCard.classList.add("show");
      reportCard.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      showError(err.message);
    } finally {
      reportSpinner.classList.remove("show");
      reportBtn.disabled = false;
    }
  });

  startOverBtn && startOverBtn.addEventListener("click", () => {
    currentFile = null;
    lastPrediction = null;
    previewWrap.classList.remove("show");
    resultCard.classList.remove("show");
    reportCard.classList.remove("show");
    qform.reset();
    fileInput.value = "";
    clearError();
    dropzone.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  // Minimal markdown -> HTML (headings, bold, paragraphs, italics). No external deps.
  function markdownToHtml(md) {
    const escape = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return escape(md)
      .split(/\n{2,}/)
      .map((block) => {
        if (/^### /.test(block)) return `<h3>${block.replace(/^### /, "")}</h3>`;
        if (/^## /.test(block)) return `<h2>${block.replace(/^## /, "")}</h2>`;
        let html = block
          .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
          .replace(/_(.+?)_/g, "<em>$1</em>")
          .replace(/\n/g, "<br>");
        return `<p>${html}</p>`;
      })
      .join("\n");
  }
})();
