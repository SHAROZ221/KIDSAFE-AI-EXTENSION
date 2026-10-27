# Product Requirements Document (PRD)
## KidSafe AI Extension: An Agentic AI-Powered Parental Control Extension & Web Dashboard for Children

| Field | Detail |
| :--- | :--- |
| **Document version** | 1.0 (Draft) |
| **Date** | 25 October 2026 |
| **Author** | Sharoz |
| **Project type** | Final-year BCA project (solo) |
| **Institution** | Khandelwal College of Management Science and Technology (KCMT), Bareilly, affiliated with MJPRU |
| **Target completion** | June 2027 (buffer until September 2027 graduation) |
| **Status** | Draft, pending guide/supervisor review |

> **Working title:** "KidSafe AI Extension". *Alternatives:* SafeSurf Extension, LittleLens Extension, GuardianWeb Extension.

---

## 1. Executive Summary
**KidSafe AI Extension** is a cross-browser extension (Manifest V3) for standard web browsers (Google Chrome, Microsoft Edge, Brave) paired with a remote web dashboard for parents. Unlike conventional filters that rely only on static blocklists, it uses an LLM-powered agent to analyse web pages and navigation requests in real time, decide whether they are appropriate for the child's age, explain decisions in simple language, and let parents manage rules through natural-language commands.

The system consists of three main parts:
1. **Child Extension (Browser Extension / Extension Shell):** Plugs into existing desktop browsers, enforces web request policies, intercepts requests, blocks unsafe pages, and manages strict lockouts.
2. **Backend Service:** Authentication, policy rules, sync, AI agent orchestration, logging, and request evaluation.
3. **Parent Dashboard (Web App):** Remote web management panel for profiles, content rules, schedules, approvals, and reports from any device.

---

## 2. Problem Statement
- Children encounter inappropriate content (adult, violent, gambling, scams, self-harm content) through standard browsers, search results, and embedded ads.
- Static blocklists miss new, obscure, or mixed-content pages, while over-blocking educational content.
- Traditional full-browser apps require replacing the default browser entirely, whereas extensions work directly on the browsers families already use.
- Parents lack simple, natural-language interfaces for setting rules and reviewing plain-language summaries.
- Children receive opaque "Access denied" errors with no context or way to request access.

---

## 3. Goals and Non-Goals

### 3.1 Goals
| ID | Goal |
| :--- | :--- |
| **G1** | Provide a browser extension that intercepts and filters web navigation with high recall and low false positives for a selected child age profile. |
| **G2** | Use an LLM agent as a decision layer for unclassified pages, yielding structured, explainable verdicts. |
| **G3** | Offer parents full remote control over profiles, schedules, time limits, approvals, and activity reports via a web dashboard. |
| **G4** | Support natural-language rule adjustments for parents with a mandatory confirmation preview step. |
| **G5** | Ensure data minimisation and protect privacy during LLM evaluation. |
| **G6** | Document resistance against realistic extension bypass attempts (e.g., disabling extension, Incognito mode, Developer mode). |
| **G7** | Produce a measured evaluation chapter covering classifier accuracy, latency, and cost for the final report. |

### 3.2 Non-Goals (v1)
- Filtering system-wide network traffic or non-browser desktop apps.
- Mobile extension builds (Safari iOS / Firefox Android) in initial release.
- Image/video content moderation at scale (text/metadata classification in v1; image checks as stretch goal).
- Guaranteeing 100% bypass prevention (extension policies can be bypassed by local device administrators).
- Multi-tenant SaaS scaling or monetisation.

---

## 4. Target Users and Personas
- **Parent / Guardian ("Meera", 38):** Wants quick remote controls and plain-language summaries without configuring complex extension settings.
- **Child ("Aarav", 9; "Zoya", 14):** Wants to browse naturally on familiar browsers with friendly explanations on blocked pages and request buttons.
- **Evaluator / Guide:** Looks for clear technical design, Manifest V3 compliance, bypass research, and an evaluation dataset.

### 4.1 Age Profiles
| Profile | Age | Default Mode | Default Strictness |
| :--- | :--- | :--- | :--- |
| **Little Explorer** | 5–8 | Allowlist only | Very strict |
| **Junior** | 9–12 | Allowlist + AI-approved categories | Strict |
| **Teen** | 13–17 | Blocklist + AI classification | Moderate |

