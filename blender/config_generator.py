"""Generate .perf.json from sample inventory."""

import json
from pathlib import Path

from .defaults import (
    DRUM_VOLUME_DB, LOOP_VOLUME_DB, DEFAULT_VOLUME_DB,
    DEFAULT_REVERB_SEND_DB, DEFAULT_DELAY_SEND_DB,
    STEM_COLORS, SCENE_TEMPLATES,
)
from .slicer import Slice


def _infer_loop_interval(duration_ms: float, bpm: float) -> str:
    """Infer Tone.js loop interval from slice duration and BPM.

    Snaps to nearest musical duration (1m, 2m, 4m).
    """
    beat_ms = 60000 / bpm
    bar_ms = beat_ms * 4

    bars = duration_ms / bar_ms
    if bars <= 1.5:
        return "1m"
    elif bars <= 3:
        return "2m"
    elif bars <= 6:
        return "4m"
    else:
        return "8m"


def _is_oneshot(stem_name: str, category: str) -> bool:
    """Determine if a sample should be oneshot (True) or loop (False)."""
    if stem_name == "drums":
        return True  # All drum hits are oneshot
    if category == "texture":
        return True   # Short textures are oneshot
    return False  # Phrases are loops


def generate_config(
    sample_inventory: dict[str, list[Slice]],
    bpm: float,
    song_name: str,
    samples_dir: Path,
) -> dict:
    """Generate a complete .perf.json from categorized samples.

    sample_inventory: {stem_name: [Slice, ...]} where each Slice.path
                      has the categorized filename (e.g., drums-kick-01.wav)
    """
    sample_tracks = []
    stem_track_indices: dict[str, list[int]] = {s: [] for s in sample_inventory}

    # Track index starts at 0 (no synth tracks in blender output)
    track_idx = 0

    for stem_name, slices in sample_inventory.items():
        color = STEM_COLORS.get(stem_name, "#aaa")

        for sl in slices:
            filename = sl.path.name
            # Extract category from filename: "drums-kick-01.wav" → "kick"
            parts = filename.replace(".wav", "").split("-")
            category = parts[1] if len(parts) >= 3 else "sample"

            oneshot = _is_oneshot(stem_name, category)
            display_name = f"{stem_name.title()} {category.title()} {parts[-1] if len(parts) >= 3 else ''}"

            track = {
                "name": display_name.strip(),
                "file": filename,
                "color": color,
                "volume": DRUM_VOLUME_DB if stem_name == "drums" else (
                    LOOP_VOLUME_DB if not oneshot else DEFAULT_VOLUME_DB
                ),
                "sends": {
                    "reverb": DEFAULT_REVERB_SEND_DB,
                    "delay": DEFAULT_DELAY_SEND_DB,
                },
                "mode": "oneshot" if oneshot else "loop",
            }

            if not oneshot:
                track["interval"] = _infer_loop_interval(sl.duration_ms, bpm)

            # Muted-in-scenes: derive from scene templates
            muted_scenes = []
            for scene_idx, scene in enumerate(SCENE_TEMPLATES):
                if scene["mutes"].get(stem_name, False):
                    muted_scenes.append(scene_idx)
            if muted_scenes:
                track["muted_in_scenes"] = muted_scenes

            sample_tracks.append(track)
            stem_track_indices[stem_name].append(track_idx)
            track_idx += 1

    # Collect oneshot indices for trigger_sample actions
    drum_indices = stem_track_indices.get("drums", [])
    vocal_indices = stem_track_indices.get("vocals", [])
    bass_indices = stem_track_indices.get("bass", [])
    other_indices = stem_track_indices.get("other", [])
    all_indices = list(range(track_idx))

    # Build intent pools referencing actual track indices
    def _trigger_actions(indices, weight=1):
        return [{"action": "trigger_sample", "args": {"track": i}, "weight": weight} for i in indices[:4]]

    def _mute_actions(indices, weight=1):
        return [{"action": "mute_track", "args": {"track": i}, "weight": weight} for i in indices[:3]]

    def _unmute_actions(indices, weight=1):
        return [{"action": "unmute_track", "args": {"track": i}, "weight": weight} for i in indices[:3]]

    config = {
        "version": "0.1",
        "name": f"{song_name} (Blended)",
        "bpm": bpm,
        "swing": 0,
        "swing_subdivision": "16n",

        "tracks": [],  # No synth tracks — pure samples

        "gestures": {
            "/gesture/1": {
                "name": "pull back",
                "streams": {"energy_down": 1, "all_movement": 1},
                "stacks": {"total_moves": 1, "pull_back_streak": 1},
                "intents": ["strip_energy"],
                "signals": ["stop"],
            },
            "/gesture/2": {
                "name": "push energy",
                "streams": {"energy_up": 1, "all_movement": 1},
                "stacks": {"total_moves": 1, "push_streak": 1},
                "intents": ["add_energy"],
                "signals": ["start"],
            },
            "/gesture/3": {
                "name": "structure shift",
                "streams": {"structure_rate": 1, "all_movement": 1},
                "stacks": {"total_moves": 1, "structure_count": 1},
                "intents": ["shift_structure"],
                "signals": [],
            },
        },

        "streams": {
            "energy_down": {
                "window_ms": 5000,
                "thresholds": [{"above": 6, "action": {"intent": "frantic_strip"}}],
            },
            "energy_up": {
                "window_ms": 5000,
                "thresholds": [{"above": 6, "action": {"intent": "explosive_build"}}],
            },
            "structure_rate": {
                "window_ms": 5000,
                "thresholds": [{"above": 4, "action": {"intent": "total_reset"}}],
            },
            "all_movement": {
                "window_ms": 5000,
                "thresholds": [{"above": 10, "action": {"intent": "peak_frenzy"}}],
            },
        },

        "stacks": {
            "total_moves": {
                "triggers": [
                    {"at": 5, "action": {"intent": "minor_shift"}, "reset": False},
                    {"at": 15, "action": {"intent": "breakthrough"}, "reset": True},
                ],
            },
            "pull_back_streak": {
                "triggers": [{"at": 5, "action": {"intent": "full_breakdown"}, "reset": True}],
            },
            "push_streak": {
                "triggers": [{"at": 5, "action": {"intent": "scene_advance"}, "reset": True}],
            },
            "structure_count": {
                "triggers": [{"at": 3, "action": {"intent": "structure_payoff"}, "reset": True}],
            },
        },

        "intents": {
            "strip_energy": (
                [{"action": "filter_sweep", "args": {"freq": 300, "duration": 3000}, "weight": 3}]
                + [{"action": "hush_master", "args": {"drop": 0.4, "duration": 2500}, "weight": 2}]
                + _mute_actions(drum_indices, 2)
            ),
            "add_energy": (
                _unmute_actions(drum_indices, 2)
                + _trigger_actions(drum_indices[:2], 2)
                + [{"action": "filter_sweep", "args": {"freq": 20000, "duration": 2000}, "weight": 1}]
            ),
            "shift_structure": [
                {"action": "fire_next_scene", "weight": 3},
                {"action": "breakdown", "args": {"duration": 6000}, "weight": 2},
            ],
            "frantic_strip": [
                {"action": "breakdown", "args": {"duration": 8000}, "weight": 2},
                {"action": "filter_sweep", "args": {"freq": 150, "duration": 5000}, "weight": 2},
                {"action": "hush_master", "args": {"drop": 0.6, "duration": 4000}, "weight": 1},
            ],
            "explosive_build": [
                {"action": "bass_drop", "weight": 2},
                {"action": "fire_scene", "args": {"scene": 3}, "weight": 2},
            ],
            "total_reset": [
                {"action": "bass_drop", "weight": 2},
                {"action": "fire_scene", "args": {"scene": 4}, "weight": 1},
                {"action": "fire_scene", "args": {"scene": 5}, "weight": 1},
            ],
            "peak_frenzy": [
                {"action": "fire_scene", "args": {"scene": 3}, "weight": 2},
                {"action": "bass_drop", "weight": 1},
            ],
            "minor_shift": (
                _trigger_actions(vocal_indices[:2], 2)
                + [{"action": "filter_sweep", "args": {"freq": 600, "duration": 3000}, "weight": 1}]
            ),
            "breakthrough": [
                {"action": "fire_next_scene", "weight": 3},
                {"action": "bass_drop", "weight": 2},
                {"action": "breakdown", "args": {"duration": 8000}, "weight": 1},
            ],
            "full_breakdown": [
                {"action": "breakdown", "args": {"duration": 10000}, "weight": 3},
                {"action": "filter_sweep", "args": {"freq": 200, "duration": 6000}, "weight": 1},
            ],
            "scene_advance": [
                {"action": "fire_next_scene", "weight": 3},
                {"action": "bass_drop", "weight": 1},
            ],
            "structure_payoff": [
                {"action": "fire_next_scene", "weight": 2},
                {"action": "breakdown", "args": {"duration": 6000}, "weight": 2},
                {"action": "bass_drop", "weight": 1},
            ],
        },

        "signals": {
            "start": {
                "action": "start_playing",
                "condition": {"state_equals": "stopped"},
            },
            "stop": {
                "action": "stop_playing",
                "condition": {"state_equals": "playing", "min_elapsed_ms": 300000},
            },
        },

        "scenes": [
            {"name": s["name"], "mutes": [], "desc": s["name"]}
            for s in SCENE_TEMPLATES
        ],

        "sample_tracks": sample_tracks,
    }

    # Filter out empty intent pools
    config["intents"] = {k: v for k, v in config["intents"].items() if v}

    return config


def write_config(config: dict, output_path: Path) -> None:
    """Write .perf.json to disk."""
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
