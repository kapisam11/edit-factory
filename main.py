"""Main runner for AI Clip Factory.

Wires together package creation, optional interactive review, auto-edit
composition, music mixing, thumbnail generation, and NLE exports.

Usage examples:
  python main.py --topic "Minecraft story" --out output --auto-edit --input-video path/to/video.mp4 --interactive
"""
import argparse
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration dataclass (replaces bare kwargs)
# ---------------------------------------------------------------------------
@dataclass
class FactoryConfig:
    topic: str
    out_root: str = "output"
    input_video: Optional[str] = None
    auto_edit: bool = False
    interactive: bool = False
    review: bool = False
    auto_fix: bool = False
    model_key: Optional[str] = None
    elevenlabs_key: Optional[str] = None
    use_groq: bool = False
    groq_key: Optional[str] = None
    target_total_seconds: float = 45.0
    config_path: Optional[str] = None
    prune_min_match: float = 0.25
    prune_min_motion: float = 0.07
    prune_require_faces: Optional[list] = None
    music_volume: float = 0.6
    dry_run: bool = False

    def __post_init__(self):
        if not self.topic or not self.topic.strip():
            raise ValueError("topic must be a non-empty string")
        if self.target_total_seconds <= 0:
            raise ValueError("target_total_seconds must be positive")
        if not (0.0 <= self.music_volume <= 1.0):
            raise ValueError("music_volume must be between 0.0 and 1.0")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def mask_key(key: Optional[str]) -> str:
    """Mask an API key for safe logging."""
    if not key:
        return "None"
    if len(key) <= 12:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg with captured output and clear error messages."""
    logger.debug("ffmpeg command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode}): {result.stderr.strip()}")


def safe_import(module_path: str, item_name: Optional[str] = None):
    """Import a module/item safely with a clear error message."""
    try:
        mod = __import__(module_path, fromlist=[item_name] if item_name else [])
        return getattr(mod, item_name) if item_name else mod
    except ImportError as e:
        raise ImportError(
            f"Failed to import '{module_path}.{item_name or ""}'. "
            f"Is the dependency installed? ({e})"
        ) from e


# ---------------------------------------------------------------------------
# Stage functions (each does one thing, testable in isolation)
# ---------------------------------------------------------------------------
def stage_create_package(cfg: FactoryConfig) -> str:
    """Create the research/package folder."""
    from ai_video_factory.factory import create_package

    logger.info("Creating package for: %s", cfg.topic)
    if cfg.dry_run:
        logger.info("[DRY RUN] Would create package for: %s", cfg.topic)
        return os.path.join(cfg.out_root, "dry_run_package")

    pkg = create_package(
        cfg.topic,
        out_root=cfg.out_root,
        use_groq=cfg.use_groq,
        groq_api_key=cfg.groq_key,
        prune_min_match=cfg.prune_min_match,
        prune_min_motion=cfg.prune_min_motion,
        prune_require_faces=cfg.prune_require_faces,
        target_total_seconds=cfg.target_total_seconds,
        config_path=cfg.config_path,
    )
    logger.info("Package created: %s", pkg)
    return pkg


def stage_generate_voiceover(pkg: str, elevenlabs_key: Optional[str], dry_run: bool = False) -> Optional[str]:
    """Generate high-quality voiceover if ElevenLabs key is provided."""
    script_path = os.path.join(pkg, "script.txt")
    if not elevenlabs_key or not os.path.exists(script_path):
        return None

    logger.info("Generating HQ voiceover (ElevenLabs key: %s)", mask_key(elevenlabs_key))
    if dry_run:
        logger.info("[DRY RUN] Would generate voiceover for: %s", script_path)
        return os.path.join(pkg, "voice_hq.mp3")

    try:
        from ai_video_factory.tts import generate_high_quality_voiceover
        with open(script_path, "r", encoding="utf-8") as f:
            txt = f.read()
        vo_out = os.path.join(pkg, "voice_hq.mp3")
        generate_high_quality_voiceover(txt, vo_out, elevenlabs_key)
        logger.info("Generated high-quality voiceover: %s", vo_out)
        return vo_out
    except Exception as e:
        logger.warning("HQ TTS failed: %s", e)
        return None


def stage_interactive_review(pkg: str, cfg: FactoryConfig) -> None:
    """Let the user review/edit the plan before auto-editing."""
    if not cfg.interactive:
        return

    logger.info("Starting interactive review...")
    if cfg.dry_run:
        logger.info("[DRY RUN] Would launch interactive review for: %s", pkg)
        return

    try:
        from ai_video_factory.interactive_review import interactive_review
        interactive_review(
            pkg,
            use_model=cfg.review,
            model_key=cfg.model_key,
            prefer_local=True,
        )
    except Exception as e:
        logger.warning("Interactive review failed: %s", e)


def stage_auto_edit(pkg: str, cfg: FactoryConfig) -> Optional[str]:
    """Run auto-edit composition if requested."""
    if not (cfg.auto_edit and cfg.input_video):
        return None

    logger.info("Running auto-edit on: %s", cfg.input_video)
    if cfg.dry_run:
        logger.info("[DRY RUN] Would compose short from: %s", cfg.input_video)
        return os.path.join(pkg, "dry_run_final.mp4")

    try:
        from ai_video_factory.auto_edit import compose_short_from_video
        output_final = compose_short_from_video(
            cfg.input_video,
            pkg,
            review=cfg.review,
            auto_fix=cfg.auto_fix,
            model_key=cfg.model_key,
        )
        logger.info("Composed short at: %s", output_final)
        return output_final
    except Exception as e:
        logger.error("Auto-edit failed: %s", e)
        return None


def stage_mix_music(video_path: Optional[str], pkg: str, cfg: FactoryConfig) -> Optional[str]:
    """Mix background music into the final video."""
    if not video_path or not os.path.isdir("music"):
        return video_path

    logger.info("Mixing music into: %s", video_path)
    if cfg.dry_run:
        logger.info("[DRY RUN] Would mix music from 'music/' into: %s", video_path)
        return os.path.join(pkg, "dry_run_with_music.mp4")

    try:
        from ai_video_factory.music import choose_music
        music = choose_music("music")
        if not music:
            logger.info("No suitable music track found in 'music/'")
            return video_path

        mixed = os.path.join(pkg, "final_with_music.mp4")
        _mix_music_ffmpeg(video_path, music, mixed, cfg.music_volume)
        logger.info("Added music, new output: %s", mixed)
        return mixed
    except Exception as e:
        logger.warning("Music mixing failed: %s", e)
        return video_path


def _mix_music_ffmpeg(video_path: str, music_path: str, out_path: str, music_volume: float) -> None:
    """Internal: ffmpeg music mixing with proper error handling."""
    out_dir = os.path.dirname(out_path) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    filter_spec = f"[1:a]volume={music_volume}[a]"
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", filter_spec,
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "copy",
        "-shortest",
        out_path,
    ]
    run_ffmpeg(cmd)


def stage_generate_thumbnail(pkg: str, topic: str, dry_run: bool = False) -> Optional[str]:
    """Generate a vertical thumbnail."""
    logger.info("Generating thumbnail...")
    if dry_run:
        logger.info("[DRY RUN] Would generate thumbnail for: %s", topic)
        return os.path.join(pkg, "dry_run_thumbnail.png")

    try:
        from ai_video_factory.thumbnail import make_thumbnail_vertical

        # Prefer plan hook if available
        subject = topic
        plan_path = os.path.join(pkg, "plan.json")
        if os.path.exists(plan_path):
            try:
                import json
                with open(plan_path, "r", encoding="utf-8") as f:
                    plan = json.load(f)
                subject = plan.get("hook") or subject
            except Exception:
                pass

        thumb_out = os.path.join(pkg, "thumbnail_vertical.png")
        make_thumbnail_vertical(subject, thumb_out)
        logger.info("Thumbnail created: %s", thumb_out)
        return thumb_out
    except Exception as e:
        logger.warning("Thumbnail creation failed: %s", e)
        return None


def stage_export_nle(pkg: str, video_path: Optional[str]) -> None:
    """Copy final video into package and export NLE project files."""
    if not video_path:
        return

    logger.info("Exporting NLE files...")
    try:
        final_dest = os.path.join(pkg, os.path.basename(video_path))
        shutil.copy(video_path, final_dest)
        logger.info("Copied final to package: %s", final_dest)
    except Exception as e:
        logger.warning("Failed to copy final video to package: %s", e)
        return

    try:
        from ai_video_factory.nle_project import export_fcpxml, export_premiere_xml

        clips_dir = os.path.join(pkg, "_clips")
        if os.path.isdir(clips_dir):
            seq = [
                os.path.join(clips_dir, p)
                for p in sorted(os.listdir(clips_dir))
                if p.endswith(".mp4")
            ]
        else:
            seq = [final_dest]

        fcpx = export_fcpxml(pkg, seq)
        prem = export_premiere_xml(pkg, seq)
        logger.info("Exported FCPXML: %s", fcpx)
        logger.info("Exported Premiere XML: %s", prem)
    except Exception as e:
        logger.warning("NLE export failed: %s", e)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_factory(cfg: FactoryConfig) -> str:
    """Run the full factory pipeline with the given configuration."""
    logger.info("=" * 50)
    logger.info("AI Video Factory — starting run")
    logger.info("Topic: %s", cfg.topic)
    logger.info("Output: %s", cfg.out_root)
    logger.info("Auto-edit: %s | Interactive: %s | Dry-run: %s", cfg.auto_edit, cfg.interactive, cfg.dry_run)

    # Stage 1: Create package
    pkg = stage_create_package(cfg)

    # Stage 2: HQ voiceover
    stage_generate_voiceover(pkg, cfg.elevenlabs_key, dry_run=cfg.dry_run)

    # Stage 3: Interactive review
    stage_interactive_review(pkg, cfg)

    # Stage 4: Auto-edit
    output_final = stage_auto_edit(pkg, cfg)

    # Stage 5: Music mixing
    output_final = stage_mix_music(output_final, pkg, cfg)

    # Stage 6: Thumbnail
    stage_generate_thumbnail(pkg, cfg.topic, dry_run=cfg.dry_run)

    # Stage 7: NLE export
    stage_export_nle(pkg, output_final)

    logger.info("Run complete. Package: %s", pkg)
    return pkg


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="AI Video Factory — generate research packages, scripts, thumbnails, and rough-cuts for short-form video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Minecraft betrayal on SMP"
  python main.py --topic "Minecraft story" --auto-edit --input-video recording.mp4
  python main.py --topic "Minecraft story" --dry-run
  python main.py --topic "Minecraft story" --use-groq --groq-key "gsk_..."
        """.strip(),
    )
    p.add_argument("--topic", required=True, help="Video topic / title idea")
    p.add_argument("--out", default="output", help="Output root folder (default: output)")
    p.add_argument(
        "--prune-min-match", type=float, default=0.25,
        help="Minimum match_score to keep visuals (default: 0.25)",
    )
    p.add_argument(
        "--prune-min-motion", type=float, default=0.07,
        help="Minimum motion_score to keep visuals (default: 0.07)",
    )
    p.add_argument(
        "--prune-require-faces", default=None,
        help="Comma-separated purpose tags that require faces (e.g. hook,payoff)",
    )
    p.add_argument(
        "--config", default=None,
        help="Path to per-project JSON config (aivf_config.json). Overrides defaults where present.",
    )
    p.add_argument(
        "--use-spacy-persona", action="store_true",
        help="Use spaCy NER to improve persona extraction (auto-installs spaCy/model if missing)",
    )
    p.add_argument("--input-video", default=None, help="Raw video for auto-edit rough-cut")
    p.add_argument("--auto-edit", action="store_true", help="Enable auto-edit composition")
    p.add_argument("--interactive", action="store_true", help="Review plan.json before composing")
    p.add_argument("--review", action="store_true", help="Use model review during interactive step")
    p.add_argument("--auto-fix", action="store_true", help="Auto-fix issues found during review")
    p.add_argument("--model-key", default=None, help="API key for review model")
    p.add_argument("--elevenlabs-key", default=None, help="ElevenLabs API key for HQ TTS")
    p.add_argument("--use-groq", action="store_true", help="Enable Groq enrichment")
    p.add_argument("--groq-key", default=None, help="Groq API key (overrides GROQ_API_KEY env var)")
    p.add_argument(
        "--target-total-seconds", type=float, default=45.0,
        help="Target structure length in seconds (default: 45; use 60 for full outline)",
    )
    p.add_argument(
        "--music-volume", type=float, default=0.6,
        help="Background music volume multiplier (0.0–1.0, default: 0.6)",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Simulate the pipeline without running ffmpeg or API calls",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    return p


def main():
    p = build_parser()
    args = p.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Build config with validation
    prune_require_faces = None
    if args.prune_require_faces:
        prune_require_faces = [s.strip() for s in args.prune_require_faces.split(",") if s.strip()]

    # Prefer env vars for API keys if not passed via CLI
    groq_key = args.groq_key or os.environ.get("GROQ_API_KEY")
    elevenlabs_key = args.elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY")

    cfg = FactoryConfig(
        topic=args.topic,
        out_root=args.out,
        input_video=args.input_video,
        auto_edit=args.auto_edit,
        interactive=args.interactive,
        review=args.review,
        auto_fix=args.auto_fix,
        model_key=args.model_key,
        elevenlabs_key=elevenlabs_key,
        use_groq=args.use_groq,
        groq_key=groq_key,
        target_total_seconds=args.target_total_seconds,
        config_path=args.config,
        prune_min_match=args.prune_min_match,
        prune_min_motion=args.prune_min_motion,
        prune_require_faces=prune_require_faces,
        music_volume=args.music_volume,
        dry_run=args.dry_run,
    )

    try:
        pkg = run_factory(cfg)
        print(f"\n✅ Success! Package: {pkg}")
        sys.exit(0)
    except Exception as e:
        logger.error("Pipeline failed: %s", e)
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
