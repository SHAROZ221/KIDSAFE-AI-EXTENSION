// KidSafe AI - Extension Popup Controller
import { PROFILES } from "../utils/constants.js";

let currentState = null;

document.addEventListener("DOMContentLoaded", async () => {
  await loadStateAndRender();
  setupEventListeners();
});

async function loadStateAndRender() {
  const resp = await chrome.runtime.sendMessage({ type: "GET_STATE" });
  if (resp && resp.state) {
    currentState = resp.state;
    renderChildView();
    renderParentView();
  }
}

function renderChildView() {
  const statusPill = document.getElementById("statusPill");
  const viewProfileName = document.getElementById("viewProfileName");
  const viewProfileRange = document.getElementById("viewProfileRange");
  const viewTimeRemaining = document.getElementById("viewTimeRemaining");
  const viewTimeUsed = document.getElementById("viewTimeUsed");

  if (!currentState.isProtectionActive) {
    statusPill.textContent = "Paused";
    statusPill.className = "status-indicator paused";
  } else {
    statusPill.textContent = "Active";
    statusPill.className = "status-indicator";
  }

  const profileKey = (currentState.activeProfile || "junior").toUpperCase();
  const profileInfo = PROFILES[profileKey] || PROFILES.JUNIOR;

  viewProfileName.textContent = profileInfo.name;
  viewProfileRange.textContent = profileInfo.ageRange;

  const limitMinutes = currentState.dailyTimeLimitMinutes || 120;
  const usedMinutes = Math.floor((currentState.timeUsedTodaySeconds || 0) / 60);
  const remainingMinutes = Math.max(0, limitMinutes - usedMinutes);

  viewTimeRemaining.textContent = `${remainingMinutes}m left`;
  viewTimeUsed.textContent = `${usedMinutes}m of ${limitMinutes}m used`;
}

function renderParentView() {
  // Profile tab
  const selectProfile = document.getElementById("selectProfile");
  const inputTimeLimit = document.getElementById("inputTimeLimit");
  const btnToggleProtection = document.getElementById("btnToggleProtection");
  const reqCount = document.getElementById("reqCount");

  selectProfile.value = currentState.activeProfile || "junior";
  inputTimeLimit.value = currentState.dailyTimeLimitMinutes || 120;

  if (currentState.isProtectionActive) {
    btnToggleProtection.textContent = "Active";
    btnToggleProtection.className = "btn btn-toggle";
  } else {
    btnToggleProtection.textContent = "Paused";
    btnToggleProtection.className = "btn btn-toggle inactive";
  }

  // Requests tab
  const requests = currentState.pendingRequests || [];
  reqCount.textContent = requests.length;
  renderRequests(requests);

  // Rules tab
  renderRules();
}

function renderRequests(requests) {
  const container = document.getElementById("requestsList");
  container.innerHTML = "";

  if (requests.length === 0) {
    container.innerHTML = `<div class="empty-notice">No pending access requests.</div>`;
    return;
  }

  requests.forEach(req => {
    const item = document.createElement("div");
    item.className = "req-item";
    item.innerHTML = `
      <div class="req-header">${escapeHtml(req.domain || req.url)}</div>
      <div class="req-reason">"${escapeHtml(req.reason)}"</div>
      <div class="req-actions">
        <button class="btn btn-primary btn-sm btn-approve" data-id="${req.id}" data-domain="${req.domain}">Approve</button>
        <button class="btn btn-secondary btn-sm btn-deny" data-id="${req.id}">Deny</button>
      </div>
    `;
    container.appendChild(item);
  });

  // Attach request action listeners
  container.querySelectorAll(".btn-approve").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const domain = btn.dataset.domain;
      await chrome.runtime.sendMessage({ type: "APPROVE_REQUEST", requestId: id, domain });
      await loadStateAndRender();
    });
  });

  container.querySelectorAll(".btn-deny").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      await chrome.runtime.sendMessage({ type: "DENY_REQUEST", requestId: id });
      await loadStateAndRender();
    });
  });
}

function renderRules() {
  const allowContainer = document.getElementById("allowlistContainer");
  const blockContainer = document.getElementById("blocklistContainer");

  allowContainer.innerHTML = "";
  blockContainer.innerHTML = "";

  const allowlist = currentState.customAllowlist || [];
  const blocklist = currentState.customBlocklist || [];

  if (allowlist.length === 0) {
    allowContainer.innerHTML = `<span style="color:#94a3b8;font-size:11px;">No custom allowed domains.</span>`;
  } else {
    allowlist.forEach(domain => {
      const tag = createTag(domain, "allow");
      allowContainer.appendChild(tag);
    });
  }

  if (blocklist.length === 0) {
    blockContainer.innerHTML = `<span style="color:#94a3b8;font-size:11px;">No custom blocked domains.</span>`;
  } else {
    blocklist.forEach(domain => {
      const tag = createTag(domain, "block");
      blockContainer.appendChild(tag);
    });
  }
}

