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

Phase 3 brings the core differentiator of KidSafe AI: intelligent agentic decision layers and natural-language interfaces.

### Key Capabilities
1. **Agentic Page Classifier (`/api/ai/classify`)**:
   - Evaluates unknown web pages in real time using LLM inference (Google Gemini / Groq / OpenAI) with deterministic semantic taxonomy fallback.
   - Outputs structured JSON matching **PRD Section 7.1**:
     - `verdict`: `allow` | `block` | `ask_parent`
     - `confidence`: (0.0 to 1.0)
     - `categories`: `["education", "coding", ...]`
     - `age_rating`: `5+` | `9+` | `13+` | `18+`
     - `reason_parent`: Concise technical explanation for parents.
     - `reason_child`: Friendly, supportive, non-frightening explanation for children.
     - `risk_flags`: High-risk categories (`adult`, `gambling`, `violence`, `weapons_drugs`, `scam`, etc.).
   - Built-in 24-hour TTL verdict caching to ensure zero latency on repeated visits.
2. **Natural-Language Parent Agent (`/api/ai/nl-rule/preview` & `/api/ai/nl-rule/confirm`)**:
   - Parents can speak or type commands in plain English:
     - *"Allow scratch.mit.edu and set daily screen time to 90 minutes"*
     - *"Block twitch and discord for Aarav"*
     - *"Switch to Little Explorer mode"*
     - *"Pause protection"*
   - **Mandatory Confirmation Preview**: The agent parses the sentence into structured actions, presents a preview card, and executes changes only upon parent confirmation.
3. **AI Dashboard Assistant & Inspector**:
   - Interactive AI Command Bar directly on the Parent Dashboard overview.
   - Dedicated **AI Agent Assistant** tab with instant prompt chips.
   - **AI Page Classifier Test Lab**: Lets parents inspect and preview how the classifier categorizes any website for their child's profile.

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
3. **Load the Extension**:
   - Open Chrome/Edge/Brave &rarr; `chrome://extensions` &rarr; Developer mode &rarr; **Load unpacked** &rarr; select `C:\CHILDSAFE\extension`.
   - Pair with the 6-digit code from the dashboard.

---

## 🧪 Comprehensive Automated Test Suites

Run all three test suites:
```powershell
# Phase 1: Extension Core & Policy Pipeline
node tests/test_extension_core.js

# Phase 2: Backend, JWT Auth, Pairing & Sync
python tests/test_phase2_backend.py

# Phase 3: AI Classifier Agent & Natural Language Parent Agent
python tests/test_phase3_ai.py
```

---

## 🔮 Next: Phase 4
- **Extension Hardening & Evaluation**:
  - Bypass resistance testing (Incognito lockout enforcement, enterprise policies).
  - Accuracy, latency, and classifier benchmark dataset.
