# KidSafe AI - Natural Language Parent Agent
# Translates plain-English parent instructions into structured actions with confirmation previews
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import models

class ParentNLAgent:
    def preview_instruction(self, instruction: str, profile: models.ChildProfile) -> Dict[str, Any]:
        """
        Parses a parent's natural-language command and generates a structured confirmation preview.
        """
        text = instruction.strip().lower()
        actions = []

        # 1. Screen Time adjustments: e.g. "set screen time to 90 mins", "limit time to 2 hours"
        time_match = re.search(r"(?:set|change|limit|give)?\s*(?:screen\s*time|time\s*limit|time)\s*(?:to|for)?\s*(\d+)\s*(mins?|minutes?|hours?|hrs?)?", text)
        if time_match:
            val = int(time_match.group(1))
            unit = time_match.group(2) or "mins"
            if "hour" in unit or "hr" in unit:
                minutes = val * 60
            else:
                minutes = val

            actions.append({
                "action_type": "SET_TIME_LIMIT",
                "params": {"daily_time_limit_minutes": minutes},
                "summary": f"Change daily screen time limit for {profile.name} to {minutes} minutes."
            })

        # 2. Strictness Tier changes: e.g. "change tier to teen", "switch to little explorer mode", "make him junior"
        if "little explorer" in text:
            actions.append({
                "action_type": "CHANGE_TIER",
                "params": {"tier": "little_explorer"},
                "summary": f"Change {profile.name}'s safety tier to Little Explorer (Ages 5–8, allowlist only)."
            })
        elif "teen" in text:
            actions.append({
                "action_type": "CHANGE_TIER",
                "params": {"tier": "teen"},
                "summary": f"Change {profile.name}'s safety tier to Teen (Ages 13–17, moderate AI screening)."
            })
        elif "junior" in text and not ("junior" == profile.tier):
            actions.append({
                "action_type": "CHANGE_TIER",
                "params": {"tier": "junior"},
                "summary": f"Change {profile.name}'s safety tier to Junior (Ages 9–12, safe categories)."
            })

        # 3. Protection toggle: e.g. "pause protection", "turn off shield", "resume protection", "enable filter"
        if any(w in text for w in ["pause protection", "disable protection", "turn off shield", "pause shield"]):
            actions.append({
                "action_type": "TOGGLE_PROTECTION",
                "params": {"is_protection_active": False},
                "summary": f"Temporarily pause web protection for {profile.name}."
            })
        elif any(w in text for w in ["resume protection", "enable protection", "turn on shield", "activate protection"]):
            actions.append({
                "action_type": "TOGGLE_PROTECTION",
                "params": {"is_protection_active": True},
                "summary": f"Re-enable web protection for {profile.name}."
            })

        # 4. Domain allow/block rules:
        # e.g. "allow scratch.mit.edu and khanacademy.org", "block twitch and reddit"
        # Find all domains mentioned
        domain_pattern = r"\b(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)\b"
        found_domains = re.findall(domain_pattern, text)

        # Check intention for domain
        is_allow_intent = any(w in text for w in ["allow", "whitelist", "permit", "unblock"])
        is_block_intent = any(w in text for w in ["block", "blacklist", "restrict", "ban", "deny"])

        # Also support popular platform names without .com
        platform_mappings = {
            "youtube": "youtube.com",
            "roblox": "roblox.com",
            "discord": "discord.com",
            "twitch": "twitch.tv",
            "reddit": "reddit.com",
            "tiktok": "tiktok.com",
            "instagram": "instagram.com",
            "steam": "store.steampowered.com",
            "netflix": "netflix.com",
            "khan academy": "khanacademy.org",
            "scratch": "scratch.mit.edu",
            "wikipedia": "wikipedia.org"
        }

        for name, domain in platform_mappings.items():
            if name in text and domain not in found_domains:
                found_domains.append(domain)

        if is_allow_intent and not is_block_intent:
            for d in found_domains:
                actions.append({
                    "action_type": "ADD_RULE",
                    "params": {"domain": d, "rule_type": "allow"},
                    "summary": f"Add {d} to {profile.name}'s Allowed list."
                })
        elif is_block_intent:
            for d in found_domains:
                actions.append({
                    "action_type": "ADD_RULE",
                    "params": {"domain": d, "rule_type": "block"},
                    "summary": f"Add {d} to {profile.name}'s Blocked list."
                })

        if not actions:
            return {
                "success": False,
                "message": "I didn't quite catch the specific rule change. Try: 'allow khanacademy.org', 'block twitch.tv', 'set screen time to 90 mins', or 'switch to teen mode'.",
                "actions": []
            }

        return {
            "success": True,
            "instruction": instruction,
            "target_child": profile.name,
            "actions_count": len(actions),
            "actions": actions,
            "requires_confirmation": True
        }

    def apply_actions(self, actions: List[Dict[str, Any]], profile_id: str, db: Session) -> Dict[str, Any]:
        """
        Executes confirmed actions against the child profile in the database.
        """
        profile = db.query(models.ChildProfile).filter(models.ChildProfile.id == profile_id).first()
        if not profile:
            return {"success": False, "error": "Profile not found."}

        applied = []
        for act in actions:
            action_type = act.get("action_type")
            params = act.get("params", {})

            if action_type == "SET_TIME_LIMIT":
                profile.daily_time_limit_minutes = params.get("daily_time_limit_minutes", 120)
                applied.append(f"Set time limit to {profile.daily_time_limit_minutes} minutes")

            elif action_type == "CHANGE_TIER":
                profile.tier = params.get("tier", "junior")
                applied.append(f"Changed tier to {profile.tier}")

            elif action_type == "TOGGLE_PROTECTION":
                profile.is_protection_active = params.get("is_protection_active", True)
                status_str = "Active" if profile.is_protection_active else "Paused"
                applied.append(f"Set protection status to {status_str}")

            elif action_type == "ADD_RULE":
                domain = params.get("domain", "").strip().lower()
                rule_type = params.get("rule_type", "allow")
                if domain:
                    existing = db.query(models.CustomRule).filter(
                        models.CustomRule.profile_id == profile.id,
                        models.CustomRule.domain == domain
                    ).first()
                    if existing:
                        existing.rule_type = rule_type
                    else:
                        new_rule = models.CustomRule(
                            profile_id=profile.id,
                            domain=domain,
                            rule_type=rule_type
                        )
                        db.add(new_rule)
                    applied.append(f"{rule_type.capitalize()}ed {domain}")

        db.commit()
        db.refresh(profile)

        return {
            "success": True,
            "profile_id": profile.id,
            "profile_name": profile.name,
            "applied_changes": applied,
            "updated_profile": {
                "tier": profile.tier,
                "daily_time_limit_minutes": profile.daily_time_limit_minutes,
                "is_protection_active": profile.is_protection_active
            }
        }

parent_agent = ParentNLAgent()
