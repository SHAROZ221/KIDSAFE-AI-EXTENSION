// KidSafe AI - Parent Dashboard Client Application

const API_BASE = window.location.origin;

let authToken = localStorage.getItem("kidsafe_token");
let currentParent = JSON.parse(localStorage.getItem("kidsafe_parent") || "null");
let profiles = [];
let activeProfileId = null;

document.addEventListener("DOMContentLoaded", () => {
  setupNavListeners();
  setupAuthFormListeners();
  setupActionListeners();
  setupAIAssistant();

  if (authToken) {
    showDashboard();
    loadDashboardData();
  } else {
    showAuthScreen();
  }
});

// UI Views Toggle
function showAuthScreen() {
  document.getElementById("authScreen").classList.remove("hidden");
  document.getElementById("appContainer").classList.add("hidden");
}

function showDashboard() {
  document.getElementById("authScreen").classList.add("hidden");
  document.getElementById("appContainer").classList.remove("hidden");
  if (currentParent) {
    document.getElementById("userNameLabel").textContent = currentParent.full_name || "Parent";
    document.getElementById("userEmailLabel").textContent = currentParent.email || "";
  }
}

// Navigation & Tab Switching
function setupNavListeners() {
  const navItems = document.querySelectorAll(".nav-item");
  const viewPanels = document.querySelectorAll(".view-panel");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      viewPanels.forEach(p => p.classList.remove("active"));

      item.classList.add("active");
      const targetView = item.dataset.view;
      document.getElementById(targetView)?.classList.add("active");

      // Update header title
      const titles = {
        viewOverview: "Overview",
        viewProfiles: "Child Profiles",
        viewApprovals: "Approval Requests",
        viewRules: "Custom Web Rules",
        viewAIAssistant: "AI Agent Assistant",
        viewPairing: "Pair Browser Extension",
        viewLogs: "Activity & Safety Logs"
      };
      document.getElementById("pageTitle").textContent = titles[targetView] || "Dashboard";

      // Refresh specific tab data
      if (targetView === "viewApprovals") loadApprovals();
      if (targetView === "viewRules") loadRules();
      if (targetView === "viewLogs") loadLogs();
      if (targetView === "viewProfiles") renderProfilesList();
    });
  });

  document.getElementById("btnViewAllApprovals")?.addEventListener("click", () => {
    document.querySelector('.nav-item[data-view="viewApprovals"]')?.click();
  });

  document.getElementById("btnQuickPairModal")?.addEventListener("click", () => {
    document.querySelector('.nav-item[data-view="viewPairing"]')?.click();
  });

  document.getElementById("childProfileSelector")?.addEventListener("change", (e) => {
    activeProfileId = e.target.value;
    updateOverviewStats();
    loadApprovals();
    loadRules();
    loadLogs();
  });
}

// Auth Forms
function setupAuthFormListeners() {
  const tabLoginBtn = document.getElementById("tabLoginBtn");
  const tabRegisterBtn = document.getElementById("tabRegisterBtn");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  // Tab switching: Sign In vs Create Account
  tabLoginBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    tabLoginBtn.classList.add("active");
    tabRegisterBtn.classList.remove("active");
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");
  });

  tabRegisterBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    tabRegisterBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    registerForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
  });

  // Login submission
  loginForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const errEl = document.getElementById("loginError");
    errEl.classList.add("hidden");

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");

      setSession(data.access_token, data);
      showDashboard();
      loadDashboardData();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });

  // Register submission
  registerForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("regName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const errEl = document.getElementById("regError");
    errEl.classList.add("hidden");

    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");

      setSession(data.access_token, data);
      showDashboard();
      loadDashboardData();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });

  document.getElementById("btnLogout")?.addEventListener("click", () => {
    localStorage.removeItem("kidsafe_token");
    localStorage.removeItem("kidsafe_parent");
    authToken = null;
    currentParent = null;
    showAuthScreen();
  });
}

