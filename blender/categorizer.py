"""Categorize audio slices using spectral heuristics."""

from pathlib import Path

import librosa
import numpy as np

from .defaults import (
    KICK_CENTROID_MAX, KICK_MIN_DURATION,
    HAT_CENTROID_MIN, HAT_MAX_DURATION,
    SNARE_CENTROID_MIN, SNARE_MAX_DURATION,
    PHRASE_MIN_DURATION,
)
from .slicer import Slice


def categorize_drum_slice(audio: np.ndarray, sr: int, duration_sec: float) -> str:
    """Classify a drum slice as kick/snare/hat/perc using spectral centroid + duration."""
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))

    if centroid < KICK_CENTROID_MAX and duration_sec > KICK_MIN_DURATION:
        return "kick"
    elif centroid > HAT_CENTROID_MIN and duration_sec < HAT_MAX_DURATION:
        return "hat"
    elif centroid > SNARE_CENTROID_MIN and duration_sec < SNARE_MAX_DURATION:
        return "snare"
    else:
        return "perc"


def categorize_nondrums_slice(duration_sec: float) -> str:
    """Classify a non-drum slice as phrase or texture based on duration."""
    if duration_sec >= PHRASE_MIN_DURATION:
        return "phrase"
    return "texture"


def categorize_and_rename(slices: list[Slice], stem_name: str) -> list[Slice]:
    """Categorize slices and rename files with category prefix.

    For drums: kick/snare/hat/perc classification.
    For other stems: phrase/texture based on duration.

    Returns updated Slice list with renamed paths.
    """
    is_drums = stem_name == "drums"

    # Group by category for sequential numbering
    category_counts: dict[str, int] = {}
    renamed = []

    for sl in slices:
        audio, sr = librosa.load(str(sl.path), sr=None)
        duration_sec = sl.duration_ms / 1000.0

        if is_drums:
            category = categorize_drum_slice(audio, sr, duration_sec)
        else:
            category = categorize_nondrums_slice(duration_sec)

        # Sequential numbering per category
        category_counts[category] = category_counts.get(category, 0) + 1
        num = category_counts[category]

        new_name = f"{stem_name}-{category}-{num:02d}.wav"
        new_path = sl.path.parent / new_name

        sl.path.rename(new_path)
        renamed.append(Slice(path=new_path, duration_ms=sl.duration_ms, start_time=sl.start_time))

    return renamed
