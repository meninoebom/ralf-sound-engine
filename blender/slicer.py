"""Slice audio stems at onset points."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from .defaults import MIN_SLICE_DURATION_MS, FADE_OUT_MS


@dataclass
class Slice:
    path: Path
    duration_ms: float
    start_time: float  # seconds into original stem


def slice_stem(
    stem_path: Path,
    onset_times: list[float],
    output_dir: Path,
    stem_name: str,
    min_duration_ms: int = MIN_SLICE_DURATION_MS,
    fade_out_ms: int = FADE_OUT_MS,
) -> list[Slice]:
    """Slice a stem WAV at onset points and save individual samples.

    Returns list of Slice objects with path, duration, and start time.
    """
    audio, sr = sf.read(str(stem_path))

    # If stereo, keep stereo
    is_stereo = audio.ndim == 2

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fade_samples = int(sr * fade_out_ms / 1000)
    min_samples = int(sr * min_duration_ms / 1000)

    slices = []
    total_samples = len(audio)

    # Add end of file as final boundary
    boundaries = list(onset_times) + [total_samples / sr]

    for i, start_sec in enumerate(onset_times):
        start_sample = int(start_sec * sr)
        end_sec = boundaries[i + 1]
        end_sample = int(end_sec * sr)

        # Clamp to file bounds
        start_sample = max(0, start_sample)
        end_sample = min(total_samples, end_sample)

        chunk = audio[start_sample:end_sample]
        if is_stereo:
            chunk = chunk.copy()
        else:
            chunk = chunk.copy()

        # Skip short slices
        if len(chunk) < min_samples:
            continue

        # Apply fade-out to prevent clicks
        if fade_samples > 0 and len(chunk) > fade_samples:
            fade = np.linspace(1.0, 0.0, fade_samples)
            if is_stereo:
                chunk[-fade_samples:] *= fade[:, np.newaxis]
            else:
                chunk[-fade_samples:] *= fade

        # Save
        filename = f"{stem_name}-{i + 1:02d}.wav"
        out_path = output_dir / filename
        sf.write(str(out_path), chunk, sr)

        duration_ms = len(chunk) / sr * 1000
        slices.append(Slice(path=out_path, duration_ms=duration_ms, start_time=start_sec))

    return slices
