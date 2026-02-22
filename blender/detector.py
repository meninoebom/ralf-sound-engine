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


def detect_onsets(audio_path: Path, sr: int = None) -> list[float]:
    """Detect onset times in an audio file.

    Returns list of onset times in seconds.
    """
    y, sr = librosa.load(str(audio_path), sr=sr)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames")
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    return onset_times.tolist()


def get_duration(audio_path: Path) -> float:
    """Get duration of an audio file in seconds."""
    return float(librosa.get_duration(path=str(audio_path)))