function createTag(domain, listType) {
  const span = document.createElement("span");
  span.className = "tag";
  span.innerHTML = `
    ${escapeHtml(domain)}
    <span class="tag-remove" data-domain="${domain}" data-type="${listType}">&times;</span>
  `;

  span.querySelector(".tag-remove").addEventListener("click", async (e) => {
    const targetDomain = e.target.dataset.domain;
    const targetType = e.target.dataset.type;
    await chrome.runtime.sendMessage({
      type: "REMOVE_CUSTOM_RULE",
      domain: targetDomain,
      listType: targetType
    });
    await loadStateAndRender();
  });

  return span;
}

function setupEventListeners() {
  const childView = document.getElementById("childView");
  const parentView = document.getElementById("parentView");
  const popupPinInput = document.getElementById("popupPinInput");
  const btnUnlockParent = document.getElementById("btnUnlockParent");
  const popupPinError = document.getElementById("popupPinError");
  const btnLockParent = document.getElementById("btnLockParent");

  // Unlock Parent controls
  btnUnlockParent.addEventListener("click", async () => {
    const pin = popupPinInput.value;
    popupPinError.classList.add("hidden");

    const resp = await chrome.runtime.sendMessage({ type: "VERIFY_PIN", pin });
    if (resp && resp.success) {
      childView.classList.add("hidden");
      parentView.classList.remove("hidden");
      popupPinInput.value = "";
    } else {
      popupPinError.classList.remove("hidden");
    }
  });

  // Lock back
  btnLockParent.addEventListener("click", () => {
    parentView.classList.add("hidden");
    childView.classList.remove("hidden");
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.dataset.tab;
      document.getElementById(targetId)?.classList.add("active");
    });
  });

  // Change Profile
  document.getElementById("selectProfile").addEventListener("change", async (e) => {
    await chrome.runtime.sendMessage({
      type: "UPDATE_PROFILE",
      profileKey: e.target.value
    });
    await loadStateAndRender();
  });

  // Save Time Limit
  document.getElementById("btnSaveTimeLimit").addEventListener("click", async () => {
    const val = document.getElementById("inputTimeLimit").value;
    await chrome.runtime.sendMessage({
      type: "SET_TIME_LIMIT",
      minutes: parseInt(val, 10)
    });
    await loadStateAndRender();
  });

  // Toggle Protection
  document.getElementById("btnToggleProtection").addEventListener("click", async () => {
    await chrome.runtime.sendMessage({ type: "TOGGLE_PROTECTION" });
    await loadStateAndRender();
  });

  // Reset Today's Time Counter
  document.getElementById("btnResetTimeToday").addEventListener("click", async () => {
    await chrome.runtime.sendMessage({ type: "RESET_TIME_TODAY" });
    await loadStateAndRender();
  });

  // Add Custom Rule
  document.getElementById("btnAddRule").addEventListener("click", async () => {
    const domainInput = document.getElementById("inputDomainRule");
    const ruleType = document.getElementById("selectRuleType").value;
    const domain = domainInput.value.trim();

    if (domain) {
      await chrome.runtime.sendMessage({
        type: "ADD_CUSTOM_RULE",
        domain,
        listType: ruleType
      });
      domainInput.value = "";
      await loadStateAndRender();
    }
  });

  // Change PIN
  document.getElementById("btnChangePin").addEventListener("click", async () => {
    const oldPin = document.getElementById("inputOldPin").value;
    const newPin = document.getElementById("inputNewPin").value;
    const errorEl = document.getElementById("pinChangeError");

    errorEl.classList.add("hidden");

    if (!newPin || newPin.length < 4) {
      errorEl.textContent = "New PIN must be at least 4 digits.";
      errorEl.classList.remove("hidden");
      return;
    }

    const resp = await chrome.runtime.sendMessage({
      type: "CHANGE_PIN",
      oldPin,
      newPin
    });

    if (resp && resp.success) {
      document.getElementById("inputOldPin").value = "";
      document.getElementById("inputNewPin").value = "";
      alert("Parent PIN updated successfully!");
    } else {
      errorEl.textContent = resp.error || "Failed to change PIN.";
      errorEl.classList.remove("hidden");
    }
  });
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
