"""Simple CLI for ai_video_factory package."""
import argparse
import os
from ai_video_factory.factory import create_package


def main():
    p = argparse.ArgumentParser(description="AI Video Factory - generate upload package for a short video topic")
    p.add_argument("topic", help="Topic or title to generate the package for")
    p.add_argument("--out", default="output", help="Output root folder")
    p.add_argument("--thumbnail-subject", default=None, help="Short subject text for thumbnail")
    p.add_argument("--use-groq", action="store_true", help="Enable optional Groq enrichment (requires API key)")
    p.add_argument("--groq-key", default=None, help="Groq API key (overrides GROQ_API_KEY env var)")
    p.add_argument("--input-video", default=None, help="Path to input video to auto-edit into a short")
    p.add_argument("--auto-edit", action="store_true", help="Run automated short composition from input video (requires --input-video)")
    p.add_argument("--interactive", action="store_true", help="Run interactive human-in-the-loop prompts before auto-edit")
    p.add_argument("--elevenlabs-key", default=None, help="API key for ElevenLabs (high-quality TTS) - optional")
    p.add_argument("--force-export", action="store_true", help="Force export even if final QC checks fail")
    p.add_argument("--review", action="store_true", help="Run automated review checks before finalizing the short")
    p.add_argument("--auto-fix", action="store_true", help="If review fails, attempt conservative auto-fixes and re-run composition")
    p.add_argument("--model-key", default=None, help="Optional model API key for model-driven suggestions (OPENAI_API_KEY if omitted)")
    p.add_argument("--target-total-seconds", type=float, default=45.0, help="Target structure length in seconds (default 45; use 60 for the full outline)")
    args = p.parse_args()

    groq_key = args.groq_key or os.environ.get("GROQ_API_KEY")
    pkg = create_package(args.topic, out_root=args.out, thumbnail_subject=args.thumbnail_subject, use_groq=args.use_groq, groq_api_key=groq_key, target_total_seconds=args.target_total_seconds)
    print("Package created:", pkg)

    if args.auto_edit:
        if not args.input_video:
            print("--auto-edit requires --input-video")
        else:
            # human-in-the-loop: interactive reviewer accepts/tweaks script and beats
            if args.interactive:
                from ai_video_factory.interactive_review import interactive_review
                try:
                    interactive_review(pkg, use_model=args.review, model_key=args.model_key, prefer_local=True)
                except Exception as e:
                    print("Interactive review failed:", e)

            from ai_video_factory.auto_edit import compose_short_from_video
            from ai_video_factory.nle_export import export_edl
            from ai_video_factory.tts import generate_high_quality_voiceover

            # try high-quality TTS if key provided
            eleven_key = args.elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY")
            if eleven_key:
                try:
                    with open(pkg + "/script.txt", "r", encoding="utf-8") as f:
                        text = f.read()
                    vo_out = os.path.join(pkg, "voice_hq.mp3")
                    generate_high_quality_voiceover(text, vo_out, eleven_key)
                    print("Generated high-quality VO at", vo_out)
                except Exception as e:
                    print("High-quality TTS failed:", e)

            try:
                out = compose_short_from_video(args.input_video, pkg, review=args.review, auto_fix=args.auto_fix, model_key=args.model_key)
            except Exception as e:
                if args.force_export:
                    print("QC failed but --force-export provided, continuing:", e)
                    # attempt a forced export by calling compose_short_from_video skipping QC
                    from ai_video_factory.auto_edit import compose_short_from_video as _compose
                    out = _compose(args.input_video, pkg)
                else:
                    print("Auto-edit aborted due to QC failure:", e)
                    out = ""
            print("Auto-edit output:", out)
            # if sequence clips exist, write a simple EDL for human polish
            clips_dir = os.path.join(pkg, "_clips")
            if os.path.exists(clips_dir):
                seq = [os.path.join(clips_dir, p) for p in sorted(os.listdir(clips_dir)) if p.endswith('.mp4')]
                if seq:
                    edl = export_edl(pkg, seq)
                    print("EDL exported:", edl)
                    # try exporting richer interchange formats for NLEs
                    try:
                        from ai_video_factory.nle_project import export_fcpxml, export_premiere_xml
                        fcpx = export_fcpxml(pkg, seq)
                        premx = export_premiere_xml(pkg, seq)
                        print("FCPXML exported:", fcpx)
                        print("Premiere XML exported:", premx)
                    except Exception as e:
                        print("NLE export failed:", e)


if __name__ == "__main__":
    main()
