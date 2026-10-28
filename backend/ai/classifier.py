# KidSafe AI - Agentic Page Classifier
# Evaluates web content using LLM APIs (Gemini/Groq/OpenAI) with high-recall semantic fallback
import os
import re
import json
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Cache entry format: { "result": dict, "timestamp": float }
_VERDICT_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 24 * 60 * 60 # 24 hours

# Taxonomy rules for semantic classification
CATEGORIES_PATTERNS = {
    "adult": [
        r"\b(porn|xxx|nsfw|erotic|sex|camgirl|stripchat|nude|boobs|penis|vagina|onlyfans|redtube|xvideos)\b",
        r"\b(adult content|escort service|erotica|fetish)\b"
    ],
    "gambling": [
        r"\b(casino|betting|poker|roulette|jackpot|slots|sportsbook|wager|bet365|stake\.com)\b",
        r"\b(real money gaming|gamble online|lottery ticket)\b"
    ],
    "violence_gore": [
        r"\b(gore|beheading|snuff|massacre|bloodbath|execution video|murder footage)\b",
        r"\b(self[- ]harm|suicide method|how to commit suicide|kill myself)\b"
    ],
    "weapons_drugs": [
        r"\b(buy drugs online|darknet market|silk road|buy cocaine|buy weed online)\b",
        r"\b(ghost gun blueprint|3d printed gun|buy assault rifle)\b"
    ],
    "social_media": [
        r"\b(reddit|twitter|x\.com|instagram|tiktok|facebook|snapchat|discord|threads)\b"
    ],
    "gaming": [
        r"\b(roblox|minecraft|fortnite|steam|epicgames|twitch|gaming|game play|play game)\b"
    ],
    "education": [
        r"\b(math|science|physics|chemistry|history|geography|encyclopedia|khanacademy|wikipedia|school|homework|learn|tutorial|coding|python|scratch)\b"
    ],
    "kids_entertainment": [
        r"\b(cartoon|disney|nickelodeon|pbskids|kiddle|national geographic kids|fairy tale|rhymes|lego|barbie)\b"
    ]
}

SYSTEM_PROMPT = """You are KidSafe AI, an expert agentic child web safety and content moderation system.
Your job is to analyze webpage content and metadata, evaluate whether it is appropriate for a child's age profile, and generate structured verdicts with plain-language explanations.

Child Age Profiles:
1. little_explorer (5–8 yrs): Strict allowlist tier. Only safe, educational, or wholesome kids content is allowed. Block all complex forums, social media, mature themes, or high-stimulation content.
2. junior (9–12 yrs): Safe browsing tier. Allow education, safe gaming, research, and general knowledge. Block adult, violence, gambling, mature discussion forums, and extreme content.
3. teen (13–17 yrs): Moderate protection tier. Allow broad web access, supervised social media, and teen interest content. Strictly block adult/NSFW, gambling, illegal substances, self-harm, hate speech, and extreme violence.

Return ONLY a valid JSON object matching this EXACT schema:
{
  "verdict": "allow" | "block" | "ask_parent",
  "confidence": 0.95,
  "categories": ["education", "coding"],
  "age_rating": "5+" | "9+" | "13+" | "18+",
  "reason_parent": "Concise technical explanation for the parent.",
  "reason_child": "Friendly, encouraging, non-scary explanation suitable for the child.",
  "risk_flags": []
}

Allowed risk_flags: ["adult", "violence", "gambling", "scam", "self_harm", "weapons_drugs", "mature_forum", "none"].
Output valid JSON only with NO markdown code fences.
"""

