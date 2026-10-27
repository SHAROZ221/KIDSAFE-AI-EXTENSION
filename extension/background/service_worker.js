// KidSafe AI Extension - Background Service Worker (Manifest V3)
import { PROFILES, DEFAULT_STATE } from "../utils/constants.js";
import { evaluateUrlPolicy, extractHostname, hashPin, getStorageState, setStorageState } from "../utils/helpers.js";

// Initialize on install or startup
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log("[KidSafe AI] Extension installed/updated:", details.reason);
  const state = await getStorageState();
  await setStorageState(state);
  setupAlarms();
  updateBadge(state);
});

chrome.runtime.onStartup.addListener(async () => {
  const state = await getStorageState();
  setupAlarms();
  updateBadge(state);
});

// Configure periodic alarms for time tracking and daily resets
function setupAlarms() {
  chrome.alarms.get("screenTimeTracker", (alarm) => {
    if (!alarm) {
      chrome.alarms.create("screenTimeTracker", { periodInMinutes: 1 });
    }
  });
}

// Alarm listener
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "screenTimeTracker") {
    await handleScreenTimeTick();
  }
});

// Handle 1-minute time ticks
async function handleScreenTimeTick() {
  const state = await getStorageState();
  const today = new Date().toISOString().slice(0, 10);

  // Check if day has rolled over
  if (state.lastActiveDate !== today) {
    state.timeUsedTodaySeconds = 0;
    state.lastActiveDate = today;
  }

  // Only track time if protection is active and windows are focused/open
  if (state.isProtectionActive) {
    const windows = await chrome.windows.getAll({ populate: false });
    const hasActiveWindow = windows.some(w => w.focused || w.state !== "minimized");

    if (hasActiveWindow) {
      state.timeUsedTodaySeconds += 60;
    }
  }

  await setStorageState({
    timeUsedTodaySeconds: state.timeUsedTodaySeconds,
    lastActiveDate: state.lastActiveDate
  });

  updateBadge(state);

  // If time limit is exceeded, notify active tabs
  const limitMinutes = state.dailyTimeLimitMinutes || 120;
  if (state.timeUsedTodaySeconds >= limitMinutes * 60) {
    lockdownExpiredTabs();
  }
}

// Update icon badge with remaining time
function updateBadge(state) {
  if (!state.isProtectionActive) {
    chrome.action.setBadgeText({ text: "PAUSE" });
    chrome.action.setBadgeBackgroundColor({ color: "#9E9E9E" });
    return;
  }

  const limitMinutes = state.dailyTimeLimitMinutes || 120;
  const usedMinutes = Math.floor(state.timeUsedTodaySeconds / 60);
  const remainingMinutes = Math.max(0, limitMinutes - usedMinutes);

  if (remainingMinutes === 0) {
    chrome.action.setBadgeText({ text: "LOCK" });
    chrome.action.setBadgeBackgroundColor({ color: "#D32F2F" });
  } else if (remainingMinutes <= 15) {
    chrome.action.setBadgeText({ text: `${remainingMinutes}m` });
    chrome.action.setBadgeBackgroundColor({ color: "#F57C00" });
  } else {
    chrome.action.setBadgeText({ text: `${remainingMinutes}m` });
    chrome.action.setBadgeBackgroundColor({ color: "#388E3C" });
  }
}

// Broadcast lockdown message to all tabs when time runs out
async function lockdownExpiredTabs() {
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith("chrome://") && !tab.url.includes("block.html")) {
      const blockUrl = chrome.runtime.getURL(
        `pages/block.html?reason=time_limit_reached&url=${encodeURIComponent(tab.url)}`
      );
      chrome.tabs.update(tab.id, { url: blockUrl }).catch(() => {});
    }
  }
}

// Navigation Interceptor
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  // Only intercept top-level navigation in the main frame
  if (details.frameId !== 0) return;

  const url = details.url;
  // Ignore blank, extension pages, and browser internals
  if (!url || url.startsWith("chrome://") || url.startsWith("edge://") || 
      url.startsWith("brave://") || url.startsWith("chrome-extension://") || 
      url.startsWith("about:")) {
    return;
  }

  const state = await getStorageState();

  // If protection is disabled by parent, allow navigation
  if (!state.isProtectionActive) return;

  // Check Incognito restriction (FR-B6)
  const tab = await chrome.tabs.get(details.tabId).catch(() => null);
  if (tab && tab.incognito && state.blockIncognitoNavigation) {
    const blockUrl = chrome.runtime.getURL(
      `pages/block.html?reason=incognito_blocked&url=${encodeURIComponent(url)}`
    );
    chrome.tabs.update(details.tabId, { url: blockUrl });
    return;
  }

  // Check if daily time limit reached (FR-B8)
  const limitMinutes = state.dailyTimeLimitMinutes || 120;
  if (state.timeUsedTodaySeconds >= limitMinutes * 60) {
    const blockUrl = chrome.runtime.getURL(
      `pages/block.html?reason=time_limit_reached&url=${encodeURIComponent(url)}`
    );
    chrome.tabs.update(details.tabId, { url: blockUrl });
    return;
  }

  // Evaluate URL against policy pipeline (FR-F1, FR-F2)
  const evaluation = await evaluateUrlPolicy(url, state);

  if (evaluation.verdict === "block") {
    console.log(`[KidSafe AI] Blocked: ${url} (Reason: ${evaluation.reason})`);
    const blockUrl = chrome.runtime.getURL(
      `pages/block.html?url=${encodeURIComponent(url)}&reason=${encodeURIComponent(evaluation.reason || "blocked")}&explanation=${encodeURIComponent(evaluation.explanation || "")}&profile=${encodeURIComponent(state.activeProfile)}`
    );
    chrome.tabs.update(details.tabId, { url: blockUrl });
  }
});

