"""Simple automated editing helpers using ffmpeg.

This module provides utilities to detect non-silent segments in a video's
audio track and to generate ffmpeg commands to trim those segments into clips.

Requires `ffmpeg` available on PATH.
"""
import re
import subprocess
from typing import List, Tuple


def detect_non_silent_segments(video_path: str, silence_thresh: float = -35.0, min_silence_len: float = 0.4) -> List[Tuple[float, float]]:
    """Use ffmpeg's silencedetect to find non-silent segments.

    Returns a list of (start, end) in seconds representing non-silent windows.
    """
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-af",
        f"silencedetect=noise={silence_thresh}dB:d={min_silence_len}",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    stderr = proc.stderr

    # parse silence_start and silence_end
    silence_starts = [float(m.group(1)) for m in re.finditer(r"silence_start: ([0-9.]+)", stderr)]
    silence_ends = [float(m.group(1)) for m in re.finditer(r"silence_end: ([0-9.]+)", stderr)]

    # build non-silent segments by inverting silence
    segments: List[Tuple[float, float]] = []
    # if no silence detected, return whole duration
    if not silence_starts and not silence_ends:
        # try to get duration
        dur = _get_duration(video_path)
        if dur:
            return [(0.0, dur)]
        return []

    # Ensure alignment
    points = []
    # start with 0
    points.append(0.0)
    for s in silence_starts:
        points.append(s)
    # append video end
    dur = _get_duration(video_path) or (silence_ends[-1] if silence_ends else None)
    if dur:
        points.append(dur)

    # pairwise intervals, skip silent intervals
    # For a simple approach, assume silence_starts/ends alternate and build non-silent between them
    last = 0.0
    for end in silence_ends:
        if last < end:
            segments.append((last, end))
        # find next silence start after this end
        next_starts = [s for s in silence_starts if s > end]
        last = next_starts[0] if next_starts else (dur or end)

    # final segment
    if segments and dur and segments[-1][1] < dur:
        segments.append((segments[-1][1], dur))

    # normalize and filter very short segments
    cleaned = [(max(0.0, s), min(e, dur)) for s, e in segments if e - s > 0.35]
    return cleaned


def _get_duration(path: str) -> float:
    """Return duration of media using ffprobe (seconds) or 0 if unknown."""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return float(out.strip())
    except Exception:
        return 0.0


def generate_trim_commands(video_path: str, segments: List[Tuple[float, float]], out_dir: str) -> List[str]:
    """Return ffmpeg command lines to trim the given segments to files in out_dir."""
    cmds = []
    for i, (s, e) in enumerate(segments):
        out = f"{out_dir}/clip_{i:03d}.mp4"
        # use -ss -to for accurate trimming (re-encode for simplicity)
        cmd = f"ffmpeg -y -i \"{video_path}\" -ss {s:.3f} -to {e:.3f} -c:v libx264 -c:a aac -b:a 128k \"{out}\""
        cmds.append(cmd)
    return cmds
