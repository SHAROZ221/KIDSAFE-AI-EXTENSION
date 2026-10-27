// KidSafe AI - Block Page Client Controller
import { extractHostname } from "../utils/helpers.js";

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const targetUrl = urlParams.get("url") || "";
  const reason = urlParams.get("reason") || "content_filtered";
  const customExplanation = urlParams.get("explanation") || "";
  const profile = urlParams.get("profile") || "junior";

  const blockedUrlEl = document.getElementById("blockedUrl");
  const blockReasonEl = document.getElementById("blockReason");
  const activeProfileEl = document.getElementById("activeProfile");
  const friendlyExplanationEl = document.getElementById("friendlyExplanation");
  const titleTextEl = document.getElementById("titleText");

  const btnAskParent = document.getElementById("btnAskParent");
  const btnGoBack = document.getElementById("btnGoBack");
  const requestForm = document.getElementById("requestForm");
  const btnSendRequest = document.getElementById("btnSendRequest");
  const btnCancelRequest = document.getElementById("btnCancelRequest");
  const requestSuccess = document.getElementById("requestSuccess");
  const requestReasonInput = document.getElementById("requestReason");

  const btnParentToggle = document.getElementById("btnParentToggle");
  const parentPanel = document.getElementById("parentPanel");
  const parentPinInput = document.getElementById("parentPinInput");
  const btnConfirmUnlock = document.getElementById("btnConfirmUnlock");
  const pinError = document.getElementById("pinError");

  // Populate UI
  const hostname = extractHostname(targetUrl) || targetUrl;
  blockedUrlEl.textContent = hostname || "Unknown URL";
  activeProfileEl.textContent = formatProfileName(profile);

  // Customize based on reason
  if (reason === "time_limit_reached") {
    titleTextEl.textContent = "Screen Time is Up for Today!";
    friendlyExplanationEl.textContent = "Great job today! You have reached your daily browsing limit. Time to step away and relax or study offline.";
    blockReasonEl.textContent = "Daily Limit Reached";
    btnAskParent.textContent = "Ask for Extra Time";
  } else if (reason === "incognito_blocked") {
    titleTextEl.textContent = "Incognito Mode is Protected";
    friendlyExplanationEl.textContent = "Private or Incognito browsing is disabled by KidSafe AI to keep your online experience safe.";
    blockReasonEl.textContent = "Incognito Mode Blocked";
  } else if (customExplanation) {
    friendlyExplanationEl.textContent = customExplanation;
    blockReasonEl.textContent = formatReason(reason);
  } else {
    blockReasonEl.textContent = formatReason(reason);
  }

  // Go Back button
  btnGoBack.addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = "https://kiddle.co";
    }
  });

  // Reveal Ask Parent form
  btnAskParent.addEventListener("click", () => {
    requestForm.classList.remove("hidden");
    requestForm.scrollIntoView({ behavior: "smooth" });
  });

  // Cancel Request
  btnCancelRequest.addEventListener("click", () => {
    requestForm.classList.add("hidden");
  });

  // Send Request
  btnSendRequest.addEventListener("click", async () => {
    const note = requestReasonInput.value.trim();
    btnSendRequest.disabled = true;
    btnSendRequest.textContent = "Sending...";

    try {
      const response = await chrome.runtime.sendMessage({
        type: "SUBMIT_ACCESS_REQUEST",
        url: targetUrl,
        reason: note
      });

      if (response && response.success) {
        requestForm.classList.add("hidden");
        requestSuccess.classList.remove("hidden");
      }
    } catch (err) {
      console.error("Failed to submit request:", err);
    } finally {
      btnSendRequest.disabled = false;
      btnSendRequest.textContent = "Send Request";
    }
  });

  // Toggle Parent Unlock accordion
  btnParentToggle.addEventListener("click", () => {
    parentPanel.classList.toggle("hidden");
    if (!parentPanel.classList.contains("hidden")) {
      parentPinInput.focus();
    }
  });

  // Parent PIN unlock
  btnConfirmUnlock.addEventListener("click", async () => {
    const pin = parentPinInput.value;
    pinError.classList.add("hidden");

    if (!pin) {
      pinError.textContent = "Please enter parent PIN.";
      pinError.classList.remove("hidden");
      return;
    }

    const verifyResp = await chrome.runtime.sendMessage({
      type: "VERIFY_PIN",
      pin
    });

    if (verifyResp && verifyResp.success) {
      // Add domain to custom allowlist
      await chrome.runtime.sendMessage({
        type: "ADD_CUSTOM_RULE",
        domain: hostname,
        listType: "allow"
      });

      // Redirect back to target URL
      if (targetUrl) {
        window.location.href = targetUrl;
      }
    } else {
      pinError.textContent = "Incorrect PIN. Please try again.";
      pinError.classList.remove("hidden");
    }
  });
});

function formatReason(reason) {
  return reason
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

function formatProfileName(key) {
  const map = {
    little_explorer: "Little Explorer (5–8)",
    junior: "Junior (9–12)",
    teen: "Teen (13–17)"
  };
  return map[key.toLowerCase()] || "Protected";
}