function setSession(token, parentData) {
  authToken = token;
  currentParent = parentData;
  localStorage.setItem("kidsafe_token", token);
  localStorage.setItem("kidsafe_parent", JSON.stringify(parentData));
}

// Action Listeners
function setupActionListeners() {
  // Generate Pairing Code
  document.getElementById("btnGeneratePairCode")?.addEventListener("click", async () => {
    if (!activeProfileId) return;
    try {
      const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/generate-pairing-code`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      const data = await res.json();
      if (res.ok) {
        document.getElementById("displayCode").textContent = data.code;
        document.getElementById("pairCodeDisplay").classList.remove("hidden");
      }
    } catch (err) {
      console.error("Pairing code error:", err);
    }
  });

  // Add Custom Rule
  document.getElementById("btnAddNewRule")?.addEventListener("click", async () => {
    if (!activeProfileId) return;
    const domainInput = document.getElementById("newRuleDomain");
    const ruleType = document.getElementById("newRuleType").value;
    const domain = domainInput.value.trim();

    if (!domain) return;

    try {
      const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/rules`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({ domain, rule_type: ruleType })
      });
      if (res.ok) {
        domainInput.value = "";
        loadRules();
      }
    } catch (err) {
      console.error("Add rule error:", err);
    }
  });

  // Refresh Logs
  document.getElementById("btnRefreshLogs")?.addEventListener("click", () => {
    loadLogs();
  });

  // Export CSV Report
  document.getElementById("btnExportCsv")?.addEventListener("click", async () => {
    if (!activeProfileId) return;
    try {
      const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/logs/export.csv`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `kidsafe_activity_report.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      console.error("Export CSV error:", err);
    }
  });

  // Modal: Add Child Profile
  const modal = document.getElementById("profileModal");
  document.getElementById("btnOpenNewProfileModal")?.addEventListener("click", () => {
    modal.classList.remove("hidden");
  });
  document.getElementById("btnCloseProfileModal")?.addEventListener("click", () => {
    modal.classList.add("hidden");
  });
  document.getElementById("btnCancelProfileModal")?.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  document.getElementById("createProfileForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("newChildName").value.trim();
    const age = parseInt(document.getElementById("newChildAge").value, 10);
    const tier = document.getElementById("newChildTier").value;
    const daily_time_limit_minutes = parseInt(document.getElementById("newChildLimit").value, 10);

    try {
      const res = await fetch(`${API_BASE}/api/profiles`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({ name, age, tier, daily_time_limit_minutes })
      });
      if (res.ok) {
        modal.classList.add("hidden");
        document.getElementById("createProfileForm").reset();
        await loadDashboardData();
      }
    } catch (err) {
      console.error("Create profile error:", err);
    }
  });
}

// Data Loaders
async function loadDashboardData() {
  try {
    const res = await fetch(`${API_BASE}/api/profiles`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.status === 401) {
      document.getElementById("btnLogout")?.click();
      return;
    }
    profiles = await res.json();

    const selector = document.getElementById("childProfileSelector");
    selector.innerHTML = "";

    profiles.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (${formatTier(p.tier)})`;
      selector.appendChild(opt);
    });

    if (profiles.length > 0) {
      if (!activeProfileId || !profiles.some(p => p.id === activeProfileId)) {
        activeProfileId = profiles[0].id;
      }
      selector.value = activeProfileId;
    }

    updateOverviewStats();
    loadApprovals();
    loadRules();
    loadLogs();
    renderProfilesList();
  } catch (err) {
    console.error("Load dashboard data failed:", err);
  }
}

function updateOverviewStats() {
  const profile = profiles.find(p => p.id === activeProfileId);
  if (!profile) return;

  const usedMinutes = Math.floor((profile.time_used_today_seconds || 0) / 60);
  document.getElementById("statScreenTime").textContent = `${usedMinutes}m`;
  document.getElementById("statLimitSub").textContent = `of ${profile.daily_time_limit_minutes}m daily limit`;

  document.getElementById("statStrictness").textContent = formatTier(profile.tier);
  document.getElementById("statAgeSub").textContent = `Age ${profile.age} • ${profile.tier.replace(/_/g, " ")}`;

  document.getElementById("statShieldStatus").textContent = profile.is_protection_active ? "Active" : "Paused";
  document.getElementById("statShieldStatus").className = profile.is_protection_active ? "metric-number safe" : "metric-number highlight";
}

// Approvals
async function loadApprovals() {
  if (!activeProfileId) return;
  try {
    const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/requests`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const requests = await res.json();

    const pending = requests.filter(r => r.status === "pending");
    document.getElementById("statPendingCount").textContent = pending.length;
    document.getElementById("navBadgeApprovals").textContent = pending.length;

    renderApprovalsTable(document.getElementById("overviewApprovalsList"), requests.slice(0, 5));
    renderApprovalsTable(document.getElementById("fullApprovalsTable"), requests);
  } catch (err) {
    console.error("Load approvals error:", err);
  }
}

