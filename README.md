# KidSafe AI 🛡️
### An Agentic AI-Powered Parental Control Extension & Web Dashboard for Children

KidSafe AI is a cross-browser extension (Manifest V3) for standard web browsers (Google Chrome, Microsoft Edge, Brave) paired with a remote web dashboard for parents.

---

## 🚀 Phase 1: Extension Core & Interception (Complete)

- **Manifest V3 Architecture**: Background service worker, declarative rules, and content script.
- **Forced SafeSearch**: Enforced on Google, Bing, DuckDuckGo, and YouTube (Restricted Mode).
- **Three Age Profiles**: Little Explorer (5–8 yrs), Junior (9–12 yrs), and Teen (13–17 yrs).
- **Child-Friendly Block Page (`pages/block.html`)**: Friendly reasoning, "Ask Parent to Unlock" request button, and instant PIN unlock.
- **Parent Popup Panel (`pages/popup.html`)**: Real-time screen time badge, profile switcher, and 4-digit Parent PIN lock (default: `1234`).

---

## 🌐 Phase 2: Parent Control & Remote Dashboard (Complete)

- **Authentication & Multi-Child Profiles**: Secure parent registration/login via JWT and bcrypt; manage multiple children with individual limits.
- **6-Digit One-Time Device Pairing**: Temporary 6-digit codes to link extensions to child profiles without passwords.
- **Remote Policy Sync (`/api/sync`)**: Background loop syncs parent rule modifications and time allowances every 30 seconds.
- **Approval Workflow**: Unlock requests from children appear live on parent's dashboard; 1-click approvals automatically whitelist the domain.
- **Safety Logs**: Full activity tracking of blocked risks and browsing events.

---

## 🤖 Phase 3: AI Agent Integration (Complete)

- **Agentic Page Classifier (`/api/ai/classify`)**: Structured JSON (`allow` | `block` | `ask_parent`) with kid-friendly reasoning, confidence rating, and risk flag tags.
- **Natural-Language Parent Agent (`/api/ai/nl-rule/preview` & `/api/ai/nl-rule/confirm`)**: Plain-language commands (e.g. *"Allow scratch.mit.edu and set daily screen time to 90 minutes"*) with a mandatory confirmation preview.
- **AI Dashboard Assistant & Inspector**: Interactive AI Command Bar and URL test lab in the Parent Dashboard.

---

## 🔒 Phase 4: Hardening & Quantitative Evaluation (Complete)

- **Anti-Bypass & Internal Settings Protection (`FR-B9`)**: Blocks unauthorized navigation to `chrome://extensions` and browser settings, redirecting to a protected screen.
- **Incognito Enforcement (`FR-B6`)**: Enforces safety policies inside Private/Incognito windows or locks Incognito entirely.
- **Windows Enterprise Group Policies (`hardening/`)**:
  - `chrome_hardening.reg`: Windows registry policy that forces installation, locks extension uninstallation, and disables DevTools.
  - `edge_hardening.reg`: Microsoft Edge policy locking InPrivate and extension management.
  - `HARDENING_GUIDE.md`: Comprehensive threat model matrix and bypass defense analysis.
- **Academic Benchmark & Evaluation Report (`evaluation/`)**:
  - `dataset.json`: 20-sample diverse test benchmark across Safe Learning, Entertainment, Social Media, Adult, Gambling, and Violent categories.
  - `benchmark.py`: Measures accuracy, precision, recall, F1-score, and latency distribution.
  - `EVALUATION_REPORT.md`: Pre-formatted evaluation chapter with confusion matrices and performance tables ready for the final BCA dissertation.
- **Activity Log CSV Export (`/api/profiles/{id}/logs/export.csv`)**: One-click export of navigation logs for parental offline records.

---

## 💻 Running the Full System

1. **Start the FastAPI Backend**:
   ```powershell
   cd C:\CHILDSAFE\backend
   python -m uvicorn main:app --reload --port 8000
   ```
2. **Open the Parent Dashboard**:
   - Visit: `http://localhost:8000`
   - Log in or create a parent account.
   - Use the **AI Assistant** tab or command bar to set rules via natural language!
   - Export activity logs via **Export CSV Report**.
3. **Load the Extension**:
   - Open Chrome/Edge/Brave &rarr; `chrome://extensions` &rarr; Developer mode &rarr; **Load unpacked** &rarr; select `C:\CHILDSAFE\extension`.
   - Pair with the 6-digit code from the dashboard.

---

## 🧪 Comprehensive Automated Test Suites

```powershell
# Phase 1: Extension Core & Policy Pipeline
node tests/test_extension_core.js

# Phase 2: Backend, JWT Auth, Pairing & Sync
python tests/test_phase2_backend.py

# Phase 3: AI Classifier Agent & Natural Language Parent Agent
python tests/test_phase3_ai.py

# Phase 4: Hardening, Benchmark Dataset & CSV Export
python tests/test_phase4_hardening.py

# Run Model Benchmark
python evaluation/benchmark.py
```
*(All 4 phases pass 100%).*
