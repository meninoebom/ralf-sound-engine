"""CLI entry point: python -m blender song.mp3"""

import argparse
import sys
from pathlib import Path

from .pipeline import blend


def main():
    parser = argparse.ArgumentParser(
        prog="blender",
        description="The Blender — turn any song into a performable remix.",
    )
    parser.add_argument("song", type=Path, help="Path to song file (mp3, wav, flac, etc.)")
    parser.add_argument("--bpm", type=float, default=None, help="Override auto-detected BPM")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: current dir)")
    parser.add_argument("--min-duration", type=int, default=100, help="Min slice duration in ms (default: 100)")
    parser.add_argument("--stems", type=str, default=None, help="Comma-separated stems to keep (e.g., drums,bass,vocals)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed analysis output")

    args = parser.parse_args()

    song = args.song.expanduser().resolve()
    if not song.exists():
        print(f"Error: File not found: {song}")
        sys.exit(1)

    stems_filter = None
    if args.stems:
        stems_filter = [s.strip() for s in args.stems.split(",")]

    print(f'Blending "{song.name}"')

    try:
        blend(
            song_path=song,
            output_dir=args.output_dir,
            bpm_override=args.bpm,
            min_duration_ms=args.min_duration,
            stems_filter=stems_filter,
            verbose=args.verbose,
        )
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
