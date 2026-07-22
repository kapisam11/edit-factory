"""Automated short composer using ffmpeg and project plan.

This module provides utilities to create a rough vertical short (9:16)
from a single input video. It is intended to produce a human-editable
rough-cut that follows the `edit_plan` durations in the package `plan.json`.

Notes:
- Requires `ffmpeg` on PATH.
- Output is a best-effort automated edit; human polish is still required
  to reach the MAIN GOAL, but this gets much of the mechanical work done.
"""
import os
import subprocess
import json
from typing import List, Tuple, Optional, Dict, Any

from .edit_automation import detect_non_silent_segments, generate_trim_commands
from .tts import generate_voiceover
from .edit_automation import _get_duration
from .hardware import choose_encoder, ffmpeg_preset_for
from .subtitle_tools import script_to_srt

try:
    import librosa  # type: ignore
except Exception:
    librosa = None


def _get_duration_safe(path: str) -> float:
    try:
        return _get_duration(path)
    except Exception:
        return 0.0


def _run(cmd: str) -> int:
    print("RUN:", cmd)
    return subprocess.call(cmd, shell=True)


def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def _build_cinematic_filter(index: int, label: str, duration: float, filter_effectiveness: Optional[Dict[str, Any]] = None) -> str:
    """Build cinematic filter chain with optional effectiveness-aware selection.
    
    Args:
        index: Segment index for variation
        label: Effect label (e.g., "jump cut", "motion blur")
        duration: Segment duration
        filter_effectiveness: Optional dict of effect_name -> effectiveness rating (0.0-1.0)
                            If provided, only applies effects with effectiveness > 0.75
    """
    # Default effectiveness ratings if not provided (from learning system)
    if filter_effectiveness is None:
        filter_effectiveness = {}
    
    zoom_base = 1.04 + ((index % 4) * 0.01)
    # Vary crop position every shot: cycle through patterns for constant visual change
    pattern = index % 3
    if pattern == 0:
        x_crop = (index % 2) * 8  # 0 or 8
        y_crop = ((index + 1) % 3) * 3  # 3, 0, or 3
    elif pattern == 1:
        x_crop = ((index + 1) % 2) * 12  # 0 or 12
        y_crop = ((index) % 3) * 4  # 0, 4, or 8
    else:
        x_crop = ((index + 2) % 2) * 10  # 0 or 10
        y_crop = ((index + 2) % 3) * 3  # 3, 0, or 3

    vf = (
        f"scale=iw*{zoom_base}:ih*{zoom_base},crop=1080:1920:x={x_crop}:y={y_crop},"
        f"eq=contrast=1.10:brightness=0.00:saturation=1.10"
    )
    label_lower = label.lower()
    
    # Helper function to check if filter is worth applying
    def should_apply_effect(effect_name: str, default_threshold: float = 0.75) -> bool:
        """Check if effect should be applied based on effectiveness rating."""
        if effect_name in filter_effectiveness:
            effectiveness = filter_effectiveness[effect_name].get("effectiveness", 0.5) if isinstance(filter_effectiveness[effect_name], dict) else filter_effectiveness[effect_name]
            return effectiveness >= default_threshold
        # If no effectiveness data, apply high-value effects
        return True

    if ("jump cut" in label_lower or "impact frame" in label_lower) and should_apply_effect("jump_cut", 0.85):
        vf += ",tblend=all_mode='lighten':all_opacity=0.30"
    if ("quick zoom" in label_lower or "punchy zoom" in label_lower) and should_apply_effect("zoom_effect"):
        vf += ",zoompan=z='if(lte(on,1),1.1,1.05)':d=1"
    if "motion blur" in label_lower and should_apply_effect("motion_blur", 0.70):
        vf += ",tblend=all_mode='average':all_opacity=0.55"
    if "subtle shake" in label_lower and should_apply_effect("subtle_shake", 0.80):
        vf += f",crop=1080:1920:x='if(gt(mod(t,0.12),0.06),{x_crop+1},{x_crop})':y='if(gt(mod(t,0.12),0.06),{y_crop+1},{y_crop})'"
    if "speed ramp" in label_lower and should_apply_effect("speed_ramp", 0.82):
        vf += ",tblend=all_mode='add':all_opacity=0.18"
    if "cinematic transition" in label_lower and should_apply_effect("cinematic_transition", 0.80):
        vf += ",fade=t=in:st=0:d=0.12"
    if "soft settle" in label_lower and should_apply_effect("eq_effect"):
        vf += ",eq=gamma=1.04"
    if ("camera move" in label_lower or "pan" in label_lower) and should_apply_effect("pan_effect"):
        vf += ",pan=x='1920/2+(iw/2-1920/2)*if(lte(t,{:.1f}),t/{:.1f},1)':y='1080/2'".format(duration, duration)
    if ("hook" in label_lower or "payoff" in label_lower) and should_apply_effect("unsharp_effect"):
        vf += ",unsharp=3:3:0.5"
    if "Main event" in label and duration > 1.5 and should_apply_effect("boxblur"):
        vf += ",boxblur=1:1"
    return vf


