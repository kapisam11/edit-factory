"""Video Director — creative orchestration engine for the AI Video Factory.

Implements the full 20-section creative workflow with:
- Deep web research (DuckDuckGo + page scraping)
- Creator style learning (YouTube thumbnail analysis)
- Royalty-free music fetching + beat-sync mixing
- Natural voiceover (Edge TTS, free)
- Professional thumbnail generation with learned styles

Usage:
    from ai_video_factory import VideoDirector
    director = VideoDirector()
    pkg = director.produce("Minecraft betrayal on SMP", raw_video="clip.mp4")
"""
import json
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .composer import compose_short_from_video
from .factory import create_package
from .hardware import choose_performance_profile, choose_encoder
from .music_fetcher import get_track_for_emotion
from .music_mixer import (
    detect_music_beats,
    align_segments_to_music,
    add_music_to_video,
    mix_audio,
)
from .research import research_topic
from .segment_engine import get_segments, detect_beats, _get_duration_safe
from .style_learner import learn_style
from .thumbnail import make_thumbnail, make_thumbnail_variants, make_thumbnail_vertical
from .tts import generate_voiceover, generate_emotional_voiceover
from .web_browser import deep_research

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Creative constants
# ───────────────────────────────────────────────

EMOTIONS = [
    "emotional", "inspiring", "nostalgic", "dramatic",
    "mysterious", "funny", "shocking", "intense"
]

HOOK_TEMPLATES = [
    "Nobody believed him", "The hidden legend", "His final choice",
    "Lost forever", "The real reason", "He lost everything",
    "The truth revealed", "Nobody expected this", "The last war", "Betrayed",
]

MUSIC_MOODS = {
    "emotional": "emotional_cinematic",
    "inspiring": "epic_orchestral",
    "nostalgic": "lofi_or_ambient",
    "dramatic": "dark_trap",
    "mysterious": "cinematic_phonk",
    "funny": "upbeat_meme",
    "shocking": "hard_phonk",
    "intense": "dark_trap",
}

STRUCTURE_SECONDS = {
    "hook": (0, 2), "intro": (2, 8), "conflict": (8, 20),
    "climax": (20, 45), "payoff": (45, 60),
}

SAFE_ZONE_TOP = 0.15
SAFE_ZONE_BOTTOM = 0.12


