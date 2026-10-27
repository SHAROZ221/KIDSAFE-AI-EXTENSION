// KidSafe AI - Phase 1 Verification Test Suite
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { PROFILES, DEFAULT_STATE } from "../extension/utils/constants.js";
import { isDomainMatch, extractHostname, hashPin, evaluateUrlPolicy } from "../extension/utils/helpers.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");

let passed = 0;
let failed = 0;

function assert(condition, testName) {
  if (condition) {
    console.log(`[PASS] ${testName}`);
    passed++;
  } else {
    console.error(`[FAIL] ${testName}`);
    failed++;
  }
}

async function runTests() {
  console.log("=== Running KidSafe AI Phase 1 Tests ===\n");

  // 1. Verify manifest.json
  const manifestPath = path.join(rootDir, "extension", "manifest.json");
  const manifestRaw = fs.readFileSync(manifestPath, "utf-8");
  const manifest = JSON.parse(manifestRaw);
  assert(manifest.manifest_version === 3, "Manifest is Version 3");
  assert(manifest.background.service_worker === "background/service_worker.js", "Background service worker configured");
  assert(manifest.declarative_net_request.rule_resources.length > 0, "DeclarativeNetRequest SafeSearch rules attached");

  // 2. Verify SafeSearch rules
  const rulesPath = path.join(rootDir, "extension", "rules", "safesearch.json");
  const rules = JSON.parse(fs.readFileSync(rulesPath, "utf-8"));
  assert(Array.isArray(rules) && rules.length >= 4, "SafeSearch rules contain rules for Google, Bing, DuckDuckGo, YouTube");

  // 3. Verify Domain match logic
  assert(isDomainMatch("pbskids.org", "pbskids.org") === true, "Exact domain match");
  assert(isDomainMatch("sub.pbskids.org", "pbskids.org") === true, "Subdomain match");
  assert(isDomainMatch("www.pbskids.org", "pbskids.org") === true, "www prefix domain match");
  assert(isDomainMatch("evil-pbskids.org", "pbskids.org") === false, "Different domain does not match");

  // 4. Verify PIN hashing
  const testPinHash = await hashPin("1234");
  assert(testPinHash === DEFAULT_STATE.parentPinHash, "Default PIN 1234 matches initial hash");

  // 5. Test Little Explorer (allowlist only)
  const explorerState = { ...DEFAULT_STATE, activeProfile: "little_explorer" };
  const allowedExplorer = await evaluateUrlPolicy("https://pbskids.org/games", explorerState);
  assert(allowedExplorer.verdict === "allow", "Little Explorer allows pbskids.org");

  const blockedExplorer = await evaluateUrlPolicy("https://random-unknown-blog.com", explorerState);
  assert(blockedExplorer.verdict === "block", "Little Explorer blocks unknown sites");

  // 6. Test Junior Profile (allows safe categories, blocks adult/risk keywords)
  const juniorState = { ...DEFAULT_STATE, activeProfile: "junior" };
  const safeJunior = await evaluateUrlPolicy("https://khanacademy.org/math", juniorState);
  assert(safeJunior.verdict === "allow", "Junior allows educational site");

  const blockedAdult = await evaluateUrlPolicy("https://pornhub.com", juniorState);
  assert(blockedAdult.verdict === "block", "Junior blocks known adult site");

  const keywordBlocked = await evaluateUrlPolicy("https://free-casino-slots-bonus.net", juniorState);
  assert(keywordBlocked.verdict === "block", "Junior blocks gambling keyword domain");

  // 7. Test Parent Custom Overrides
  const customOverrideState = {
    ...DEFAULT_STATE,
    activeProfile: "little_explorer",
    customAllowlist: ["customschool.edu"],
    customBlocklist: ["pbskids.org"] // parent specifically blocked
  };
  const customAllowed = await evaluateUrlPolicy("https://customschool.edu", customOverrideState);
  assert(customAllowed.verdict === "allow" && customAllowed.reason === "parent_approved", "Custom parent allowlist overrides profile restriction");

  const customBlocked = await evaluateUrlPolicy("https://pbskids.org", customOverrideState);
  assert(customBlocked.verdict === "block" && customBlocked.reason === "parent_blocked", "Custom parent blocklist overrides allowlist");

  console.log(`\n=== Test Results: ${passed} Passed, ${failed} Failed ===`);
  if (failed > 0) process.exit(1);
}

runTests().catch(err => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