---

## 5. Scope and Phasing

| Phase | Name | Contents |
| :--- | :--- | :--- |
| **Phase 1** | Extension Core & Interception | Manifest V3 Extension background worker, `declarativeNetRequest` / `webNavigation` hooks, local policy rules, force SafeSearch, custom block overlay/page. |
| **Phase 2** | Parent Control & Remote Dashboard | FastAPI backend, web dashboard, time limits, approval request workflow, device pairing token, sync engine. |
| **Phase 3** | AI Agent Integration | LLM page classifier (URL/DOM text extraction), age-aware policies, kid-friendly explainer, natural-language parent agent. |
| **Phase 4** | Extension Hardening & Evaluation | Resistance testing (Incognito block, enterprise management policies, PIN lock), evaluation dataset, evaluation report. |
| **Stretch** | Extensions Extras | WhatsApp/Telegram alerts, image classification stretch goal, multi-language support. |

---

## 6. Functional Requirements

### 6.1 Extension Engine (Child Side)
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-B1** | Built using Browser Extension API (Manifest V3) compatible with Chrome, Edge, and Brave. | **P0** |
| **FR-B2** | Intercept web requests using `chrome.declarativeNetRequest` or `chrome.webNavigation` before content rendering. | **P0** |
| **FR-B3** | Redirect blocked requests to an extension-hosted block page (`block.html`) with age-appropriate reasoning and an "Ask Parent" button. | **P0** |
| **FR-B4** | Enforce forced SafeSearch query parameters on Google, Bing, DuckDuckGo, and YouTube via request header/parameter modification rules. | **P0** |
| **FR-B5** | Require Parent PIN inside extension popup to modify settings, pause protection, or unpair device. | **P0** |
| **FR-B6** | Detect Incognito/Private mode execution and enforce extension permission in Incognito or block navigation in Incognito windows. | **P0** |
| **FR-B7** | Enforce fallback behavior (strict offline cache policies) when the backend server is unreachable. | **P0** |
| **FR-B8** | Show time-remaining badge on the extension action icon and display lock overlay when time expires. | **P1** |
| **FR-B9** | Restrict access to `chrome://extensions` / `edge://extensions` settings page using DOM redirection injection or parent warnings where possible. | **P1** |

### 6.2 Authentication and Pairing
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-A1** | Parent registers/logs into Dashboard via email, password (hashed with argon2/bcrypt), and session handling. | **P0** |
| **FR-A2** | One-time pairing code links an installed browser extension to a parent account and specific child profile. | **P0** |
| **FR-A3** | Parent local PIN configured during extension setup to lock internal extension options. | **P0** |

### 6.3 Content Filtering Engine
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-F1** | Domain allowlist and blocklist enforcement directly within background Service Worker. | **P0** |
| **FR-F2** | Evaluation order: (1) Parent Overrides → (2) Extension Local Cache → (3) Static Category Lists → (4) AI Classifier Endpoint. | **P0** |
| **FR-F3** | Content scripts sanitise and extract page meta description/DOM text for unknown pages to send to classifier. | **P0** |
| **FR-F4** | In-memory and `chrome.storage.local` verdict caching to minimise network calls and LLM latency. | **P0** |

### 6.4 Requests, Time Management & Dashboard
- Real-time approval requests from the block page.
- Screen-time daily limits and hourly schedules per child profile.
- Automated activity logs and aggregated usage reports.
- Natural-language rule management agent with confirmation previews.

---

## 7. AI and Agent Requirements

### 7.1 Page Classifier Agent
- **Purpose:** Decides whether an unknown page is appropriate for the child's age profile.
- **Inputs:** URL, domain, title, meta description, extracted visible text (truncated), child age profile, category settings.
- **Output Schema:**
```jso
{
  "verdict": "allow | block | ask_parent",
  "confidence": 0.0,
  "categories": ["education", "gaming"],
  "age_rating": "5+ | 9+ | 13+ | 18+",
  "reason_parent": "technical explanation for the parent",
  "reason_child": "simple, friendly explanation for the child",
  "risk_flags": ["adult", "violence", "gambling", "scam", "self_harm", "other"]
}