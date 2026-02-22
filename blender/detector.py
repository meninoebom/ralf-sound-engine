"""Beat and onset detection using Librosa."""

from pathlib import Path

import librosa
import numpy as np


def detect_bpm(audio_path: Path) -> float:
    """Detect BPM of an audio file.

    Returns estimated BPM as a float (e.g., 120.0).
    """
    y, sr = librosa.load(str(audio_path), sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # tempo can be an array in some librosa versions
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    return round(float(tempo), 1)


def detect_onsets(audio_path: Path, is_drums: bool = False) -> list[float]:
    """Detect onset times in an audio file.

    Uses more sensitive settings for drums, less sensitive for melodic stems
    to avoid over-slicing piano/vocal/bass content.
    """
    y, sr = librosa.load(str(audio_path), sr=None)

    if is_drums:
        # Drums: default sensitivity works well
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames")
    else:
        # Melodic content: raise the detection threshold to only catch
        # significant note onsets, not every subtle variation
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(
            y=y, sr=sr, units="frames",
            onset_envelope=onset_env,
            delta=0.3,       # Higher threshold (default ~0.07)
            wait=15,         # Min frames between onsets (~350ms at 22050/512)
        )

    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    return onset_times.tolist()


def detect_bar_boundaries(audio_path: Path, bpm: float) -> list[float]:
    """Detect bar boundaries (every 4 beats) aligned to the beat grid.

    Uses librosa beat tracking to find actual beat positions, then groups them
    into bars. This produces musically useful loop boundaries.

    Returns list of times in seconds at the start of each bar.
    """
    y, sr = librosa.load(str(audio_path), sr=None)
    duration = len(y) / sr

    # Get beat positions from librosa
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, bpm=bpm)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    if len(beat_times) < 4:
        # Not enough beats detected — fall back to BPM-based grid
        bar_duration = 4 * 60.0 / bpm
        return [i * bar_duration for i in range(int(duration / bar_duration) + 1)]

    # Group beats into bars (every 4 beats)
    bar_boundaries = [beat_times[i] for i in range(0, len(beat_times), 4)]

    return bar_boundaries


def get_duration(audio_path: Path) -> float:
    """Get duration of an audio file in seconds."""
    return float(librosa.get_duration(path=str(audio_path)))
