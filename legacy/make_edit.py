"""CLI tool for requesting video edits from AI Video Factory.

Usage:
    python make_edit.py "Minecraft" "make a betrayal edit"
    python make_edit.py "Roblox" "create a difficult obby challenge video"
    python make_edit.py "COD" "create a 1v5 clutch moment showcase"
    python make_edit.py "Valorant" "make a perfect execute guide"

The script learns from each request and improves its editing over time.
"""
import sys
import argparse
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_video_factory.request_handler import create_edit


def main():
    parser = argparse.ArgumentParser(
        description="Create a video edit from a topic and request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python make_edit.py "Minecraft" "make a betrayal edit"
  python make_edit.py "Roblox" "create an obby challenge"
  python make_edit.py "COD" "make a 1v5 clutch compilation"

Topics: Minecraft, Roblox, COD, Valorant, and many more
        """
    )

    parser.add_argument("topic", help="Topic (Minecraft, Roblox, COD, Valorant, etc.)")
    parser.add_argument("request", help="What to create (e.g., 'make a betrayal edit')")
    parser.add_argument("--duration", type=float, default=45.0, help="Video duration in seconds (30-60, default 45)")
    parser.add_argument("--output", default="output", help="Output directory (default: output)")
    parser.add_argument("--thumbnail", help="Optional thumbnail subject override")

    args = parser.parse_args()

    # Validate duration
    if args.duration < 30 or args.duration > 60:
        print(f"Error: Duration must be 30-60 seconds (got {args.duration})")
        return 1

    print(f"Creating edit...")
    print(f"  Topic: {args.topic}")
    print(f"  Request: {args.request}")
    print(f"  Duration: {args.duration}s")
    print()

    # Process request
    success, message, pkg_dir = create_edit(
        args.topic,
        args.request,
        output_root=args.output,
        target_seconds=args.duration,
        thumbnail_subject=args.thumbnail,
    )

    print(message)

    if success:
        print()
        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print(f"Package directory: {pkg_dir}")
        print()
        print("Next steps:")
        print("  1. Review the generated plan.json for editing structure")
        print("  2. Review the script.srt for voiceover timing")
        print("  3. Run auto_edit to process the video")
        print("  4. Review the output short in the package directory")
        return 0
    else:
        print()
        print("=" * 70)
        print("FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
