"""Centralized defaults for the Blender pipeline."""

# Stem separation
DEMUCS_MODEL = "htdemucs"
STEM_NAMES = ["drums", "bass", "vocals", "other"]

# Onset detection
MIN_SLICE_DURATION_MS = 500  # Discard slices shorter than this (was 100, too many micro-slices)
FADE_OUT_MS = 10             # Fade-out to prevent clicks at slice boundaries
MAX_SLICES_PER_STEM = 30     # Safety cap — keep the best N slices per stem

# Drum categorization thresholds (spectral centroid in Hz)
KICK_CENTROID_MAX = 500
KICK_MIN_DURATION = 0.1      # seconds
HAT_CENTROID_MIN = 5000
HAT_MAX_DURATION = 0.1
SNARE_CENTROID_MIN = 1000
SNARE_MAX_DURATION = 0.3

# Non-drum categorization
PHRASE_MIN_DURATION = 0.5     # seconds — shorter = "texture", longer = "phrase"

# Config generation
DEFAULT_VOLUME_DB = -8
DRUM_VOLUME_DB = -6
LOOP_VOLUME_DB = -10
DEFAULT_REVERB_SEND_DB = -14
DEFAULT_DELAY_SEND_DB = -18

# Scene templates (mute patterns for 4 stem groups: drums, bass, vocals, other)
# True = muted
SCENE_TEMPLATES = [
    {"name": "Intro",     "mutes": {"drums": True,  "bass": False, "vocals": False, "other": True}},
    {"name": "Groove",    "mutes": {"drums": False, "bass": False, "vocals": True,  "other": True}},
    {"name": "Build",     "mutes": {"drums": False, "bass": False, "vocals": False, "other": True}},
    {"name": "Peak",      "mutes": {"drums": False, "bass": False, "vocals": False, "other": False}},
    {"name": "Breakdown", "mutes": {"drums": True,  "bass": False, "vocals": False, "other": False}},
    {"name": "Drop",      "mutes": {"drums": False, "bass": False, "vocals": False, "other": False}},
]

# Stem colors for UI
STEM_COLORS = {
    "drums": "#f90",
    "bass": "#4af",
    "vocals": "#f4a",
    "other": "#af4",
}
