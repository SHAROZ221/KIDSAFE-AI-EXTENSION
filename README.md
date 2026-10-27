# KidSafe AI 🛡️
### An Agentic AI-Powered Parental Control Extension & Web Dashboard for Children

KidSafe AI is a cross-browser extension (Manifest V3) for standard web browsers (Google Chrome, Microsoft Edge, Brave) paired with a remote web dashboard for parents.

---

## 🚀 Phase 1: Extension Core & Interception (Complete)

Phase 1 provides the core browser extension shell and real-time request filtering engine.

### Features Implemented
- **Manifest V3 Architecture**: Clean background service worker and content scripts compliant with modern Chromium standards.
- **DeclarativeNetRequest Rules**: Forced SafeSearch enforced automatically on **Google**, **Bing**, **DuckDuckGo**, and **YouTube** (Restricted Mode).
- **Navigation Interception Engine**: Evaluates web traffic in real time against policy layers before rendering.
- **Three Age Profiles**:
  - **Little Explorer (5–8 yrs)**: Strict allowlist only (e.g., PBS Kids, National Geographic Kids, Scratch, Khan Academy).
  - **Junior (9–12 yrs)**: Hybrid allowlist + safe categories; restricts adult, gambling, and violent content.
  - **Teen (13–17 yrs)**: Blocklist + AI classification; allows broader exploration while protecting against harmful content.
- **Kid-Friendly Block Page (`pages/block.html`)**:
  - Reassuring, age-appropriate explanations instead of harsh error messages.
  - Interactive **"Ask Parent to Unlock"** button allowing children to send an access request with a personal note.
  - **On-the-spot Parent PIN unlock** so a parent present with the child can instantly review and whitelist a site.
- **Parent-Locked Popup Controller (`pages/popup.html`)**:
  - Glance view for the child: active profile, screen time left today, protection status.
  - Protected by a **4-digit Parent PIN** (default: `1234`).
  - Parent panel for profile switching, daily time limits, approving pending requests, and custom allow/block rules.
- **Screen Time Manager**:
  - Real-time time remaining badge on extension icon.
  - Automatically redirects tabs to a timeout page when the daily allowance expires.

---

## 🛠️ How to Load the Extension in Chrome / Edge / Brave

1. Open your browser and navigate to:
   - **Chrome**: `chrome://extensions`
   - **Edge**: `edge://extensions`
   - **Brave**: `brave://extensions`
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked**.
4. Select the folder: `C:\CHILDSAFE\extension`.
5. The **KidSafe AI** icon will appear in your browser toolbar!

---

## 🧪 Testing Phase 1 Core

To run the automated verification test suite:
```powershell
node tests/test_extension_core.js
```
*(All 16 unit tests for manifest compliance, SafeSearch, PIN hashing, profile logic, and parent overrides pass).*

---

## 🔮 Next: Phase 2
- **Backend Service (FastAPI)**: Authentication, pairing tokens, REST endpoints for approval requests and remote policy sync.
- **Parent Web Dashboard**: Remote browser panel for parents to manage multiple child devices from any phone or laptop.