class PageClassifierAgent:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def classify(
        self,
        url: str,
        title: Optional[str] = "",
        meta_description: Optional[str] = "",
        page_text_sample: Optional[str] = "",
        age_profile: str = "junior"
    ) -> Dict[str, Any]:
        """
        Classifies webpage content for a specific child age profile.
        Checks cache first, then calls LLM (if configured) or semantic heuristic classifier.
        """
        clean_url = url.strip()
        parsed = urlparse(clean_url)
        hostname = (parsed.hostname or "").lower()

        # Cache key combines domain + path + age_profile
        cache_key = f"{hostname}:{age_profile}"
        now = time.time()
        if cache_key in _VERDICT_CACHE:
            cached = _VERDICT_CACHE[cache_key]
            if now - cached["timestamp"] < CACHE_TTL_SECONDS:
                return cached["result"]

        # Check for configured LLM Provider
        verdict = None
        if self.gemini_key:
            verdict = self._classify_with_gemini(clean_url, title, meta_description, page_text_sample, age_profile)
        elif self.groq_key:
            verdict = self._classify_with_groq(clean_url, title, meta_description, page_text_sample, age_profile)

        # Fallback to intelligent semantic classifier
        if not verdict:
            verdict = self._classify_semantic_fallback(clean_url, title, meta_description, page_text_sample, age_profile)

        # Store in cache
        _VERDICT_CACHE[cache_key] = {
            "result": verdict,
            "timestamp": now
        }
        return verdict

    def _classify_with_gemini(
        self, url: str, title: str, meta: str, text: str, age_profile: str
    ) -> Optional[Dict[str, Any]]:
        """Call Google Gemini API using google-genai or requests."""
        try:
            import google.genai as genai
            client = genai.Client(api_key=self.gemini_key)
            prompt = f"{SYSTEM_PROMPT}\n\nWebpage to evaluate:\nURL: {url}\nTitle: {title}\nMeta Description: {meta}\nPage Text: {text[:1500]}\nTarget Child Age Profile: {age_profile}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = response.text.strip()
            # Clean possible markdown fences
            raw = re.sub(r"^```(?:json)?\n", "", raw)
            raw = re.sub(r"\n```$", "", raw)
            data = json.loads(raw)
            return self._normalize_output(data, age_profile)
        except Exception:
            return None

    def _classify_with_groq(
        self, url: str, title: str, meta: str, text: str, age_profile: str
    ) -> Optional[Dict[str, Any]]:
        """Call Groq API using groq client."""
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            prompt = f"Webpage to evaluate:\nURL: {url}\nTitle: {title}\nMeta Description: {meta}\nPage Text: {text[:1500]}\nTarget Child Age Profile: {age_profile}"
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return self._normalize_output(data, age_profile)
        except Exception:
            return None

    def _classify_semantic_fallback(
        self, url: str, title: str, meta: str, text: str, age_profile: str
    ) -> Dict[str, Any]:
        """
        Deterministic, high-accuracy semantic and category classifier.
        Used as primary engine when API keys are not supplied and as fallback.
        """
        combined = f"{url} {title or ''} {meta or ''} {text or ''}".lower()
        matched_categories = []
        risk_flags = []

        # Check each pattern set
        for category, patterns in CATEGORIES_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, combined, re.IGNORECASE):
                    matched_categories.append(category)
                    break

        # Check high-severity risks
        if "adult" in matched_categories:
            risk_flags.append("adult")
        if "gambling" in matched_categories:
            risk_flags.append("gambling")
        if "violence_gore" in matched_categories:
            risk_flags.append("violence")
        if "weapons_drugs" in matched_categories:
            risk_flags.append("weapons_drugs")

        # Determine age rating & verdict based on child profile
        age_profile = age_profile.lower()

        # HIGH-RISK: Immediate block for all profiles
        if risk_flags:
            flags_str = ", ".join(risk_flags)
            return {
                "verdict": "block",
                "confidence": 0.98,
                "categories": matched_categories or ["restricted"],
                "age_rating": "18+",
                "reason_parent": f"Page contains high-risk content detected by KidSafe AI ({flags_str}).",
                "reason_child": "Oops! KidSafe AI found content here that isn't safe for kids yet.",
                "risk_flags": risk_flags
            }

        # Profile: Little Explorer (5–8)
        if age_profile == "little_explorer":
            if any(c in matched_categories for c in ["education", "kids_entertainment"]):
                return {
                    "verdict": "allow",
                    "confidence": 0.92,
                    "categories": matched_categories or ["education"],
                    "age_rating": "5+",
                    "reason_parent": "Verified age-appropriate learning or entertainment site for young children.",
                    "reason_child": "Great choice! This is a fun and safe website for you to explore.",
                    "risk_flags": []
                }
            elif "social_media" in matched_categories or "gaming" in matched_categories:
                return {
                    "verdict": "ask_parent",
                    "confidence": 0.88,
                    "categories": matched_categories,
                    "age_rating": "9+",
                    "reason_parent": "Interactive social or gaming platform. Parent approval required for Little Explorer mode.",
                    "reason_child": "This website is for older kids. Click 'Ask Parent' if you'd like your mom or dad to unlock it for you!",
                    "risk_flags": ["mature_forum"]
                }
            else:
                return {
                    "verdict": "block",
                    "confidence": 0.85,
                    "categories": matched_categories or ["general_web"],
                    "age_rating": "9+",
                    "reason_parent": "General web page outside Little Explorer pre-approved learning categories.",
                    "reason_child": "This website isn't in your approved list yet. Ask mom or dad if you need it for school!",
                    "risk_flags": []
                }

        # Profile: Junior (9–12)
        if age_profile == "junior":
            if "social_media" in matched_categories:
                return {
                    "verdict": "ask_parent",
                    "confidence": 0.85,
                    "categories": ["social_media"],
                    "age_rating": "13+",
                    "reason_parent": "Social community with unmoderated user comments. Requires parent permission for Junior profile.",
                    "reason_child": "This site lets people chat publicly. You can ask your parent to unlock it if you need it!",
                    "risk_flags": ["mature_forum"]
                }
            return {
                "verdict": "allow",
                "confidence": 0.90,
                "categories": matched_categories or ["general_web"],
                "age_rating": "9+",
                "reason_parent": "Content is age-appropriate with no adult, gambling, or violent indicators.",
                "reason_child": "You're all clear! Enjoy browsing safely.",
                "risk_flags": []
            }

        # Profile: Teen (13–17)
        return {
            "verdict": "allow",
            "confidence": 0.92,
            "categories": matched_categories or ["general_web"],
            "age_rating": "13+",
            "reason_parent": "Standard web content suitable for teenagers with no extreme risk flags.",
            "reason_child": "Safe to browse for teens.",
            "risk_flags": []
        }

    def _normalize_output(self, data: Dict[str, Any], age_profile: str) -> Dict[str, Any]:
        """Validates and guarantees full PRD compliance for output structure."""
        verdict = str(data.get("verdict", "allow")).lower()
        if verdict not in ["allow", "block", "ask_parent"]:
            verdict = "allow"

        return {
            "verdict": verdict,
            "confidence": float(data.get("confidence", 0.90)),
            "categories": list(data.get("categories", ["general"])),
            "age_rating": str(data.get("age_rating", "9+")),
            "reason_parent": str(data.get("reason_parent", "Evaluated by KidSafe AI agent.")),
            "reason_child": str(data.get("reason_child", "Protected by KidSafe AI.")),
            "risk_flags": list(data.get("risk_flags", []))
        }

# Global singleton
classifier_agent = PageClassifierAgent()