// Message dispatch handler for popup, content scripts, and block page
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleRuntimeMessage(message, sender).then(sendResponse);
  return true; // Keep channel open for async response
});

async function handleRuntimeMessage(message, sender) {
  const state = await getStorageState();

  switch (message.type) {
    case "GET_STATE":
      return { success: true, state };

    case "VERIFY_PIN": {
      const inputHash = await hashPin(message.pin || "");
      const isValid = inputHash === state.parentPinHash;
      return { success: isValid };
    }

    case "CHANGE_PIN": {
      const oldHash = await hashPin(message.oldPin || "");
      if (oldHash !== state.parentPinHash) {
        return { success: false, error: "Incorrect current PIN." };
      }
      const newHash = await hashPin(message.newPin || "");
      await setStorageState({ parentPinHash: newHash });
      return { success: true };
    }

    case "UPDATE_PROFILE": {
      if (PROFILES[message.profileKey?.toUpperCase()]) {
        const newProfile = message.profileKey.toLowerCase();
        await setStorageState({ activeProfile: newProfile });
        return { success: true, activeProfile: newProfile };
      }
      return { success: false, error: "Invalid profile key." };
    }

    case "TOGGLE_PROTECTION": {
      const newStatus = !state.isProtectionActive;
      await setStorageState({ isProtectionActive: newStatus });
      updateBadge({ ...state, isProtectionActive: newStatus });
      return { success: true, isProtectionActive: newStatus };
    }

    case "ADD_CUSTOM_RULE": {
      const { domain, listType } = message; // 'allow' or 'block'
      const cleanDomain = extractHostname(`http://${domain}`) || domain.trim().toLowerCase();
      if (!cleanDomain) return { success: false, error: "Invalid domain." };

      if (listType === "allow") {
        const customAllowlist = Array.from(new Set([...(state.customAllowlist || []), cleanDomain]));
        // remove from blocklist if exists
        const customBlocklist = (state.customBlocklist || []).filter(d => d !== cleanDomain);
        await setStorageState({ customAllowlist, customBlocklist });
      } else {
        const customBlocklist = Array.from(new Set([...(state.customBlocklist || []), cleanDomain]));
        const customAllowlist = (state.customAllowlist || []).filter(d => d !== cleanDomain);
        await setStorageState({ customAllowlist, customBlocklist });
      }
      return { success: true };
    }

    case "REMOVE_CUSTOM_RULE": {
      const { domain, listType } = message;
      if (listType === "allow") {
        const customAllowlist = (state.customAllowlist || []).filter(d => d !== domain);
        await setStorageState({ customAllowlist });
      } else {
        const customBlocklist = (state.customBlocklist || []).filter(d => d !== domain);
        await setStorageState({ customBlocklist });
      }
      return { success: true };
    }

    case "SUBMIT_ACCESS_REQUEST": {
      const { url, reason } = message;
      const hostname = extractHostname(url);
      const newRequest = {
        id: "req_" + Date.now(),
        url,
        domain: hostname,
        reason: reason || "I need this website for school / study.",
        requestedAt: new Date().toISOString(),
        status: "pending"
      };

      const pendingRequests = [newRequest, ...(state.pendingRequests || [])].slice(0, 50);
      await setStorageState({ pendingRequests });
      return { success: true, request: newRequest };
    }

    case "APPROVE_REQUEST": {
      const { requestId, domain } = message;
      const pendingRequests = (state.pendingRequests || []).filter(r => r.id !== requestId);
      const customAllowlist = Array.from(new Set([...(state.customAllowlist || []), domain]));
      await setStorageState({ pendingRequests, customAllowlist });
      return { success: true };
    }

    case "DENY_REQUEST": {
      const { requestId } = message;
      const pendingRequests = (state.pendingRequests || []).filter(r => r.id !== requestId);
      await setStorageState({ pendingRequests });
      return { success: true };
    }

    case "SET_TIME_LIMIT": {
      const minutes = parseInt(message.minutes, 10);
      if (isNaN(minutes) || minutes < 0) return { success: false, error: "Invalid minutes" };
      await setStorageState({ dailyTimeLimitMinutes: minutes });
      updateBadge({ ...state, dailyTimeLimitMinutes: minutes });
      return { success: true, dailyTimeLimitMinutes: minutes };
    }

    case "RESET_TIME_TODAY": {
      await setStorageState({ timeUsedTodaySeconds: 0 });
      updateBadge({ ...state, timeUsedTodaySeconds: 0 });
      return { success: true };
    }

    default:
      return { success: false, error: "Unknown message action" };
  }
}
