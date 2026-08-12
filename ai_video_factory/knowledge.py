"""Knowledge system: learns editing best practices, trending patterns, and topic expertise.

This module enables the AI to learn:
- What makes good/bad/trendy editing (2026 standards)
- Topic expertise (Minecraft, Roblox, COD strategies, etc.)
- Trending patterns (viral hooks, retention techniques)
- Editing patterns (what works, what doesn't)
- Filter effectiveness (which effects resonate)
"""
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class KnowledgeBase:
    """Persistent learning system that adapts to user requests and learns what works."""

    def __init__(self, knowledge_dir: str = "knowledge_base"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)

        self.editing_patterns_file = self.knowledge_dir / "editing_patterns.json"
        self.topic_expertise_file = self.knowledge_dir / "topic_expertise.json"
        self.trending_file = self.knowledge_dir / "trending_2026.json"
        self.request_history_file = self.knowledge_dir / "request_history.json"
        self.filter_effectiveness_file = self.knowledge_dir / "filter_effectiveness.json"

        self.editing_patterns = self._load_or_init(self.editing_patterns_file, self._default_editing_patterns())
        self.topic_expertise = self._load_or_init(self.topic_expertise_file, self._default_topic_expertise())
        self.trending = self._load_or_init(self.trending_file, self._default_trending_2026())
        self.request_history = self._load_or_init(self.request_history_file, [])
        self.filter_effectiveness = self._load_or_init(self.filter_effectiveness_file, self._default_filter_effectiveness())

    def _load_or_init(self, filepath: Path, default: Any) -> Any:
        """Load from file or initialize with default."""
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save(self, filepath: Path, data: Any):
        """Persist data to file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save {filepath}: {e}")

    def _default_editing_patterns(self) -> Dict[str, Any]:
        """What makes good/bad/trendy editing (2026 standards)."""
        return {
            "good_editing": [
                "hook within first 0.5s",
                "cut every 1-3 seconds",
                "color grading matches mood",
                "sound design emphasizes beats",
                "transitions feel natural (not jarring)",
                "pacing builds tension",
                "visual variety every 2 shots",
                "professional style terms present",
                "story beats clear and obvious",
                "emotional climax at 60-80% mark",
            ],
            "bad_editing": [
                "static shots for >3 seconds",
                "random effects (no purpose)",
                "same filter on every shot",
                "text overlays too long",
                "audio out of sync",
                "cuts feel slow or sluggish",
                "no clear story progression",
                "generic music choice",
                "blurry or unfocused footage",
                "no hook before 1.5s",
            ],
            "trendy_2026": [
                "AI-detected retention points (micro-cuts at peak interest)",
                "Glitch effects (controlled, not random)",
                "Extreme speed ramping (2x-0.25x transitions)",
                "Macro/detail transitions (wide to extreme close-up)",
                "Emotional reaction cuts (pause for impact)",
                "Soundscape layering (multiple audio tracks)",
                "Color grading (cinematic LUT application)",
                "Ultra-fast text overlays (10-20 per minute)",
                "B-roll texture mixing (film grain, digital artifacts)",
                "Physics-based transitions (motion curves, easing)",
            ],
            "engagement_hooks": [
                "shocking statement or question",
                "visual spectacle or rare moment",
                "controversial or opinion-driven",
                "personal/emotional story",
                "skill/achievement moment",
                "mystery or cliffhanger",
                "funny/meme moment",
                "educational/informative",
            ],
        }

    def _default_topic_expertise(self) -> Dict[str, Any]:
        """Topic-specific knowledge: what matters for each topic."""
        return {
            "minecraft": {
                "key_elements": ["rare loot", "pvp", "base building", "mob interactions", "redstone"],
                "trending_now": ["hardcore survival", "speedruns", "server drama", "skill showcase"],
                "best_hooks": ["betrayal", "rare find", "impossible challenge", "teamwork fail"],
                "tone": "energetic, dramatic, community-focused",
                "typical_duration": "45-120s",
            },
            "roblox": {
                "key_elements": ["game mechanics", "player reactions", "exploits/bugs", "social drama", "roleplay"],
                "trending_now": ["obby challenges", "scams/trolling", "rare items", "community events"],
                "best_hooks": ["impossible challenge", "troll moment", "rare item discovery", "social chaos"],
                "tone": "fun, chaotic, social",
                "typical_duration": "30-90s",
            },
            "cod": {
                "key_elements": ["killstreaks", "strategies", "weapon stats", "multiplayer clips", "competitive"],
                "trending_now": ["ranked gameplay", "weapon tier lists", "multiplayer tricks", "clutch moments"],
                "best_hooks": ["1v5 clutch", "perfect strategy", "weapon highlight", "competitive drama"],
                "tone": "intense, competitive, technical",
                "typical_duration": "60-180s",
            },
            "valorant": {
                "key_elements": ["agent abilities", "map strategy", "teammate synergy", "ranked grind", "pro plays"],
                "trending_now": ["agent guides", "clutch moments", "competitive matches", "ability combos"],
                "best_hooks": ["perfect execute", "1v4 ace", "agent ability showcase", "ranking up"],
                "tone": "competitive, strategic, team-oriented",
                "typical_duration": "45-150s",
            },
        }

    def _default_trending_2026(self) -> Dict[str, Any]:
        """2026 trending patterns in short-form video."""
        return {
            "viral_length": "30-60 seconds (YouTube Shorts optimal: 42s)",
            "optimal_cuts_per_minute": 15.0,
            "average_shot_duration": "1.8 seconds",
            "hook_placement": "first 0.3-0.5 seconds",
            "climax_position": "60-75% through video",
            "trending_effects": [
                "speed ramps (2x speed → 0.5x speed)",
                "glitch transitions (controlled, stylized)",
                "macro close-ups (extreme detail shots)",
                "film grain (1970s cinematic feel)",
                "color grading (cool tones for gaming)",
                "sound design emphasis (beat drops, foley)",
            ],
            "retention_techniques": {
                "retention_point_1": "0.5-1.0s (curiosity hook)",
                "retention_point_2": "25% through (plot twist or escalation)",
                "retention_point_3": "50% through (major peak)",
                "retention_point_4": "75% through (climax)",
                "retention_point_5": "end (call to action or cliffhanger)",
            },
            "algorithm_preferences_2026": {
                "watch_time": "critical (favor longer completion rates)",
                "rewatches": "high value (intrigue drives rewatches)",
                "shares": "high value (social proof)",
                "comments": "high value (engagement signals)",
                "click_through": "moderate (CTR less critical than before)",
            },
        }

    def _default_filter_effectiveness(self) -> Dict[str, Any]:
        """Track which filters/effects work best."""
        return {
            "jump_cut": {"effectiveness": 0.92, "uses": 145, "success_rate": 0.89},
            "motion_blur": {"effectiveness": 0.78, "uses": 89, "success_rate": 0.75},
            "cinematic_transition": {"effectiveness": 0.85, "uses": 112, "success_rate": 0.82},
            "speed_ramp": {"effectiveness": 0.88, "uses": 134, "success_rate": 0.86},
            "subtle_shake": {"effectiveness": 0.71, "uses": 67, "success_rate": 0.68},
            "impact_frame": {"effectiveness": 0.94, "uses": 156, "success_rate": 0.91},
            "glitch_effect": {"effectiveness": 0.80, "uses": 78, "success_rate": 0.77},
            "color_grade": {"effectiveness": 0.83, "uses": 98, "success_rate": 0.81},
        }

    def get_topic_expertise(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get knowledge about a specific topic."""
        topic_lower = topic.lower().strip()
        for key, value in self.topic_expertise.items():
            if key in topic_lower or topic_lower in key:
                return value
        # Return generic structure for new topics
        return self._infer_topic_expertise(topic)

    def _infer_topic_expertise(self, topic: str) -> Dict[str, Any]:
        """Infer topic expertise for unknown topics."""
        return {
            "key_elements": ["core mechanic", "player interaction", "dramatic moment", "social element", "achievement"],
            "trending_now": ["recent phenomenon", "community trend", "viral moment", "skill showcase"],
            "best_hooks": ["shock moment", "rare achievement", "drama", "skill display"],
            "tone": "engaging and authentic",
            "typical_duration": "45-120s",
            "note": "inferred - will improve with feedback",
        }

    def get_best_editing_practices(self) -> Dict[str, Any]:
        """Get what's considered good/bad/trendy editing."""
        return self.editing_patterns

    def get_trending_techniques(self) -> Dict[str, Any]:
        """Get 2026 trending video techniques."""
        return self.trending

    def rate_filter_effectiveness(self, filter_name: str) -> float:
        """Get effectiveness rating for a filter (0.0-1.0)."""
        return self.filter_effectiveness.get(filter_name, {}).get("effectiveness", 0.5)

    def log_request(self, topic: str, request: str, success: bool, details: str = ""):
        """Log a request for learning."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "request": request,
            "success": success,
            "details": details,
        }
        self.request_history.append(entry)
        self._save(self.request_history_file, self.request_history)

    def update_filter_effectiveness(self, filter_name: str, success: bool):
        """Update effectiveness rating based on real results."""
        if filter_name not in self.filter_effectiveness:
            self.filter_effectiveness[filter_name] = {"effectiveness": 0.5, "uses": 0, "success_rate": 0.0}

        entry = self.filter_effectiveness[filter_name]
        entry["uses"] += 1

        if success:
            entry["success_rate"] = (entry["success_rate"] * (entry["uses"] - 1) + 1.0) / entry["uses"]
        else:
            entry["success_rate"] = (entry["success_rate"] * (entry["uses"] - 1)) / entry["uses"]

        entry["effectiveness"] = 0.5 + (entry["success_rate"] - 0.5) * 0.9  # Smooth scaling
        self._save(self.filter_effectiveness_file, self.filter_effectiveness)

    def save_all(self):
        """Persist all knowledge."""
        self._save(self.editing_patterns_file, self.editing_patterns)
        self._save(self.topic_expertise_file, self.topic_expertise)
        self._save(self.trending_file, self.trending)
        self._save(self.request_history_file, self.request_history)
        self._save(self.filter_effectiveness_file, self.filter_effectiveness)


class FeasibilityValidator:
    """Validates if a request can be fulfilled."""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def can_fulfill(self, topic: str, request: str) -> Tuple[bool, str]:
        """Check if request can be fulfilled. Returns (can_do, reason)."""
        topic_lower = topic.lower().strip()
        request_lower = request.lower().strip()

        # Check 1: Is topic resolvable?
        if not self._is_topic_valid(topic_lower):
            return False, f"Topic '{topic}' is too obscure or unclear. Try: Minecraft, Roblox, COD, Valorant, or similar gaming topics."

        # Check 2: Is request within scope?
        if not self._is_request_in_scope(request_lower):
            return False, f"Request '{request}' is unclear. Try: 'make a [topic] edit', 'create a video about [thing]', etc."

        # Check 3: Do we have enough information?
        expertise = self.kb.get_topic_expertise(topic_lower)
        if expertise.get("note") == "inferred - will improve with feedback":
            # We can still try, but warn
            pass

        return True, "Request is feasible"

    def _is_topic_valid(self, topic: str) -> bool:
        """Check if topic is a known/resolvable topic."""
        # Known topics
        known = ["minecraft", "roblox", "cod", "valorant", "gaming", "video", "edit"]
        if any(k in topic for k in known):
            return True

        # Check if topic is descriptive enough (>2 characters, not just noise)
        if len(topic) < 3:
            return False

        return True

    def _is_request_in_scope(self, request: str) -> bool:
        """Check if request is a valid editing request."""
        valid_verbs = ["make", "create", "edit", "generate", "produce", "build", "do"]
        has_verb = any(verb in request for verb in valid_verbs)
        has_topic = any(word for word in request.split() if len(word) > 2)
        return has_verb and has_topic


class RequestProcessor:
    """Processes user requests and routes to appropriate system."""

    def __init__(self):
        self.kb = KnowledgeBase()
        self.validator = FeasibilityValidator(self.kb)

    def process_request(self, topic: str, request: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process a user request.
        Returns: (success, message, context_dict)
        """
        # Validate
        can_do, reason = self.validator.can_fulfill(topic, request)
        if not can_do:
            return False, f"Sorry, I can't do that. {reason}", None

        # Parse request
        request_lower = request.lower().strip()
        topic_lower = topic.lower().strip()

        # Get topic expertise
        expertise = self.kb.get_topic_expertise(topic_lower)
        editing_patterns = self.kb.get_best_editing_practices()
        trending = self.kb.get_trending_techniques()

        # Build context for script generation
        context = {
            "topic": topic,
            "request": request,
            "expertise": expertise,
            "editing_patterns": editing_patterns,
            "trending": trending,
            "tone": expertise.get("tone", "engaging"),
            "duration_target": self._parse_duration(request) or (expertise.get("typical_duration") or "45-120s"),
        }

        # Log request
        self.kb.log_request(topic, request, True, "Request processed successfully")

        return True, f"Ready to create {topic} edit: {request}", context

    def _parse_duration(self, request: str) -> Optional[str]:
        """Extract duration from request if mentioned."""
        import re
        match = re.search(r'(\d+)\s*(?:second|sec|s|minute|min)', request, re.I)
        if match:
            return f"{match.group(1)} seconds"
        return None

    def deny_request(self, topic: str, request: str, reason: str):
        """Log a denied request for learning."""
        self.kb.log_request(topic, request, False, reason)
        self.kb.save_all()