def _make_srt_from_script(script: str, durations: List[float], out_path: str):
    """Create a simple SRT splitting `script` into chunks matching `durations`.

    This uses a naive word-based split to produce 2-6 words per line.
    """
    words = script.split()
    idx = 0
    items = []
    for i, dur in enumerate(durations):
        # aim for 4 words per subtitle line, adjust by duration
        target_words = max(2, min(6, int(round(len(words) / max(1, len(durations))))))
        chunk = words[idx: idx + target_words]
        if not chunk:
            break
        text = " ".join(chunk)
        items.append((i + 1, i, i + 1, text, dur))
        idx += len(chunk)

    # write SRT with progressive timestamps
    with open(out_path, "w", encoding="utf-8") as f:
        t = 0.0
        for i, start_sec, end_sec, text, dur in items:
            start = _sec_to_srt(t)
            t += dur
            end = _sec_to_srt(t)
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


def _sec_to_srt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def compose_short_from_video(input_video: str, package_dir: str, out_file: Optional[str] = None, review: bool = True, auto_fix: bool = False, model_key: Optional[str] = None) -> str:
    """Create a rough vertical short following `plan.json` inside `package_dir`.

    Steps:
      - detect non-silent segments
      - trim candidate clips
      - assemble a sequence following `edit_plan` durations
      - generate SRT subtitles from `script`
      - optionally generate TTS and mix
      - scale/pad to 1080x1920 and export H.264 MP4

    Returns path to exported file.
    """
    _ensure_dir(package_dir)
    if out_file is None:
        out_file = os.path.join(package_dir, "final_short.mp4")

    # Initialize defaults
    edit_plan = [(6, "segment")]
    script = ""

    # run final checks and optionally model-driven review; abort unless checks pass
    try:
        from .quality_control import run_final_checks
        checks = run_final_checks(package_dir)
        if not checks.get("ok", False):
            raise RuntimeError("Final quality checks failed: " + "; ".join(checks.get("notes", [])))
    except RuntimeError:
        # re-raise to caller
        raise
    except Exception:
        # if checks cannot run treat as warning and continue
        checks = {}

    if review:
        try:
            from .review import run_review, apply_auto_fixes
            report = run_review(package_dir, use_model=bool(model_key), model_key=model_key or "")
            # if not ok and auto_fix enabled, attempt conservative fixes and reload plan/script
            if not report.get("ok", True) and auto_fix:
                applied = apply_auto_fixes(package_dir)
                if applied:
                    # reload plan/script
                    try:
                        with open(os.path.join(package_dir, "plan.json"), "r", encoding="utf-8") as f:
                            plan = json.load(f)
                            edit_plan = plan.get("edit_plan", edit_plan)
                            script = plan.get("script", script)
                    except Exception:
                        pass
        except Exception:
            pass

    # load plan/script
    try:
        with open(os.path.join(package_dir, "plan.json"), "r", encoding="utf-8") as f:
            plan = json.load(f)
    except Exception:
        plan = {}

    # Update from loaded plan if available
    edit_plan = plan.get("edit_plan", edit_plan)
    script = plan.get("script", script)

    # detect segments (non-silent) and fallback to evenly spaced windows if none
    segments = detect_non_silent_segments(input_video)
    if not segments:
        dur = _get_duration_safe(input_video)
        if dur <= 0:
            segments = [(0.0, 10.0)]
        else:
            # split video into windows of ~4s
            step = max(2.0, min(6.0, dur / 8))
            segments = [(i, min(i + step, dur)) for i in [j * step for j in range(int(dur // step))]]

    temp_dir = os.path.join(package_dir, "_clips")
    _ensure_dir(temp_dir)

    # optional: compute beats and align shot cuts to nearest beat (if librosa available)
    beats = None
    if librosa:
        try:
            y, sr = librosa.load(input_video, sr=None, mono=True)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beats = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        except Exception:
            beats = None

    # create trims for first N segments
    trim_cmds = generate_trim_commands(input_video, segments[: len(edit_plan)], temp_dir)
    clip_paths = []
    for cmd in trim_cmds:
        _run(cmd)
        out = cmd.split()[-1].strip('"')
        clip_paths.append(out)

    # Load knowledge context if available (from learning system)
    filter_effectiveness = {}
    try:
        knowledge_file = os.path.join(package_dir, "knowledge_context.json")
        if os.path.exists(knowledge_file):
            with open(knowledge_file, "r", encoding="utf-8") as f:
                knowledge_data = json.load(f)
                # Try to load filter effectiveness from knowledge system
                try:
                    from .knowledge import KnowledgeBase
                    kb = KnowledgeBase()
                    filter_effectiveness = kb.filter_effectiveness
                except Exception:
                    pass
    except Exception:
        pass

    # create per-segment trimmed files matching edit_plan durations and apply cinematic effects
    seq_files = []
    durations = []
    for i, seg in enumerate(edit_plan):
        duration = float(seg[0]) if isinstance(seg, (list, tuple)) else float(seg)
        label = seg[1] if isinstance(seg, (list, tuple)) and len(seg) > 1 else "segment"
        durations.append(duration)
        src_clip = clip_paths[i % len(clip_paths)]
        dst = os.path.join(temp_dir, f"segment_{i:02d}.mp4")
        # Pass filter effectiveness to cinematic filter builder
        vf = _build_cinematic_filter(i, label, duration, filter_effectiveness if filter_effectiveness else None)

        # if beats are available, align trim end to nearest beat boundary
        ss = 0.0
        to = duration
        if beats:
            # find a beat near the desired duration and snap to it if within 0.25s
            desired_end = duration
            nearest = min(beats, key=lambda b: abs(b - desired_end)) if beats else None
            if nearest and abs(nearest - desired_end) < 0.25:
                to = nearest

        cmd = f"ffmpeg -y -i \"{src_clip}\" -ss {ss:.3f} -t {to:.3f} -vf \"{vf}\" -c:v libx264 -c:a aac -b:a 128k \"{dst}\""
        _run(cmd)
        seq_files.append(dst)

    # apply motion-graphics templates if available
    try:
        from .templates import find_templates, apply_overlay

        templates = find_templates()
        if templates:
            templ_dir = os.path.join(package_dir, "_templ")
            _ensure_dir(templ_dir)
            templ_seq = []
            for i, s in enumerate(seq_files):
                overlay = templates[i % len(templates)]
                outp = os.path.join(templ_dir, os.path.basename(s))
                apply_overlay(s, overlay, outp)
                templ_seq.append(outp)
            seq_files = templ_seq
    except Exception:
        pass

    # write concat list
    concat_list = os.path.join(temp_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in seq_files:
            f.write(f"file '{p}'\n")

    # generate subtitles using subtitle_tools for better time estimates
    srt_path = os.path.join(package_dir, "script.srt")
    try:
        script_to_srt(script, srt_path)
    except Exception:
        _make_srt_from_script(script, durations, srt_path)

    # optional TTS voiceover (best-effort)
    vo_path = os.path.join(package_dir, "voice.mp3")
    try:
        generate_voiceover(script, vo_path)
        has_vo = True
    except Exception:
        has_vo = False

    encoder = choose_encoder()
    preset = ffmpeg_preset_for(encoder)
    codec = preset.get("codec", "libx264")
    vcodec = codec
    x264_opts = ""
    if "h264_nvenc" in codec or "hevc_nvenc" in codec:
        x264_opts = f"-preset {preset.get('preset', 'p5')} -rc {preset.get('rc', 'vbr_hq')} -b:v {preset.get('bitrate', '6000k')}"
    else:
        x264_opts = f"-preset {preset.get('preset', 'slow')} -crf {preset.get('crf', '20')}"

    ff_cmd = (
        f"ffmpeg -y -f concat -safe 0 -i \"{concat_list}\" -i \"{srt_path}\" "
        f"-c:v {vcodec} {x264_opts} -c:a aac -vf \"subtitles={srt_path}\" -movflags +faststart \"{out_file}\""
    )
    _run(ff_cmd)

    if has_vo:
        mixed = os.path.join(package_dir, "final_short_vo.mp4")
        mix_cmd = f"ffmpeg -y -i \"{out_file}\" -i \"{vo_path}\" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest \"{mixed}\""
        _run(mix_cmd)
        return mixed

    return out_file
