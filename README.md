
# AI Video Factory (scaffold)

This repository contains a lightweight implementation of the AI Video Factory
workflow described in the prompt. It generates a research summary, an edit
plan, sample script, thumbnail mock, and writes an upload-ready package.

Quick start

1. Create a virtual environment and install requirements

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

```text

1. Generate a package for a topic:

```powershell
python cli.py "Minecraft betrayal on SMP"

```text

1. Inspect the output folder under `output/`.

Notes

- This is a scaffold: it does not perform automated video cutting. Use the
  generated `plan.json` and `script.txt` as the human editor's blueprint and
  apply them in your NLE (Premiere, DaVinci, or ffmpeg scripts).

- The thumbnail is a simple mock created with Pillow. Replace it with a
  human-designed thumbnail for best results.

Additional tools and notes

- This scaffold optionally uses `ffmpeg` for trimming, burning subtitles,
  and rendering multi-aspect variants. Install `ffmpeg` and ensure it's on
  your PATH for those features to work.

- The video structure is optional and scalable: the default target is a
  shorter edit, and you can request the full 60-second structure with
  `--target-total-seconds 60`.

- `hooks.weights.json` controls the fast visual hook scoring used by the
  package rerun tools. After changing it, run `python tools/regenerate_visual_hooks.py`
  to refresh hook picks and reports across existing packages.

- `python tools/export_ab_review.py .` writes CSV exports under `reports/`.

- `python tools/build_dashboard.py` generates `reports/dashboard.html` for
  reviewer-friendly visual A/B comparison of top hooks and thumbnails.

- `python tools/export_crowdsource_csv.py` produces `reports/ab_review_crowdsource.csv`
  with direct `file:///` thumbnail links for crowdsourcing and human review.

- `python tools/smoke_test_exporters.py` can be used to verify the NLE XML
  exporters and PSD helper flow with a lightweight synthetic test.

- For beat detection the scaffold uses `librosa` and `numpy` (heavy
  dependencies). If you prefer not to install them, the music chooser will
  still pick a track heuristically.

- TTS uses `pyttsx3` for offline voice generation; voice quality depends on
  your platform's installed voices. For professional voiceovers, record a
  human VO or use a premium voice service.

Example ffmpeg trimming flow (generated commands):

```powershell
ffmpeg -y -i "input.mp4" -ss 12.345 -to 20.500 -c:v libx264 -c:a aac -b:a 128k "clip_000.mp4"

```text

Example render variants (burn subtitles):

```powershell
ffmpeg -y -i "input.mp4" -vf "scale=w=min(1080\,iw):h=min(1920\,ih),pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles=\"script.srt\"" -c:v libx264 -c:a aac "vertical_9_16.mp4"

```text

## Groq (optional)

The project supports optional Groq enrichment for stronger viral angles and
short-form phrasing. Groq is entirely optional — the pipeline works without
it using public web lookups and heuristics.

Enable Groq from the CLI or environment

Powershell example (env var):

```powershell
setx GROQ_API_KEY "gsk_your_key_here"
python cli.py "Minecraft betrayal on SMP" --use-groq

```text

Or pass the key directly:

```powershell
python cli.py "Minecraft betrayal on SMP" --use-groq --groq-key "gsk_your_key_here"

```text

Groq is used only to enrich the research summary (titles, short facts,
viral angle). If Groq calls fail the pipeline continues; no package creation
is blocked by Groq errors.

## CLI reference

The `cli.py` supports the following flags

- `--out`: output root folder (default `output`)

- `--thumbnail-subject`: short subject text used when generating thumbnails

- `--use-groq`: enable optional Groq enrichment (requires an API key)

- `--groq-key`: provide Groq API key directly (overrides `GROQ_API_KEY`)

- `--target-total-seconds`: choose the structure length, default `45` seconds, or set `60` for the full version

Example run (no Groq):

```powershell
python cli.py "His final choice: betrayal on the SMP"

```text

Example run (with Groq enrichment):

```powershell
setx GROQ_API_KEY "gsk_..."
python cli.py "His final choice: betrayal on the SMP" --use-groq

```text

Example run with the full 60-second structure:

```powershell
python cli.py "His final choice: betrayal on the SMP" --target-total-seconds 60

```text

## Automated rough-cut / auto-edit

You can provide a raw recorded video and ask the tool to create a rough
vertical short automatically. This is intended to produce a human-editable
rough-cut that follows the generated `plan.json`.

```powershell

# generate package then run auto-edit in one command

python cli.py "Minecraft betrayal on SMP" --input-video "recording.mp4" --auto-edit

# or run auto-edit after package creation

python cli.py "Minecraft betrayal on SMP"
python cli.py "Minecraft betrayal on SMP" --input-video "recording.mp4" --auto-edit

```text

Notes

- `ffmpeg` must be installed and on PATH.

- The auto-edit is a best-effort rough-cut. Review `output/<pkg>/final_checks.json` and the exported short and perform human polish.

## Beat-sync and higher quality VO

The tool can align cuts to music beats (if `librosa` is installed). Install with

```powershell
pip install librosa

```text

High-quality voiceovers can be generated via ElevenLabs (optional). Set `ELEVENLABS_API_KEY` or pass `--elevenlabs-key` to the CLI. If used, the voice will be saved to `voice_hq.mp3` in the package and mixed into the final short.

## Interactive human-in-the-loop

Use `--interactive` to review and edit the generated `plan.json` hook before auto-editing.

Example end-to-end (recommended)

```powershell
setx ELEVENLABS_API_KEY "your_key_here"
python cli.py "Minecraft betrayal on SMP" --input-video recording.mp4 --auto-edit --interactive --elevenlabs-key "your_key_here"

```text

## Motion-graphics templates

Place PNG overlays (1080x1920 design with transparency) in one of

- `prompt_templates/overlays`

- `templates/overlays`

- `templates`

The pipeline will pick overlays and apply them per segment automatically.
