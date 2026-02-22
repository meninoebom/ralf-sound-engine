"""Stem separation using Demucs."""

import subprocess
import sys
from pathlib import Path

from .defaults import DEMUCS_MODEL, STEM_NAMES


def separate(song_path: Path, output_dir: Path, model: str = DEMUCS_MODEL) -> dict[str, Path]:
    """Separate a song into stems using Demucs.

    Returns dict mapping stem name to WAV path, e.g.:
        {"drums": Path("output/drums.wav"), "bass": Path("output/bass.wav"), ...}
    """
    song_path = Path(song_path)
    output_dir = Path(output_dir)

    if not song_path.exists():
        raise FileNotFoundError(f"Song not found: {song_path}")

    # Demucs outputs to: output_dir/model_name/track_name/stem.wav
    # We use the default filename pattern and look in the right place.
    cmd = [
        sys.executable, "-m", "demucs",
        "--name", model,
        "--out", str(output_dir),
        "--float32",
        str(song_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError(
            "Demucs is not installed.\n"
            "Install it with: pip install demucs\n"
            "Then try again."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed:\n{e.stderr}")

    # Demucs puts stems in output_dir/model_name/track_name/stem.wav
    song_name = song_path.stem
    stems_dir = output_dir / model / song_name

    stems = {}
    for stem_name in STEM_NAMES:
        stem_path = stems_dir / f"{stem_name}.wav"
        if stem_path.exists():
            stems[stem_name] = stem_path

    if not stems:
        raise RuntimeError(
            f"No stems found in {stems_dir}. "
            f"Expected: {', '.join(STEM_NAMES)}"
        )

    return stems
