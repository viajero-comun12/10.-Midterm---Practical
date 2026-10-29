/**
 * AWS URL Shortener - Frontend Application Logic
 * Consumes the FastAPI backend deployed on Amazon EC2.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const apiStatusPill = document.getElementById("api-status-pill");
  const statusDot = document.getElementById("status-dot");
  const statusLabel = document.getElementById("status-label");

  // Config Drawer Elements
  const btnToggleConfig = document.getElementById("btn-toggle-config");
  const configDrawer = document.getElementById("config-drawer");
  const btnCloseConfig = document.getElementById("btn-close-config");
  const inputApiUrl = document.getElementById("input-api-url");
  const btnSaveApi = document.getElementById("btn-save-api");
  const chipLocalhost = document.getElementById("chip-localhost");

  // Tabs
  const tabShorten = document.getElementById("tab-shorten");
  const tabInspect = document.getElementById("tab-inspect");
  const viewShorten = document.getElementById("view-shorten");
  const viewInspect = document.getElementById("view-inspect");

  // Shorten Form Elements
  const shortenForm = document.getElementById("shorten-form");
  const urlInput = document.getElementById("url-input");
  const btnClearUrl = document.getElementById("btn-clear-url");
  const btnSubmitShorten = document.getElementById("btn-submit-shorten");
  const spinnerShorten = document.getElementById("spinner-shorten");
  const shortenError = document.getElementById("shorten-error");
  const shortenErrorTitle = document.getElementById("shorten-error-title");
  const shortenErrorMsg = document.getElementById("shorten-error-msg");
  const dismissShortenError = document.getElementById("dismiss-shorten-error");

  // Results Elements
  const resultContainer = document.getElementById("result-container");
  const resultShortUrl = document.getElementById("result-short-url");
  const btnCopyUrl = document.getElementById("btn-copy-url");
  const btnOpenUrl = document.getElementById("btn-open-url");
  const resultUuid = document.getElementById("result-uuid");
  const resultOriginalUrl = document.getElementById("result-original-url");

  // Inspect Form Elements
  const inspectForm = document.getElementById("inspect-form");
  const inspectInput = document.getElementById("inspect-input");
  const btnSubmitInspect = document.getElementById("btn-submit-inspect");
  const spinnerInspect = document.getElementById("spinner-inspect");
  const inspectError = document.getElementById("inspect-error");
  const inspectErrorTitle = document.getElementById("inspect-error-title");
  const inspectErrorMsg = document.getElementById("inspect-error-msg");
  const dismissInspectError = document.getElementById("dismiss-inspect-error");
  const inspectResult = document.getElementById("inspect-result");
  const inspectJsonDisplay = document.getElementById("inspect-json-display");

  // History Elements
  const historyList = document.getElementById("history-list");
  const btnClearHistory = document.getElementById("btn-clear-history");
  const toastContainer = document.getElementById("toast-container");

  // State Management
  const STORAGE_KEY_API = "AWS_SHORTENER_API_URL";
  const STORAGE_KEY_HISTORY = "AWS_SHORTENER_HISTORY";

  function getApiBaseUrl() {
    const saved = localStorage.getItem(STORAGE_KEY_API);
    if (saved) return saved.replace(/\/+$/, "");
    if (window.API_BASE_URL) return window.API_BASE_URL.replace(/\/+$/, "");
    return "http://localhost:8000";
  }

  function setApiBaseUrl(url) {
    const cleaned = url.trim().replace(/\/+$/, "");
    localStorage.setItem(STORAGE_KEY_API, cleaned);
    inputApiUrl.value = cleaned;
    checkApiHealth();
  }

  // Toast Notification Helper
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${message}</span>
    `;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("fade-out");
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // Check Backend API Health
  async function checkApiHealth() {
    const baseUrl = getApiBaseUrl();
    statusDot.className = "status-dot";
    statusLabel.textContent = "Conectando...";

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const response = await fetch(`${baseUrl}/health`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        statusDot.className = "status-dot connected";
        const mode = data.storage_mode === "mock" ? "(Modo Local)" : "(DynamoDB)";
        statusLabel.textContent = `API EC2 Online ${mode}`;
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err) {
      statusDot.className = "status-dot error";
      statusLabel.textContent = "API Desconectada (Verifica IP EC2)";
    }
  }

  // Tab Switching
  function switchTab(target) {
    if (target === "shorten") {
      tabShorten.classList.add("active");
      tabShorten.setAttribute("aria-selected", "true");
      tabInspect.classList.remove("active");
      tabInspect.setAttribute("aria-selected", "false");
      viewShorten.classList.remove("hidden");
      viewInspect.classList.add("hidden");
    } else {
      tabInspect.classList.add("active");
      tabInspect.setAttribute("aria-selected", "true");
      tabShorten.classList.remove("active");
      tabShorten.setAttribute("aria-selected", "false");
      viewInspect.classList.remove("hidden");
      viewShorten.classList.add("hidden");
    }
  }

  tabShorten.addEventListener("click", () => switchTab("shorten"));
  tabInspect.addEventListener("click", () => switchTab("inspect"));

  // Config Drawer toggle
  btnToggleConfig.addEventListener("click", () => {
    configDrawer.classList.toggle("hidden");
    inputApiUrl.value = getApiBaseUrl();
  });

  btnCloseConfig.addEventListener("click", () => {
    configDrawer.classList.add("hidden");
  });

  btnSaveApi.addEventListener("click", () => {
    const val = inputApiUrl.value.trim();
    if (!val) {
      showToast("Por favor ingresa una URL válida", "error");
      return;
    }
    setApiBaseUrl(val);
    configDrawer.classList.add("hidden");
    showToast(`Endpoint actualizado: ${val}`, "success");
  });

  chipLocalhost.addEventListener("click", () => {
    inputApiUrl.value = "http://localhost:8000";
    setApiBaseUrl("http://localhost:8000");
    configDrawer.classList.add("hidden");
    showToast("Endpoint establecido en localhost:8000", "info");
  });

  // URL Input Clear Button
  urlInput.addEventListener("input", () => {
    if (urlInput.value.trim()) {
      btnClearUrl.classList.remove("hidden");
    } else {
      btnClearUrl.classList.add("hidden");
    }
  });

  btnClearUrl.addEventListener("click", () => {
    urlInput.value = "";
    btnClearUrl.classList.add("hidden");
    urlInput.focus();
  });

  dismissShortenError.addEventListener("click", () => {
    shortenError.classList.add("hidden");
  });

  dismissInspectError.addEventListener("click", () => {
    inspectError.classList.add("hidden");
  });

  // Client-side URL validation
  function isValidHttpUrl(string) {
    try {
      const url = new URL(string);
      return url.protocol === "http:" || url.protocol === "https:";
    } catch (_) {
      return false;
    }
  }

  // Handle URL Shortening (POST /shorten)
  shortenForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    shortenError.classList.add("hidden");

    let rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      showShortenError("Campo requerido", "Por favor ingresa la URL que deseas acortar.");
      return;
    }

    // Auto-prepend https:// if missing scheme
    if (!/^https?:\/\//i.test(rawUrl)) {
      rawUrl = "https://" + rawUrl;
      urlInput.value = rawUrl;
    }

    if (!isValidHttpUrl(rawUrl)) {
      showShortenError("URL no válida", "La URL debe ser válida e iniciar con http:// o https://");
      return;
    }

    const baseUrl = getApiBaseUrl();

    // UI Loading state
    btnSubmitShorten.disabled = true;
    spinnerShorten.classList.remove("hidden");
    btnSubmitShorten.querySelector(".btn-text").textContent = "Generando UUID...";

    try {
      const response = await fetch(`${baseUrl}/shorten`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ original_url: rawUrl })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Error HTTP ${response.status}`);
      }

      // Display results
      resultShortUrl.value = data.short_url;
      resultUuid.textContent = data.short_code;
      resultOriginalUrl.textContent = data.original_url;
      resultOriginalUrl.title = data.original_url;
      btnOpenUrl.href = data.short_url;

      resultContainer.classList.remove("hidden");
      resultContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

      // Save to local history
      saveToHistory({
        short_code: data.short_code,
        short_url: data.short_url,
        original_url: data.original_url,
        created_at: new Date().toISOString()
      });

      showToast("¡Enlace generado exitosamente!", "success");
    } catch (err) {
      console.error("Shorten error:", err);
      showShortenError(
        "No se pudo acortar el enlace",
        `Error al comunicar con ${baseUrl}: ${err.message}. Verifica que el backend en EC2 esté ejecutándose y los Security Groups permitan el tráfico.`
      );
    } finally {
      btnSubmitShorten.disabled = false;
      spinnerShorten.classList.add("hidden");
      btnSubmitShorten.querySelector(".btn-text").textContent = "Acortar Enlace";
    }
  });

  function showShortenError(title, message) {
    shortenErrorTitle.textContent = title;
    shortenErrorMsg.textContent = message;
    shortenError.classList.remove("hidden");
  }

  // Copy Shortened URL to Clipboard
  btnCopyUrl.addEventListener("click", async () => {
    const textToCopy = resultShortUrl.value;
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      btnCopyUrl.classList.add("copied");
      const copyTextSpan = btnCopyUrl.querySelector(".copy-text");
      copyTextSpan.textContent = "¡Copiado!";
      showToast("¡Enlace copiado al portapapeles!", "success");

      setTimeout(() => {
        btnCopyUrl.classList.remove("copied");
        copyTextSpan.textContent = "Copiar";
      }, 2000);
    } catch (err) {
      // Fallback for older browsers
      resultShortUrl.select();
      document.execCommand("copy");
      showToast("¡Enlace copiado!", "success");
    }
  });

  // Handle UUID Inspection (GET /urls/{short_code})
  inspectForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    inspectError.classList.add("hidden");
    inspectResult.classList.add("hidden");

    const code = inspectInput.value.trim();
    if (!code) {
      showInspectError("UUID Requerido", "Por favor ingresa el UUID que deseas consultar.");
      return;
    }

    const baseUrl = getApiBaseUrl();

    btnSubmitInspect.disabled = true;
    spinnerInspect.classList.remove("hidden");
    btnSubmitInspect.querySelector(".btn-text").textContent = "Consultando...";

    try {
      const response = await fetch(`${baseUrl}/urls/${encodeURIComponent(code)}`);
      const data = await response.json();

      if (response.status === 404) {
        showInspectError("404 Not Found", `El identificador UUID "${code}" no existe en la tabla DynamoDB.`);
        return;
      }

      if (!response.ok) {
        throw new Error(data.detail || `Error HTTP ${response.status}`);
      }

      // Display formatted JSON
      inspectJsonDisplay.textContent = JSON.stringify(data, null, 2);
      inspectResult.classList.remove("hidden");
      showToast("Registro recuperado de DynamoDB", "success");
    } catch (err) {
      console.error("Inspect error:", err);
      showInspectError(
        "Error en la consulta",
        `No fue posible consultar el UUID en ${baseUrl}: ${err.message}`
      );
    } finally {
      btnSubmitInspect.disabled = false;
      spinnerInspect.classList.add("hidden");
      btnSubmitInspect.querySelector(".btn-text").textContent = "Consultar DynamoDB";
    }
  });

  function showInspectError(title, message) {
    inspectErrorTitle.textContent = title;
    inspectErrorMsg.textContent = message;
    inspectError.classList.remove("hidden");
  }

  // History Management
  function loadHistory() {
    try {
      const data = localStorage.getItem(STORAGE_KEY_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      return [];
    }
  }

  function saveToHistory(item) {
    const list = loadHistory();
    // Prepend and keep max 10
    const filtered = list.filter((i) => i.short_code !== item.short_code);
    filtered.unshift(item);
    if (filtered.length > 10) filtered.pop();
    localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(filtered));
    renderHistory();
  }

  function renderHistory() {
    const items = loadHistory();
    historyList.innerHTML = "";

    if (items.length === 0) {
      historyList.innerHTML = `
        <div class="history-empty">
          <p>Aún no has generado enlaces. Ingresa una URL arriba para comenzar.</p>
        </div>
      `;
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "history-item";
      row.innerHTML = `
        <div class="history-item-info">
          <a href="${item.short_url}" target="_blank" class="history-item-short" title="Probar redirección 307">${item.short_url}</a>
          <span class="history-item-orig" title="${item.original_url}">↳ ${item.original_url}</span>
        </div>
        <div class="history-item-actions">
          <button class="btn-mini btn-history-copy" data-url="${item.short_url}" title="Copiar enlace">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            Copiar
          </button>
          <button class="btn-mini btn-history-inspect" data-code="${item.short_code}" title="Consultar en DynamoDB">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            Consultar
          </button>
          <a href="${item.short_url}" target="_blank" class="btn-mini" title="Redirigir">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            Probar
          </a>
        </div>
      `;
      historyList.appendChild(row);
    });

    // Attach copy actions
    document.querySelectorAll(".btn-history-copy").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const url = btn.getAttribute("data-url");
        await navigator.clipboard.writeText(url);
        showToast("¡Enlace copiado al portapapeles!", "success");
      });
    });

    // Attach inspect actions
    document.querySelectorAll(".btn-history-inspect").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = btn.getAttribute("data-code");
        inspectInput.value = code;
        switchTab("inspect");
        btnSubmitInspect.click();
      });
    });
  }

  btnClearHistory.addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY_HISTORY);
    renderHistory();
    showToast("Historial borrado", "info");
  });

  // Initial Boot
  inputApiUrl.value = getApiBaseUrl();
  renderHistory();
  checkApiHealth();
});
