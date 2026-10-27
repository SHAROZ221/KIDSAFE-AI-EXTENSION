// KidSafe AI - Constants and Policy Presets

export const PROFILES = {
  LITTLE_EXPLORER: {
    id: "little_explorer",
    name: "Little Explorer",
    ageRange: "5–8 years",
    description: "Strict allowlist only. Only pre-approved child-friendly websites are accessible.",
    mode: "allowlist_only",
    dailyTimeLimitMinutes: 60,
    safeSearchRequired: true
  },
  JUNIOR: {
    id: "junior",
    name: "Junior",
    ageRange: "9–12 years",
    description: "Allowlist + AI-verified safe categories. Dangerous and mature sites are blocked.",
    mode: "hybrid",
    dailyTimeLimitMinutes: 120,
    safeSearchRequired: true
  },
  TEEN: {
    id: "teen",
    name: "Teen",
    ageRange: "13–17 years",
    description: "Blocklist + AI classification. Broad web access with protection against adult & high-risk content.",
    mode: "blocklist_ai",
    dailyTimeLimitMinutes: 180,
    safeSearchRequired: true
  }
};

// Safe default allowlist for younger kids
export const DEFAULT_ALLOWLIST = [
  "pbskids.org",
  "kids.nationalgeographic.com",
  "scratch.mit.edu",
  "kiddle.co",
  "khanacademy.org",
  "code.org",
  "funbrain.com",
  "nasa.gov/kidsclub",
  "highlightskids.com",
  "scholastic.com",
  "turtlediary.com",
  "starfall.com",
  "abcya.com",
  "wikipedia.org",
  "en.wikipedia.org"
];

// High-risk blocked domain patterns & categories
export const DEFAULT_BLOCKLIST = [
  // Adult & mature
  "pornhub.com",
  "xvideos.com",
  "xnxx.com",
  "chaturbate.com",
  "onlyfans.com",
  "redtube.com",
  "youporn.com",
  // Gambling
  "bet365.com",
  "pokerstars.com",
  "stake.com",
  "draftkings.com",
  "bovada.lv",
  // Violent & shock
  "bestgore.com",
  "liveleak.com",
  "rotten.com",
  // Piracy & unmonitored chat
  "thepiratebay.org",
  "1337x.to",
  "omegle.com",
  "chatroulette.com"
];

// Category risk keywords for fallback classification
export const RISK_KEYWORD_RULES = {
  adult: [
    "porn", "xxx", "nsfw", "erotic", "sex", "nude", "camgirl", "escort", "stripchat"
  ],
  gambling: [
    "casino", "betting", "poker", "roulette", "jackpot", "slots", "wager", "sportsbook"
  ],
  violence: [
    "gore", "beheading", "murder video", "brutal execution", "snuff"
  ],
  weapons_drugs: [
    "buy drugs online", "darknet market", "buy assault rifle", "ghost gun build"
  ]
};

// Default initial state for extension storage
export const DEFAULT_STATE = {
  activeProfile: "junior",
  parentPinHash: "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4", // SHA-256 for default "1234"
  isProtectionActive: true,
  safeSearchEnforced: true,
  blockIncognitoNavigation: true,
  dailyTimeLimitMinutes: 120,
  timeUsedTodaySeconds: 0,
  lastActiveDate: new Date().toISOString().slice(0, 10),
  customAllowlist: [],
  customBlocklist: [],
  pendingRequests: [],
  verdictCache: {},
  backendUrl: "http://localhost:8000",
  deviceToken: null,
  isPaired: false,
  pairedProfileName: null
};
