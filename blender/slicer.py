"""Slice audio stems at bar boundaries or onset points."""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from .defaults import MIN_SLICE_DURATION_MS, FADE_OUT_MS, MAX_SLICES_PER_STEM


@dataclass
class Slice:
    path: Path
    duration_ms: float
    start_time: float  # seconds into original stem
    category: str = ""  # filled by categorizer
    energy: float = 0.0  # RMS energy, used for selection
    spectral_centroid: float = 0.0  # Hz, used for selection


def slice_at_bars(
    stem_path: Path,
    bar_boundaries: list[float],
    output_dir: Path,
    stem_name: str,
    fade_out_ms: int = FADE_OUT_MS,
) -> list[Slice]:
    """Slice a stem at bar boundaries, producing musically-aligned loops.

    Each slice spans one or more bars. Returns Slice objects with
    pre-computed energy and spectral centroid for downstream selection.
    """
    import librosa

    audio, sr = sf.read(str(stem_path))
    is_stereo = audio.ndim == 2
    total_samples = len(audio)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fade_samples = int(sr * fade_out_ms / 1000)
    slices = []

    # Add end-of-file as final boundary
    boundaries = list(bar_boundaries) + [total_samples / sr]

    for i in range(len(boundaries) - 1):
        start_sec = boundaries[i]
        end_sec = boundaries[i + 1]
        start_sample = max(0, int(start_sec * sr))
        end_sample = min(total_samples, int(end_sec * sr))

        chunk = audio[start_sample:end_sample].copy()
        if len(chunk) < sr * 0.25:  # skip chunks shorter than 250ms
            continue

        # Apply fade-out
        if fade_samples > 0 and len(chunk) > fade_samples:
            fade = np.linspace(1.0, 0.0, fade_samples)
            if is_stereo:
                chunk[-fade_samples:] *= fade[:, np.newaxis]
            else:
                chunk[-fade_samples:] *= fade

        # Compute analysis features (mono for analysis)
        mono = chunk.mean(axis=1) if is_stereo else chunk
        rms = float(np.sqrt(np.mean(mono ** 2)))
        # Spectral centroid via librosa
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=mono.astype(np.float32), sr=sr)))

        filename = f"{stem_name}-bar-{i + 1:02d}.wav"
        out_path = output_dir / filename
        sf.write(str(out_path), chunk, sr)

        duration_ms = len(chunk) / sr * 1000
        slices.append(Slice(
            path=out_path,
            duration_ms=duration_ms,
            start_time=start_sec,
            energy=rms,
            spectral_centroid=centroid,
        ))

    return slices


def slice_stem(
    stem_path: Path,
    onset_times: list[float],
    output_dir: Path,
    stem_name: str,
    min_duration_ms: int = MIN_SLICE_DURATION_MS,
    fade_out_ms: int = FADE_OUT_MS,
    max_slices: int = MAX_SLICES_PER_STEM,
) -> list[Slice]:
    """Slice a stem WAV at onset points and save individual samples.

    Returns list of Slice objects with path, duration, and start time.
    """
    import librosa

    audio, sr = sf.read(str(stem_path))
    is_stereo = audio.ndim == 2
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fade_samples = int(sr * fade_out_ms / 1000)
    min_samples = int(sr * min_duration_ms / 1000)

    slices = []
    total_samples = len(audio)
    boundaries = list(onset_times) + [total_samples / sr]

    for i, start_sec in enumerate(onset_times):
        start_sample = max(0, int(start_sec * sr))
        end_sec = boundaries[i + 1]
        end_sample = min(total_samples, int(end_sec * sr))

        chunk = audio[start_sample:end_sample].copy()

        if len(chunk) < min_samples:
            continue

        # Apply fade-out
        if fade_samples > 0 and len(chunk) > fade_samples:
            fade = np.linspace(1.0, 0.0, fade_samples)
            if is_stereo:
                chunk[-fade_samples:] *= fade[:, np.newaxis]
            else:
                chunk[-fade_samples:] *= fade

        # Compute analysis features
        mono = chunk.mean(axis=1) if is_stereo else chunk
        rms = float(np.sqrt(np.mean(mono ** 2)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=mono.astype(np.float32), sr=sr)))

        filename = f"{stem_name}-{i + 1:02d}.wav"
        out_path = output_dir / filename
        sf.write(str(out_path), chunk, sr)

        duration_ms = len(chunk) / sr * 1000
        slices.append(Slice(
            path=out_path,
            duration_ms=duration_ms,
            start_time=start_sec,
            energy=rms,
            spectral_centroid=centroid,
        ))

    # Cap at max_slices, keeping the longest
    if len(slices) > max_slices:
        slices.sort(key=lambda s: s.duration_ms, reverse=True)
        for discarded in slices[max_slices:]:
            discarded.path.unlink(missing_ok=True)
        slices = slices[:max_slices]
        slices.sort(key=lambda s: s.start_time)

    return slices