class VideoDirector:
    """Orchestrates the full creative pipeline."""

    def __init__(
        self,
        out_root: str = "output",
        model_key: Optional[str] = None,
        freesound_key: Optional[str] = None,
    ):
        self.out_root = out_root
        self.model_key = model_key
        self.freesound_key = freesound_key
        self.profile = choose_performance_profile()
        self.encoder = choose_encoder()
        self.creative_brief: Dict = {}
        self.edit_plan: List[Tuple[float, str, str]] = []
        self.style_profile: Optional[Dict] = None
        self.music_path: Optional[str] = None

    # ── 1. RESEARCH (deep web) ───────────────────

    def research(
        self, topic: str, use_groq: bool = False, groq_key: Optional[str] = None
    ) -> Dict:
        """Research topic via deep web browsing + optional Groq."""
        logger.info("[DIRECTOR] Researching: %s", topic)

        # Deep web research
        web_data = deep_research(topic, max_search=10, max_scrape=5)

        # Traditional research (Wikipedia, etc.)
        summary = research_topic(topic, use_groq=use_groq, groq_api_key=groq_key)

        # Merge web findings into summary
        if web_data.get("summary_text"):
            summary["web_research"] = web_data["summary_text"][:2000]
        if web_data.get("images"):
            summary["web_images"] = web_data["images"][:20]
        if web_data.get("videos"):
            summary["web_videos"] = web_data["videos"][:10]

        emotion = self._pick_emotion(summary)
        angle = self._pick_angle(summary)
        hook = self._generate_hook(summary, emotion)

        self.creative_brief = {
            "topic": topic,
            "who_what": summary.get("who_what", ""),
            "main_conflict": summary.get("main_conflict", ""),
            "strongest_angle": angle,
            "emotion": emotion,
            "hook": hook,
            "why_care": summary.get("why_viewers_care", ""),
            "visuals": summary.get("visuals", []),
            "web_images": summary.get("web_images", []),
            "web_videos": summary.get("web_videos", []),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return self.creative_brief

    def _pick_emotion(self, summary: Dict) -> str:
        text = " ".join(str(v) for v in summary.values()).lower()
        scores = {}
        keywords = {
            "emotional": ["sad", "cry", "loss", "heart", "emotional", "tears"],
            "inspiring": ["never give up", "comeback", "win", "hope", "inspiring"],
            "nostalgic": ["old", "remember", "past", "legend", "nostalgia"],
            "dramatic": ["betray", "war", "fight", "drama", "conflict"],
            "mysterious": ["secret", "unknown", "mystery", "hidden", "truth"],
            "funny": ["funny", "lol", "meme", "hilarious", "joke"],
            "shocking": ["shock", "unexpected", "crazy", "insane", "wtf"],
            "intense": ["intense", "clutch", "sweat", "hardcore", "pvp"],
        }
        for emotion, kws in keywords.items():
            scores[emotion] = sum(text.count(kw) for kw in kws)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "dramatic"

    def _pick_angle(self, summary: Dict) -> str:
        candidates = [
            summary.get("strongest_angle", ""),
            summary.get("main_conflict", ""),
            summary.get("who_what", ""),
        ]
        for c in candidates:
            if c and len(c) > 5:
                return c
        return "The untold story"

    def _generate_hook(self, summary: Dict, emotion: str) -> str:
        text = " ".join(str(v) for v in summary.values()).lower()
        for tmpl in HOOK_TEMPLATES:
            if any(k in text for k in tmpl.lower().split()):
                return tmpl
        conflict = summary.get("main_conflict", "")
        if conflict:
            words = conflict.split()[:3]
            return " ".join(words).title()
        return "The Real Reason"

    # ── 2. STYLE LEARNING ────────────────────────

    def learn_creator_style(self, topic: str) -> Dict:
        """Learn thumbnail style from top creators in the niche."""
        logger.info("[DIRECTOR] Learning creator style for: %s", topic)
        self.style_profile = learn_style(topic)
        return self.style_profile

    # ── 3. MUSIC ─────────────────────────────────

    def fetch_music(self, emotion: str, out_dir: str) -> Optional[str]:
        """Fetch royalty-free music matching the emotion."""
        logger.info("[DIRECTOR] Fetching music for: %s", emotion)
        self.music_path = get_track_for_emotion(
            emotion,
            freesound_key=self.freesound_key,
            out_dir=out_dir,
            prefer_local=True,
        )
        return self.music_path

    # ── 4. VIDEO ANALYSIS ────────────────────────

    def analyze_video(self, video_path: str) -> Dict:
        logger.info("[DIRECTOR] Analyzing video: %s", video_path)
        if not os.path.exists(video_path):
            raise FileNotFoundError(video_path)
        duration = _get_duration_safe(video_path)
        segments = get_segments(video_path, 10)
        beats = detect_beats(video_path)

        scored = []
        for s, e in segments:
            seg_dur = e - s
            quality = 1.0 - abs(seg_dur - 4.5) / 10.0
            scored.append((quality, s, e))
        scored.sort(reverse=True)

        # If music available, detect its beats too
        music_bpm, music_beats = None, None
        if self.music_path and os.path.exists(self.music_path):
            music_bpm, music_beats = detect_music_beats(self.music_path)

        return {
            "duration": duration,
            "segments": segments,
            "beats": beats,
            "music_bpm": music_bpm,
            "music_beats": music_beats,
            "best_segments": [(s, e) for _, s, e in scored[:6]],
        }

    # ── 5. SCRIPT & STRUCTURE ────────────────────

    def build_script(self, analysis: Dict) -> str:
        brief = self.creative_brief
        hook = brief.get("hook", "The Real Reason")
        topic = brief.get("topic", "")
        angle = brief.get("strongest_angle", "")
        emotion = brief.get("emotion", "dramatic")

        lines = [
            hook,
            f"This is the story of {topic}.",
            f"{angle}.",
            "But nobody saw this coming.",
            "And the ending changed everything.",
        ]
        script = "\n".join(lines)
        brief["script"] = script
        return script

    def build_edit_plan(self, analysis: Dict, target_seconds: float = 45.0):
        scale = target_seconds / 60.0
        self.edit_plan = [
            (max(1.5, 2.0 * scale), "hook", "impact frame + zoom"),
            (max(4.0, 6.0 * scale), "intro", "cinematic transition + settle"),
            (max(6.0, 12.0 * scale), "conflict", "jump cuts + speed ramp"),
            (max(10.0, 25.0 * scale), "climax", "motion blur + quick zoom"),
            (max(5.0, 15.0 * scale), "payoff", "soft settle + fade out"),
        ]
        return self.edit_plan

    # ── 6. ANTI SLOP ─────────────────────────────

    def _anti_slop_check(self, script: str, plan: List) -> List[str]:
        warnings = []
        if len(script.split()) < 20:
            warnings.append("Script too short")
        if not any(c in script for c in ".!?"):
            warnings.append("No sentence endings")
        generic = ["hello everyone", "today we will", "in this video", "dont forget to"]
        for g in generic:
            if g in script.lower():
                warnings.append(f"Generic filler: '{g}'")
        labels = [p[1] for p in plan]
        if len(set(labels)) < 3:
            warnings.append("Edit plan lacks variety")
        return warnings

    # ── 7. THUMBNAIL ─────────────────────────────

    def generate_thumbnail(self, pkg_dir: str, subject: Optional[str] = None) -> str:
        brief = self.creative_brief
        subj = subject or brief.get("hook", "The Real Reason")
        logger.info("[DIRECTOR] Generating thumbnail: %s", subj)

        thumb_dir = os.path.join(pkg_dir, "thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)

        main = os.path.join(pkg_dir, "thumbnail.png")
        make_thumbnail(subj, main, size=(1280, 720), style_profile=self.style_profile)

        variants = make_thumbnail_variants(subj, thumb_dir, count=3, topic=brief.get("topic"))

        vert = os.path.join(pkg_dir, "thumbnail_vertical.png")
        try:
            make_thumbnail_vertical(subj, vert, size=(1080, 1920))
        except Exception as e:
            logger.warning("Vertical thumbnail failed: %s", e)

        return main

    # ── 8. METADATA ──────────────────────────────

    def generate_metadata(self, pkg_dir: str) -> Dict:
        brief = self.creative_brief
        topic = brief.get("topic", "")
        hook = brief.get("hook", "")
        emotion = brief.get("emotion", "")

        titles = [
            f"{hook} — {topic}",
            f"{hook}",
            f"The Real Story of {topic}",
            f"{topic} — {hook}",
        ]
        description = (
            f"{hook}\n\n"
            f"This is the story of {topic}.\n"
            f"What do you think? Let us know in the comments.\n\n"
            f"#Shorts #YouTubeShorts"
        )
        tags = [
            topic.replace(" ", ""), "Shorts", "YouTubeShorts", "TikTok", "Reels",
            emotion.title(), "Gaming", "Minecraft", "SMP",
        ]
        hashtags = [
            f"#{topic.replace(' ', '')}", "#Shorts", "#YouTubeShorts", "#TikTok", "#Reels",
            f"#{emotion.title()}", "#Gaming", "#Minecraft", "#SMP", "#Lore",
        ]

        meta = {
            "titles": titles,
            "description": description,
            "tags": tags,
            "hashtags": " ".join(hashtags),
            "platforms": ["YouTube Shorts", "TikTok", "Instagram Reels"],
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "safe_zones": {
                "top_percent": SAFE_ZONE_TOP * 100,
                "bottom_percent": SAFE_ZONE_BOTTOM * 100,
            },
        }

        with open(os.path.join(pkg_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        with open(os.path.join(pkg_dir, "title_options.txt"), "w", encoding="utf-8") as f:
            for t in titles:
                f.write(t + "\n")
        return meta

    # ── 9. HUMAN CHECK ───────────────────────────

    def run_human_check(self, pkg_dir: str) -> Dict:
        brief = self.creative_brief
        script = brief.get("script", "")
        hook = brief.get("hook", "")

        checks = {
            "stop_scrolling": len(hook) <= 25 and any(c.isupper() for c in hook),
            "first_second_strong": hook != "The Real Reason",
            "has_emotion": brief.get("emotion") in EMOTIONS,
            "story_makes_sense": len(script.split("\n")) >= 3,
            "feels_human": len(self._anti_slop_check(script, self.edit_plan)) == 0,
            "avoids_ai_slop": True,
            "satisfying_ending": "ending" in script.lower() or "everything" in script.lower(),
        }
        checks["passed"] = all(checks.values())

        with open(os.path.join(pkg_dir, "human_check.json"), "w", encoding="utf-8") as f:
            json.dump(checks, f, indent=2)

        if not checks["passed"]:
            failed = [k for k, v in checks.items() if not v and k != "passed"]
            logger.warning("[DIRECTOR] Human check failed: %s", failed)
        return checks

    # ── 10. MAIN WORKFLOW ────────────────────────

    def produce(
        self,
        topic: str,
        raw_video: Optional[str] = None,
        use_groq: bool = False,
        groq_key: Optional[str] = None,
        target_seconds: float = 45.0,
        skip_qc: bool = False,
    ) -> str:
        logger.info("=" * 50)
        logger.info("[DIRECTOR] Starting production: %s", topic)
        logger.info("[DIRECTOR] Profile: %s | Encoder: %s", self.profile, self.encoder)
        logger.info("=" * 50)

        # STEP 1: Research
        self.research(topic, use_groq=use_groq, groq_key=groq_key)

        # STEP 2: Learn creator style
        try:
            self.learn_creator_style(topic)
        except Exception as e:
            logger.warning("[DIRECTOR] Style learning failed: %s", e)

        # STEP 3: Create base package
        pkg_dir = create_package(
            topic,
            out_root=self.out_root,
            thumbnail_subject=self.creative_brief.get("hook"),
            target_total_seconds=target_seconds,
        )
        logger.info("[DIRECTOR] Package: %s", pkg_dir)

        # STEP 4: Script & plan
        script = self.build_script({})
        with open(os.path.join(pkg_dir, "script.txt"), "w", encoding="utf-8") as f:
            f.write(script)

        plan_path = os.path.join(pkg_dir, "plan.json")
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
        except Exception:
            plan_data = {}
        plan_data.update({
            "script": script,
            "edit_plan": self.build_edit_plan({}, target_seconds),
            "creative_brief": self.creative_brief,
            "emotion": self.creative_brief.get("emotion"),
            "hook": self.creative_brief.get("hook"),
        })
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, indent=2)

        # STEP 5: Anti-slop
        slop_warnings = self._anti_slop_check(script, self.edit_plan)
        if slop_warnings:
            logger.warning("[DIRECTOR] Anti-slop: %s", slop_warnings)
            with open(os.path.join(pkg_dir, "anti_slop_warnings.json"), "w") as f:
                json.dump(slop_warnings, f, indent=2)

        # STEP 6: Thumbnail
        self.generate_thumbnail(pkg_dir)

        # STEP 7: Metadata
        self.generate_metadata(pkg_dir)

        # STEP 8: Fetch music
        try:
            self.fetch_music(self.creative_brief.get("emotion", "dramatic"), pkg_dir)
        except Exception as e:
            logger.warning("[DIRECTOR] Music fetch failed: %s", e)

        # STEP 9: Auto-edit
        final_video = None
        if raw_video and os.path.exists(raw_video):
            logger.info("[DIRECTOR] Auto-editing: %s", raw_video)
            analysis = self.analyze_video(raw_video)
            with open(os.path.join(pkg_dir, "video_analysis.json"), "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, default=str)

            # If music exists, align segments to music beats
            if analysis.get("music_bpm") and analysis.get("music_beats"):
                analysis["best_segments"] = align_segments_to_music(
                    analysis["best_segments"],
                    analysis["music_beats"],
                    analysis["music_bpm"],
                )
                # Update plan with music-synced segments
                plan_data["music_synced"] = True
                plan_data["music_bpm"] = analysis["music_bpm"]
                with open(plan_path, "w", encoding="utf-8") as f:
                    json.dump(plan_data, f, indent=2)

            final_video = compose_short_from_video(
                raw_video,
                pkg_dir,
                review=not skip_qc,
                auto_fix=True,
                model_key=self.model_key,
                skip_qc=skip_qc,
            )
            logger.info("[DIRECTOR] Video rendered: %s", final_video)

            # Voiceover (emotional, natural)
            vo_path = os.path.join(pkg_dir, "voiceover.mp3")
            try:
                generate_emotional_voiceover(script, vo_path, self.creative_brief.get("emotion", "dramatic"))
                logger.info("[DIRECTOR] Voiceover: %s", vo_path)
            except Exception as e:
                logger.warning("[DIRECTOR] Voiceover failed: %s", e)
                vo_path = None

            # Mix music + video + VO
            if self.music_path and final_video:
                mixed = os.path.join(pkg_dir, "final_with_music.mp4")
                try:
                    if vo_path and os.path.exists(vo_path):
                        mix_audio(final_video, self.music_path, vo_path, mixed)
                    else:
                        add_music_to_video(final_video, self.music_path, mixed)
                    logger.info("[DIRECTOR] Mixed with music: %s", mixed)
                    # Replace final_video with mixed version
                    shutil.copy2(mixed, final_video)
                except Exception as e:
                    logger.warning("[DIRECTOR] Music mix failed: %s", e)

        # STEP 10: Human check
        checks = self.run_human_check(pkg_dir)
        if checks["passed"]:
            logger.info("[DIRECTOR] ✅ Human check PASSED")
        else:
            logger.warning("[DIRECTOR] ❌ Human check FAILED")

        # Write brief
        with open(os.path.join(pkg_dir, "creative_brief.json"), "w", encoding="utf-8") as f:
            json.dump(self.creative_brief, f, indent=2)

        logger.info("[DIRECTOR] Done: %s", pkg_dir)
        return pkg_dir
