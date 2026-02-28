/* ==========================================================================
   Server Room Monitor - Shared Frontend Script
   Handles login + dashboard logic with a single file.
   ========================================================================== */

// --- Supabase configuration (replace with your project values) ---
const SUPABASE_URL = "https://shqyxskelognjfqohucs.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNocXl4c2tlbG9nbmpmcW9odWNzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyNzg4NDAsImV4cCI6MjA4Nzg1NDg0MH0.DciVl2cLDJYCnQ1cpcbn-K4LV1Cfzr_4omi36u5F0aQ";

// --- Dashboard refresh interval (ms) ---
const REFRESH_MS = 5000;

let accessToken = null;

// --- DEV ONLY: bypass auth to view dashboard without signing in ---
const DEV_BYPASS_AUTH = false;

// ==========================================================================
// Helpers
// ==========================================================================
function getEl(id) {
  return document.getElementById(id);
}

function showError(msg) {
  const el = getEl("errMsg");
  if (!el) return;
  el.textContent = msg;
  el.style.display = "block";
}

// ==========================================================================
// Login
// ==========================================================================
async function doLogin() {
  const emailInput = getEl("email");
  const passInput = getEl("password");
  const btn = getEl("loginBtn");

  if (!emailInput || !passInput || !btn) return;

  const email = emailInput.value.trim();
  const password = passInput.value;

  const errDiv = getEl("errMsg");
  if (errDiv) errDiv.style.display = "none";

  if (!email || !password) {
    showError("Please enter email and password.");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Signing in...";

  try {
    const resp = await fetch(
      `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: SUPABASE_ANON_KEY,
        },
        body: JSON.stringify({ email, password }),
      }
    );
    const data = await resp.json();
    if (!resp.ok) {
      showError(data.error_description || data.msg || "Login failed.");
      return;
    }
    localStorage.setItem("sb_session", JSON.stringify(data));
    window.location.href = "dashboard.html";
  } catch (e) {
    showError("Network error - check your connection.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
}

function loginInit() {
  const btn = getEl("loginBtn");
  if (!btn) return;

  // If already logged in, go straight to dashboard
  const stored = localStorage.getItem("sb_session");
  if (stored) {
    const sess = JSON.parse(stored);
    if (sess.expires_at > Date.now() / 1000) {
      window.location.href = "dashboard.html";
      return;
    }
  }

  btn.addEventListener("click", doLogin);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doLogin();
  });
}

// ==========================================================================
// Dashboard
// ==========================================================================
function loadSession() {
  if (DEV_BYPASS_AUTH) {
    accessToken = SUPABASE_ANON_KEY;
    return false; // Still return false to avoid showing "Live" status in header
  }
  const raw = localStorage.getItem("sb_session");
  if (!raw) {
    window.location.href = "login.html";
    return false;
  }
  const sess = JSON.parse(raw);
  if (sess.expires_at < Date.now() / 1000) {
    localStorage.removeItem("sb_session");
    window.location.href = "login.html";
    return false;
  }
  accessToken = sess.access_token;
  return true;
}

function logout() {
  localStorage.removeItem("sb_session");
  window.location.href = "login.html";
}

async function fetchData() {
  try {
    const url =
      `${SUPABASE_URL}/rest/v1/telemetry?select=*` +
      "&order=created_at.desc&limit=20";
    const resp = await fetch(url, {
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${accessToken}`,
      },
    });
    if (resp.status === 401) {
      logout();
      return;
    }
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const rows = await resp.json();
    render(rows);
    setConnected(true);
  } catch (e) {
    console.error("Fetch error:", e);
    setConnected(false);
  }
}

function render(rows) {
  getEl("loadingMsg").style.display = "none";
  getEl("statusCards").style.display = "";
  getEl("tableSection").style.display = "";
  getEl("lastUpdate").textContent =
    "Updated " + new Date().toLocaleTimeString();

  if (rows.length === 0) return;
  const latest = rows[0];

  // Temperature
  const temp = latest.temperature_c;
  setCard(
    "cTemp",
    "vTemp",
    temp !== null ? temp.toFixed(1) : "--",
    temp !== null && temp > 35 ? "alert" : "ok"
  );

  // Humidity
  const hum = latest.humidity_pct;
  setCard(
    "cHumid",
    "vHumid",
    hum !== null ? hum.toFixed(0) : "--",
    hum !== null && hum > 70 ? "warn" : "ok"
  );

  // Gas
  setCard(
    "cGas",
    "vGas",
    latest.gas_alert ? "ALERT" : "OK",
    latest.gas_alert ? "alert" : "ok"
  );

  // Power
  setCard(
    "cPwr",
    "vPwr",
    latest.power_source,
    latest.power_source === "GRID" ? "ok" : "warn"
  );

  // Alarm
  setCard(
    "cAlarm",
    "vAlarm",
    latest.alarm_active ? "ACTIVE" : "OFF",
    latest.alarm_active ? "alert" : "ok"
  );

  // Table
  const tbody = getEl("logBody");
  tbody.innerHTML = rows
    .map(
      (r) => `
        <tr>
          <td data-label="Time">${new Date(r.created_at).toLocaleString()}</td>
          <td data-label="Temp">${r.temperature_c !== null ? Number(r.temperature_c).toFixed(1) : "--"}</td>
          <td data-label="Humidity">${r.humidity_pct !== null ? Number(r.humidity_pct).toFixed(0) : "--"}</td>
          <td data-label="Gas"><span class="badge ${r.gas_alert ? "alert" : "ok"}">${r.gas_alert ? "ALERT" : "OK"}</span></td>
          <td data-label="Grid"><span class="badge ${r.grid_present ? "ok" : "alert"}">${r.grid_present ? "YES" : "NO"}</span></td>
          <td data-label="Power"><span class="badge ${r.power_source === "GRID" ? "grid" : "bkup"}">${r.power_source}</span></td>
          <td data-label="Alarm"><span class="badge ${r.alarm_active ? "alert" : "ok"}">${r.alarm_active ? "ON" : "OFF"}</span></td>
        </tr>`
    )
    .join("");
}

function setCard(cardId, valueId, text, state) {
  getEl(valueId).textContent = text;
  const card = getEl(cardId);
  card.className = `card ${state || ""}`.trim();
}

function setConnected(online) {
  getEl("connDot").className = `online-dot${online ? "" : " offline"}`;
  getEl("connLabel").textContent = online ? "Live" : "Offline";
}

function dashboardInit() {
  const logoutBtn = getEl("logoutBtn");
  if (logoutBtn) logoutBtn.addEventListener("click", logout);

  if (loadSession()) {
    fetchData();
    setInterval(fetchData, REFRESH_MS);
  }
}

// ==========================================================================
// Page Router
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  if (document.body.classList.contains("page-login")) {
    loginInit();
  }
  if (document.body.classList.contains("page-dashboard")) {
    dashboardInit();
  }
});
