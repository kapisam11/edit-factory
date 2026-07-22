"""Main runner for AI Clip Factory.

Wires together package creation, optional interactive review, auto-edit
composition, music mixing, thumbnail generation, and NLE exports.

Usage examples:
  python main.py --topic "Minecraft story" --out output --auto-edit --input-video path/to/video.mp4 --interactive
"""
import argparse
import os
import subprocess
import shutil

from ai_video_factory.factory import create_package


def mix_music(video_path: str, music_path: str, out_path: str, music_volume: float = 0.6):
    out_dir = os.path.dirname(out_path) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    # apply volume to music input and map that audio track
    filter_spec = f"[1:a]volume={music_volume}[a]"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        music_path,
        "-filter_complex",
        filter_spec,
        "-map",
        "0:v:0",
        "-map",
        "[a]",
        "-c:v",
        "copy",
        "-shortest",
        out_path,
    ]
    try:
        subprocess.run(cmd, check=True)
        return out_path
    except Exception:
        return ""


def run_factory(topic: str, out_root: str = "output", input_video: str = None, auto_edit: bool = False, interactive: bool = False, review: bool = False, auto_fix: bool = False, model_key: str = None, elevenlabs_key: str = None, use_groq: bool = False, groq_key: str = None, target_total_seconds: float = 45.0, config_path: str = None):
    print("Creating package for:", topic)
    # allow pruning overrides to be passed via main runner
    prune_min_match = getattr(run_factory, "prune_min_match", 0.25)
    prune_min_motion = getattr(run_factory, "prune_min_motion", 0.07)
    prune_require_faces = getattr(run_factory, "prune_require_faces", None)

    pkg = create_package(topic, out_root=out_root, use_groq=use_groq, groq_api_key=groq_key, prune_min_match=prune_min_match, prune_min_motion=prune_min_motion, prune_require_faces=prune_require_faces, target_total_seconds=target_total_seconds, config_path=config_path)
    print("Package created:", pkg)

    # optional HQ TTS generation before composition
    if elevenlabs_key and os.path.exists(os.path.join(pkg, "script.txt")):
        try:
            from ai_video_factory.tts import generate_high_quality_voiceover
            with open(os.path.join(pkg, "script.txt"), "r", encoding="utf-8") as f:
                txt = f.read()
            vo_out = os.path.join(pkg, "voice_hq.mp3")
            generate_high_quality_voiceover(txt, vo_out, elevenlabs_key)
            print("Generated high-quality voiceover:", vo_out)
        except Exception as e:
            print("HQ TTS failed:", e)

    # interactive review before composing
    if interactive:
        try:
            from ai_video_factory.interactive_review import interactive_review
            interactive_review(pkg, use_model=review, model_key=model_key, prefer_local=True)
        except Exception as e:
            print("Interactive review failed:", e)

    output_final = None
    if auto_edit and input_video:
        try:
            from ai_video_factory.auto_edit import compose_short_from_video
            output_final = compose_short_from_video(input_video, pkg, review=review, auto_fix=auto_fix, model_key=model_key)
            print("Composed short at:", output_final)
        except Exception as e:
            print("Auto-edit failed:", e)

    # add music if available
    if output_final and os.path.isdir("music"):
        try:
            from ai_video_factory.music import choose_music
            music = choose_music("music")
            if music:
                mixed = os.path.join(pkg, "final_with_music.mp4")
                res = mix_music(output_final, music, mixed)
                if res:
                    output_final = res
                    print("Added music, new output:", output_final)
        except Exception as e:
            print("Music mixing failed:", e)

    # create thumbnail
    try:
        from ai_video_factory.thumbnail import make_thumbnail_vertical
        subject = topic
        # prefer plan hook if exists
        try:
            import json
            with open(os.path.join(pkg, "plan.json"), "r", encoding="utf-8") as f:
                plan = json.load(f)
                subject = plan.get("hook") or subject
        except Exception:
            pass
        thumb_out = os.path.join(pkg, "thumbnail_vertical.png")
        make_thumbnail_vertical(subject, thumb_out)
        print("Thumbnail created:", thumb_out)
    except Exception as e:
        print("Thumbnail creation failed:", e)

    # copy final into package and export NLE files
    if output_final:
        try:
            import shutil
            final_dest = os.path.join(pkg, os.path.basename(output_final))
            shutil.copy(output_final, final_dest)
            print("Copied final to package:", final_dest)
        except Exception:
            pass

        try:
            from ai_video_factory.nle_project import export_fcpxml, export_premiere_xml
            # look for clip segments folder if available
            clips_dir = os.path.join(pkg, "_clips")
            seq = []
            if os.path.isdir(clips_dir):
                seq = [os.path.join(clips_dir, p) for p in sorted(os.listdir(clips_dir)) if p.endswith('.mp4')]
            if not seq:
                seq = [final_dest]
            fcpx = export_fcpxml(pkg, seq)
            prem = export_premiere_xml(pkg, seq)
            print("Exported FCPXML:", fcpx)
            print("Exported Premiere XML:", prem)
        except Exception as e:
            print("NLE export failed:", e)

    print("Run complete. Package:", pkg)
    return pkg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--out", default="output")
    p.add_argument("--prune-min-match", type=float, default=0.25, help="Minimum match_score to keep visuals")
    p.add_argument("--prune-min-motion", type=float, default=0.07, help="Minimum motion_score to keep visuals")
    p.add_argument("--prune-require-faces", default=None, help="Comma-separated purpose tags that require faces (e.g. hook,payoff)")
    p.add_argument("--config", default=None, help="Path to per-project JSON config (aivf_config.json). Overrides defaults where present.")
    p.add_argument("--use-spacy-persona", action="store_true", help="Use spaCy NER to improve persona extraction (auto-installs spaCy/model if missing)")
    p.add_argument("--input-video", default=None)
    p.add_argument("--auto-edit", action="store_true")
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--review", action="store_true")
    p.add_argument("--auto-fix", action="store_true")
    p.add_argument("--model-key", default=None)
    p.add_argument("--elevenlabs-key", default=None)
    p.add_argument("--use-groq", action="store_true")
    p.add_argument("--groq-key", default=None)
    p.add_argument("--target-total-seconds", type=float, default=45.0, help="Target structure length in seconds (default 45; use 60 for the full outline)")
    args = p.parse_args()

    # attach pruning prefs to run_factory so they propagate without changing signature everywhere
    try:
        run_factory.prune_min_match = float(args.prune_min_match)
        run_factory.prune_min_motion = float(args.prune_min_motion)
        if args.prune_require_faces:
            run_factory.prune_require_faces = [s.strip() for s in args.prune_require_faces.split(",") if s.strip()]
        else:
            run_factory.prune_require_faces = None
    except Exception:
        pass

    run_factory(args.topic, out_root=args.out, input_video=args.input_video, auto_edit=args.auto_edit, interactive=args.interactive, review=args.review, auto_fix=args.auto_fix, model_key=args.model_key, elevenlabs_key=args.elevenlabs_key, use_groq=args.use_groq, groq_key=args.groq_key, target_total_seconds=args.target_total_seconds, config_path=args.config)


if __name__ == "__main__":
    main()
