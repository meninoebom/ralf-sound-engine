"""Centralized defaults for the Blender pipeline."""

# Stem separation
DEMUCS_MODEL = "htdemucs"
STEM_NAMES = ["drums", "bass", "vocals", "other"]

# Onset detection (used for accent slicing fallback)
MIN_SLICE_DURATION_MS = 500
FADE_OUT_MS = 10
MAX_SLICES_PER_STEM = 30

# Category limits: 12-18 total samples per song
CATEGORY_LIMITS = {
    "foundation": 2,
    "groove": 2,
    "bass": 3,
    "harmonic_bed": 2,
    "hook": 2,
    "texture": 2,
    "accent": 5,
}

# Category → mode and default interval
CATEGORY_MODES = {
    "foundation":   {"mode": "loop",    "interval": "1m"},
    "groove":       {"mode": "loop",    "interval": "1m"},
    "bass":         {"mode": "loop",    "interval": "2m"},
    "harmonic_bed": {"mode": "loop",    "interval": "4m"},
    "hook":         {"mode": "oneshot", "interval": None},
    "texture":      {"mode": "loop",    "interval": "4m"},
    "accent":       {"mode": "oneshot", "interval": None},
}

# Category colors for UI
CATEGORY_COLORS = {
    "foundation":   "#f90",
    "groove":       "#fa0",
    "bass":         "#4af",
    "harmonic_bed": "#af4",
    "hook":         "#f4a",
    "texture":      "#8af",
    "accent":       "#f84",
}

# Volume defaults per category (dB)
CATEGORY_VOLUMES = {
    "foundation":   -6,
    "groove":       -8,
    "bass":         -6,
    "harmonic_bed": -10,
    "hook":         -6,
    "texture":      -14,
    "accent":       -6,
}

DEFAULT_REVERB_SEND_DB = -14
DEFAULT_DELAY_SEND_DB = -18

# 5 density-layer scenes (start sparse, build UP)
# Each scene lists which categories are ACTIVE (unmuted)
DENSITY_SCENES = [
    {"name": "Bare",     "active": ["texture"]},
    {"name": "Skeletal", "active": ["texture", "harmonic_bed"]},
    {"name": "Groove",   "active": ["foundation", "groove", "bass"]},
    {"name": "Full",     "active": ["foundation", "groove", "bass", "harmonic_bed"]},
    {"name": "Peak",     "active": ["foundation", "groove", "bass", "harmonic_bed", "texture"]},
]
# NOTE: hook and accent are NEVER scene-controlled — always gesture-triggered

STARTING_SCENE = 1  # Skeletal

# Stem colors for UI (legacy, kept for compatibility)
STEM_COLORS = {
    "drums": "#f90",
    "bass": "#4af",
    "vocals": "#f4a",
    "other": "#af4",
}
