// KidSafe AI - Utility Functions and Policy Evaluator
import { PROFILES, DEFAULT_ALLOWLIST, DEFAULT_BLOCKLIST, RISK_KEYWORD_RULES, DEFAULT_STATE } from "./constants.js";

/**
 * Computes SHA-256 hash string for PIN verification.
 */
export async function hashPin(pin) {
  const encoder = new TextEncoder();
  const data = encoder.encode(pin.trim());
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Extracts clean hostname from URL string.
 */
export function extractHostname(urlString) {
  try {
    const url = new URL(urlString);
    return url.hostname.toLowerCase();
  } catch {
    return "";
  }
}

/**
 * Checks if a hostname matches a target domain or its subdomains.
 */
export function isDomainMatch(hostname, targetDomain) {
  if (!hostname || !targetDomain) return false;
  const cleanTarget = targetDomain.trim().toLowerCase().replace(/^www\./, "");
  const cleanHost = hostname.trim().toLowerCase().replace(/^www\./, "");
  return cleanHost === cleanTarget || cleanHost.endsWith("." + cleanTarget);
}

/**
 * Evaluates whether a domain or keyword is safe based on KidSafe policy pipeline.
 * Order:
 * 1. Parent Overrides (Custom Allowlist / Custom Blocklist)
 * 2. Extension Local Verdict Cache
 * 3. Static Profile Rules & Default Category Lists
 * 4. Fallback Heuristics
 */
export async function evaluateUrlPolicy(url, state) {
  const hostname = extractHostname(url);
  const urlLower = url.toLowerCase();

  // Always ignore internal extension or browser protocols
  if (!url || url.startsWith("chrome://") || url.startsWith("edge://") || 
      url.startsWith("brave://") || url.startsWith("chrome-extension://") || 
      url.startsWith("about:") || url.startsWith("view-source:")) {
    return { verdict: "allow", reason: "internal_system_page" };
  }

  // 1. Check Parent Custom Whitelist
  if (state.customAllowlist && state.customAllowlist.some(d => isDomainMatch(hostname, d))) {
    return {
      verdict: "allow",
      reason: "parent_approved",
      explanation: "Approved by your parent."
    };
  }

  // 2. Check Parent Custom Blacklist
  if (state.customBlocklist && state.customBlocklist.some(d => isDomainMatch(hostname, d))) {
    return {
      verdict: "block",
      reason: "parent_blocked",
      explanation: "This website has been specifically restricted by your parent.",
      category: "custom_block"
    };
  }

  // 3. Check Local Verdict Cache
  if (state.verdictCache && state.verdictCache[hostname]) {
    const cached = state.verdictCache[hostname];
    // Cache valid for 24 hours
    if (Date.now() - (cached.timestamp || 0) < 24 * 60 * 60 * 1000) {
      return cached;
    }
  }

  // 4. Default Static Blocklist check
  if (DEFAULT_BLOCKLIST.some(d => isDomainMatch(hostname, d))) {
    return {
      verdict: "block",
      reason: "static_blocklist",
      explanation: "This website contains mature or unsafe content not suitable for your age.",
      category: "restricted"
    };
  }

  // Keyword check in URL/domain
  for (const [category, keywords] of Object.entries(RISK_KEYWORD_RULES)) {
    for (const kw of keywords) {
      if (hostname.includes(kw) || urlLower.includes(kw)) {
        return {
          verdict: "block",
          reason: `keyword_${category}`,
          explanation: `KidSafe detected high-risk ${category} keywords in this web address.`,
          category: category
        };
      }
    }
  }

  // 5. Profile-specific handling
  const profileKey = (state.activeProfile || "junior").toUpperCase();
  const profile = PROFILES[profileKey] || PROFILES.JUNIOR;

  // Profile: Little Explorer (5-8) - strict allowlist only
  if (profile.mode === "allowlist_only") {
    const isAllowed = DEFAULT_ALLOWLIST.some(d => isDomainMatch(hostname, d));
    if (!isAllowed) {
      return {
        verdict: "block",
        reason: "allowlist_only_enforced",
        explanation: "Little Explorer mode is active. Only pre-approved child-friendly websites can be opened.",
        category: "unapproved_site"
      };
    }
    return { verdict: "allow", reason: "default_allowlist" };
  }

  // Profile: Junior (9-12) - allowlist + safe categories
  if (profile.mode === "hybrid") {
    // If it's on the default allowlist, allow immediately
    if (DEFAULT_ALLOWLIST.some(d => isDomainMatch(hostname, d))) {
      return { verdict: "allow", reason: "default_allowlist" };
    }
    // Popular safe search engines
    if (isDomainMatch(hostname, "google.com") || 
        isDomainMatch(hostname, "bing.com") || 
        isDomainMatch(hostname, "duckduckgo.com") ||
        isDomainMatch(hostname, "youtube.com")) {
      return { verdict: "allow", reason: "search_engine_safesearch" };
    }
  }

  // Default fallback for safe web navigation
  return {
    verdict: "allow",
    reason: "default_pass",
    explanation: "Content passed standard safety checks."
  };
}

/**
 * Storage helpers
 */
export async function getStorageState() {
  return new Promise((resolve) => {
    chrome.storage.local.get(null, (data) => {
      resolve({ ...DEFAULT_STATE, ...data });
    });
  });
}

export async function setStorageState(updates) {
  return new Promise((resolve) => {
    chrome.storage.local.set(updates, () => {
      resolve(true);
    });
  });
}
