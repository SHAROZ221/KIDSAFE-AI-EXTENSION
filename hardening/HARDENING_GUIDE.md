# KidSafe AI - Hardening & Bypass Resistance Report
### Final Year BCA Project (Phase 4 Deliverable)

---

## 1. Threat Model & Realistic Bypass Vectors

In child web safety and parental control systems, children frequently attempt bypasses to circumvent restrictions. The following threat matrix outlines common bypass attempts and KidSafe AI's defense layer:

| Bypass Vector | Description | Child Tech Level | KidSafe AI Defense Mechanism | Defense Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Extension Disabling** | Navigating to `chrome://extensions` and toggling the extension off. | Low | Monitored by `tabs.onUpdated` redirecting to `block.html`; locked via Windows Group Policy `ExtensionInstallForcelist`. | **Resistant** |
| **2. Incognito / InPrivate Browsing** | Opening Private windows to browse without extension filtering. | Low | Automatically intercepts Incognito requests (`FR-B6`) or disables Incognito entirely via Registry policy `IncognitoModeAvailability=1`. | **Resistant** |
| **3. Developer Tools Manipulation** | Opening DevTools (`F12`) to modify DOM or terminate Service Worker. | Medium | Blocked via Enterprise Registry policy `DeveloperToolsAvailability=2`. | **Resistant** |
| **4. SafeSearch Tampering** | Removing `safe=active` or `adlt=strict` query parameters. | Low–Medium | Forced DeclarativeNetRequest header and query transformations re-inject parameters automatically before request execution. | **Fully Enforced** |
| **5. Tampering with Extension Settings** | Changing the active child profile, time limit, or allowlist. | Low | Protected by 4-digit SHA-256 hashed **Parent PIN** inside popup controller. | **Fully Enforced** |
| **6. Disconnecting Network (Offline Bypass)** | Browsing cached files or disconnecting from backend API. | Medium | Offline fallback cache (`FR-B7`) enforces strict local blocklists even if backend is unreachable. | **Resistant** |
| **7. Alternative Unmonitored Browser** | Opening Firefox, Tor, or Opera installed on the machine. | Medium | Outside single-browser extension scope; mitigated via Windows AppLocker or Family Safety. | *Documented Limitation* |
| **8. Local Admin Registry Removal** | Child with full Windows Administrator privileges deleting registry keys. | High | Documented Non-Goal (PRD Section 3.2: local OS root privilege overrides application-level policies). | *Documented Limitation* |

---

## 2. Hardening Configurations

### 2.1 Google Chrome Hardening
Run `hardening/chrome_hardening.reg` as Administrator:
- Disables Chrome Developer Tools.
- Disables Incognito mode or forces extension in Incognito.
- Adds KidSafe AI to `ExtensionInstallForcelist` (prevents "Remove from Chrome" option).

### 2.2 Microsoft Edge Hardening
Run `hardening/edge_hardening.reg` as Administrator:
- Disables InPrivate mode.
- Locks Edge extension management.

---

## 3. Academic Defense Discussion for Dissertation
In standard Manifest V3 architectures, browser extensions run inside a sandboxed Chromium user space. Our defense-in-depth model leverages:
1. **Application-level policy:** Real-time request interception, PIN authentication, and internal settings redirects.
2. **OS-level policy:** Chrome/Edge Enterprise Group Policies that establish administrative immutability.
This two-tier defense satisfies Goal **G6** and Functional Requirement **FR-B6 & FR-B9**.