function renderApprovalsTable(container, list) {
  if (!container) return;
  if (!list || list.length === 0) {
    container.innerHTML = `<div style="padding:24px;text-align:center;color:#94a3b8;font-size:13px;">No requests found.</div>`;
    return;
  }

  let html = `
    <table>
      <thead>
        <tr>
          <th>Domain / Site</th>
          <th>Child's Note</th>
          <th>Requested At</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
  `;

  list.forEach(req => {
    const dateStr = new Date(req.requested_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    html += `
      <tr>
        <td><strong>${escapeHtml(req.domain)}</strong></td>
        <td>"${escapeHtml(req.reason)}"</td>
        <td>${dateStr}</td>
        <td><span class="status-badge ${req.status}">${req.status}</span></td>
        <td>
          ${req.status === "pending" ? `
            <button class="btn btn-sm btn-success btn-approve-req" data-id="${req.id}">Approve</button>
            <button class="btn btn-sm btn-danger btn-deny-req" data-id="${req.id}">Deny</button>
          ` : `<span style="color:#94a3b8;font-size:12px;">Resolved</span>`}
        </td>
      </tr>
    `;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;

  container.querySelectorAll(".btn-approve-req").forEach(b => {
    b.addEventListener("click", async () => {
      await fetch(`${API_BASE}/api/requests/${b.dataset.id}/approve`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      loadApprovals();
      loadRules();
    });
  });

  container.querySelectorAll(".btn-deny-req").forEach(b => {
    b.addEventListener("click", async () => {
      await fetch(`${API_BASE}/api/requests/${b.dataset.id}/deny`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      loadApprovals();
    });
  });
}

// Rules
async function loadRules() {
  if (!activeProfileId) return;
  try {
    const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/rules`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const rules = await res.json();

    const allowContainer = document.getElementById("dashboardAllowlist");
    const blockContainer = document.getElementById("dashboardBlocklist");
    allowContainer.innerHTML = "";
    blockContainer.innerHTML = "";

    const allowRules = rules.filter(r => r.rule_type === "allow");
    const blockRules = rules.filter(r => r.rule_type === "block");

    if (allowRules.length === 0) {
      allowContainer.innerHTML = `<span style="color:#94a3b8;font-size:12px;">No allowed domains yet.</span>`;
    } else {
      allowRules.forEach(r => allowContainer.appendChild(createTag(r)));
    }

    if (blockRules.length === 0) {
      blockContainer.innerHTML = `<span style="color:#94a3b8;font-size:12px;">No blocked domains yet.</span>`;
    } else {
      blockRules.forEach(r => blockContainer.appendChild(createTag(r)));
    }
  } catch (err) {
    console.error("Load rules error:", err);
  }
}

function createTag(rule) {
  const el = document.createElement("div");
  el.className = "tag-item";
  el.innerHTML = `
    <span>${escapeHtml(rule.domain)}</span>
    <span class="tag-del" data-id="${rule.id}">&times;</span>
  `;
  el.querySelector(".tag-del").addEventListener("click", async () => {
    await fetch(`${API_BASE}/api/profiles/${activeProfileId}/rules/${rule.id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    loadRules();
  });
  return el;
}

// Profiles List
function renderProfilesList() {
  const grid = document.getElementById("profilesCardsGrid");
  if (!grid) return;
  grid.innerHTML = "";

  profiles.forEach(p => {
    const card = document.createElement("div");
    card.className = "profile-card";
    card.innerHTML = `
      <div class="profile-card-header">
        <span class="profile-card-name">${escapeHtml(p.name)}</span>
        <span class="status-badge ${p.is_protection_active ? 'approved' : 'denied'}">
          ${p.is_protection_active ? 'Active' : 'Paused'}
        </span>
      </div>
      <p style="font-size:12px;color:#64748b;margin-bottom:8px;">Age: ${p.age} • Tier: ${formatTier(p.tier)}</p>
      <p style="font-size:12px;color:#64748b;margin-bottom:12px;">Daily Limit: ${p.daily_time_limit_minutes} mins</p>
      <button class="btn btn-secondary btn-sm w-100 btn-select-p" data-id="${p.id}">
        ${p.id === activeProfileId ? 'Selected Profile' : 'Select Profile'}
      </button>
    `;
    card.querySelector(".btn-select-p").addEventListener("click", () => {
      activeProfileId = p.id;
      document.getElementById("childProfileSelector").value = p.id;
      loadDashboardData();
    });
    grid.appendChild(card);
  });
}

// Logs
async function loadLogs() {
  if (!activeProfileId) return;
  const container = document.getElementById("logsTableContainer");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/profiles/${activeProfileId}/logs`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const logs = await res.json();

    if (logs.length === 0) {
      container.innerHTML = `<div style="padding:24px;text-align:center;color:#94a3b8;font-size:13px;">No navigation activity recorded yet.</div>`;
      return;
    }

    let html = `
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Domain</th>
            <th>Action</th>
            <th>Reason / Category</th>
          </tr>
        </thead>
        <tbody>
    `;

    logs.forEach(l => {
      const timeStr = new Date(l.timestamp).toLocaleTimeString();
      html += `
        <tr>
          <td>${timeStr}</td>
          <td><strong>${escapeHtml(l.domain)}</strong></td>
          <td><span class="status-badge ${l.action}">${l.action}</span></td>
          <td>${escapeHtml(l.reason || l.category)}</td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
  } catch (err) {
    console.error("Load logs error:", err);
  }
}

// Phase 3: AI Agent Assistant UI Logic
function setupAIAssistant() {
  // 1. Overview AI quick command
  const btnOverviewAi = document.getElementById("btnOverviewAiSend");
  const inputOverviewAi = document.getElementById("overviewAiInput");
  const previewOverviewBox = document.getElementById("overviewAiPreviewBox");

  btnOverviewAi?.addEventListener("click", async () => {
    const text = inputOverviewAi.value.trim();
    if (!text || !activeProfileId) return;
    await handleAiPreview(text, previewOverviewBox, btnOverviewAi);
  });

  // 2. Full Assistant Tab
  const btnAssistantSend = document.getElementById("btnAssistantSend");
  const inputAssistant = document.getElementById("assistantInput");
  const previewAssistantBox = document.getElementById("assistantPreviewContainer");

  btnAssistantSend?.addEventListener("click", async () => {
    const text = inputAssistant.value.trim();
    if (!text || !activeProfileId) return;
    await handleAiPreview(text, previewAssistantBox, btnAssistantSend);
  });

  // Example prompt chips
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      inputAssistant.value = chip.dataset.prompt;
      btnAssistantSend.click();
    });
  });

  // 3. AI Classifier URL Inspector
  const btnInspect = document.getElementById("btnRunClassification");
  const inputInspectUrl = document.getElementById("testClassifyUrl");
  const resultBox = document.getElementById("classifierResultBox");

  btnInspect?.addEventListener("click", async () => {
    const url = inputInspectUrl.value.trim();
    if (!url) return;

    btnInspect.disabled = true;
    btnInspect.textContent = "Analyzing...";

    try {
      const profile = profiles.find(p => p.id === activeProfileId);
      const res = await fetch(`${API_BASE}/api/ai/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          age_profile: profile ? profile.tier : "junior"
        })
      });
      const data = await res.json();

      resultBox.innerHTML = `
        <div class="class-row"><strong>Verdict:</strong> <span class="status-badge ${data.verdict}">${data.verdict.toUpperCase()}</span></div>
        <div class="class-row"><strong>Confidence:</strong> <span>${(data.confidence * 100).toFixed(0)}%</span></div>
        <div class="class-row"><strong>Age Rating:</strong> <span>${data.age_rating}</span></div>
        <div class="class-row"><strong>Categories:</strong> <span>${data.categories.join(", ")}</span></div>
        <div class="class-row" style="margin-top:6px;"><strong>Parent Explanation:</strong> <span>${escapeHtml(data.reason_parent)}</span></div>
        <div class="class-row"><strong>Child Friendly Note:</strong> <span>${escapeHtml(data.reason_child)}</span></div>
      `;
      resultBox.classList.remove("hidden");
    } catch (err) {
      resultBox.innerHTML = `<span style="color:#dc2626;">Classification failed.</span>`;
      resultBox.classList.remove("hidden");
    } finally {
      btnInspect.disabled = false;
      btnInspect.textContent = "Inspect URL";
    }
  });
}

async function handleAiPreview(instruction, container, btnTrigger) {
  if (!container || !activeProfileId) return;

  btnTrigger.disabled = true;
  btnTrigger.textContent = "Agent Thinking...";

  try {
    const res = await fetch(`${API_BASE}/api/ai/nl-rule/preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify({
        profile_id: activeProfileId,
        instruction
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      container.innerHTML = `<div style="color:#dc2626;font-size:13px;">${data.message || "Could not parse instruction."}</div>`;
      container.classList.remove("hidden");
      return;
    }

    let itemsHtml = data.actions.map(a => `<li>${escapeHtml(a.summary)}</li>`).join("");

    container.innerHTML = `
      <div class="preview-header">
        <h4>Proposed Policy Changes for ${escapeHtml(data.target_child)}:</h4>
        <span class="status-badge pending">Confirmation Needed</span>
      </div>
      <ul class="preview-actions-list">${itemsHtml}</ul>
      <div class="preview-btn-row">
        <button class="btn btn-secondary btn-sm" id="btnCancelAiPreview">Cancel</button>
        <button class="btn btn-primary btn-sm" id="btnConfirmAiAction">Confirm & Apply</button>
      </div>
    `;
    container.classList.remove("hidden");

    container.querySelector("#btnCancelAiPreview")?.addEventListener("click", () => {
      container.classList.add("hidden");
    });

    container.querySelector("#btnConfirmAiAction")?.addEventListener("click", async () => {
      const confirmBtn = container.querySelector("#btnConfirmAiAction");
      confirmBtn.disabled = true;
      confirmBtn.textContent = "Applying...";

      const confRes = await fetch(`${API_BASE}/api/ai/nl-rule/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({
          profile_id: activeProfileId,
          actions: data.actions
        })
      });

      if (confRes.ok) {
        container.innerHTML = `<div style="color:#16a34a;font-weight:600;font-size:13px;">Changes applied successfully by AI Agent!</div>`;
        setTimeout(() => {
          container.classList.add("hidden");
          loadDashboardData();
        }, 1500);
      }
    });
  } catch (err) {
    container.innerHTML = `<div style="color:#dc2626;font-size:13px;">Failed to reach AI Agent.</div>`;
    container.classList.remove("hidden");
  } finally {
    btnTrigger.disabled = false;
    btnTrigger.textContent = btnTrigger.id.includes("Overview") ? "Ask AI Agent" : "Preview Changes";
  }
}

function formatTier(tier) {
  const map = {
    little_explorer: "Little Explorer (5–8)",
    junior: "Junior (9–12)",
    teen: "Teen (13–17)"
  };
  return map[tier] || tier;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[m]));
}
