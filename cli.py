"""CLI for AI Video Factory — supports both legacy and director workflows.

Usage:
    # Full director workflow (recommended)
    python cli.py "Minecraft betrayal on SMP" --raw-video clip.mp4 --director

    # Legacy package-only mode
    python cli.py "Minecraft betrayal on SMP"

    # With Groq enrichment
    python cli.py "Topic" --raw-video clip.mp4 --use-groq --groq-key $GROQ_API_KEY
"""
import argparse
import os
import sys


def main():
    p = argparse.ArgumentParser(
        description="AI Video Factory — generate upload-ready short video packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Minecraft betrayal on SMP" --raw-video gameplay.mp4 --director
  %(prog)s "Topic" --out output --use-groq
  %(prog)s "Topic" --raw-video clip.mp4 --target-seconds 60 --skip-qc
        """,
    )
    p.add_argument("topic", help="Video topic or title")
    p.add_argument("--out", default="output", help="Output root folder")
    p.add_argument("--raw-video", default=None, help="Path to raw footage for auto-edit")
    p.add_argument("--director", action="store_true", help="Use VideoDirector workflow (full creative pipeline)")
    p.add_argument("--thumbnail-subject", default=None, help="Custom thumbnail subject text")
    p.add_argument("--use-groq", action="store_true", help="Enable Groq research enrichment")
    p.add_argument("--groq-key", default=None, help="Groq API key (or set GROQ_API_KEY env var)")
    p.add_argument("--model-key", default=None, help="Model API key for QC/review (or set OPENAI_API_KEY)")
    p.add_argument("--target-seconds", type=float, default=45.0, help="Target video length (default 45)")
    p.add_argument("--skip-qc", action="store_true", help="Skip quality control checks (faster, for testing)")
    p.add_argument("--interactive", action="store_true", help="Interactive human-in-the-loop review")
    p.add_argument("--elevenlabs-key", default=None, help="ElevenLabs API key for high-quality TTS")
    p.add_argument("--review", action="store_true", help="Run automated review before finalizing")
    p.add_argument("--auto-fix", action="store_true", help="Auto-fix issues found in review")
    p.add_argument("--force-export", action="store_true", help="Force export even if QC fails")
    p.add_argument("--legacy", action="store_true", help="Use legacy producer instead of director")
    args = p.parse_args()

    groq_key = args.groq_key or os.environ.get("GROQ_API_KEY")
    model_key = args.model_key or os.environ.get("OPENAI_API_KEY")

    # —— DIRECTOR WORKFLOW (recommended) ——————————————————————————————
    if args.director or (args.raw_video and not args.legacy):
        from ai_video_factory.director import VideoDirector

        print("=" * 50)
        print("AI VIDEO FACTORY — Director Mode")
        print("Topic:", args.topic)
        print("Raw video:", args.raw_video or "(none)")
        print("Target:", args.target_seconds, "seconds")
        print("=" * 50)

        director = VideoDirector(out_root=args.out, model_key=model_key)
        pkg = director.produce(
            args.topic,
            raw_video=args.raw_video,
            use_groq=args.use_groq,
            groq_key=groq_key,
            target_seconds=args.target_seconds,
            skip_qc=args.skip_qc,
        )
        print("\n✓ Director workflow complete!")
        print("Package:", pkg)

        # Optional: high-quality TTS
        if args.elevenlabs_key:
            from ai_video_factory.tts import generate_high_quality_voiceover
            script_path = os.path.join(pkg, "script.txt")
            if os.path.exists(script_path):
                with open(script_path, "r", encoding="utf-8") as f:
                    text = f.read()
                vo_out = os.path.join(pkg, "voice_hq.mp3")
                try:
                    generate_high_quality_voiceover(text, vo_out, args.elevenlabs_key)
                    print("High-quality VO:", vo_out)
                except Exception as e:
                    print("HQ TTS failed:", e)

        # Optional: interactive review
        if args.interactive:
            from ai_video_factory.interactive_review import interactive_review
            try:
                interactive_review(pkg, use_model=args.review, model_key=model_key, prefer_local=True)
            except Exception as e:
                print("Interactive review failed:", e)

        # Optional: EDL export
        clips_dir = os.path.join(pkg, "_clips")
        if os.path.exists(clips_dir):
            from ai_video_factory.nle_export import export_edl
            seq = [os.path.join(clips_dir, p) for p in sorted(os.listdir(clips_dir)) if p.endswith(".mp4")]
            if seq:
                edl = export_edl(pkg, seq)
                print("EDL:", edl)

        return

    # —— LEGACY WORKFLOW ————————————————————————————————————————
    from ai_video_factory.factory import create_package

    pkg = create_package(
        args.topic,
        out_root=args.out,
        thumbnail_subject=args.thumbnail_subject,
        use_groq=args.use_groq,
        groq_api_key=groq_key,
        target_total_seconds=args.target_seconds,
    )
    print("Package created:", pkg)

    if args.raw_video:
        if not os.path.exists(args.raw_video):
            print("ERROR: Raw video not found:", args.raw_video)
            sys.exit(1)

        if args.interactive:
            from ai_video_factory.interactive_review import interactive_review
            try:
                interactive_review(pkg, use_model=args.review, model_key=model_key, prefer_local=True)
            except Exception as e:
                print("Interactive review failed:", e)

        from ai_video_factory.composer import compose_short_from_video
        from ai_video_factory.nle_export import export_edl

        try:
            out = compose_short_from_video(
                args.raw_video,
                pkg,
                review=args.review,
                auto_fix=args.auto_fix,
                model_key=model_key,
            )
        except Exception as e:
            if args.force_export:
                print("QC failed, force-exporting:", e)
                out = compose_short_from_video(
                    args.raw_video, pkg,
                    review=False, auto_fix=False,
                    model_key=model_key, skip_qc=True,
                )
            else:
                print("Auto-edit aborted:", e)
                sys.exit(1)

        print("Auto-edit output:", out)

        clips_dir = os.path.join(pkg, "_clips")
        if os.path.exists(clips_dir):
            seq = [os.path.join(clips_dir, p) for p in sorted(os.listdir(clips_dir)) if p.endswith(".mp4")]
            if seq:
                edl = export_edl(pkg, seq)
                print("EDL exported:", edl)


if __name__ == "__main__":
    main()