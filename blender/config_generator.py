"""Generate .perf.json from musical primitives."""

import json
from pathlib import Path

from .slicer import Slice
from .defaults import (
    CATEGORY_MODES, CATEGORY_COLORS, CATEGORY_VOLUMES,
    DEFAULT_REVERB_SEND_DB, DEFAULT_DELAY_SEND_DB,
    DENSITY_SCENES, STARTING_SCENE,
)


def _infer_interval(duration_ms: float, bpm: float, default: str) -> str:
    """Snap slice duration to nearest musical interval."""
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


def generate_config(
    primitives: dict[str, list[Slice]],
    bpm: float,
    song_name: str,
    samples_dir: Path,
) -> dict:
    """Generate a complete .perf.json from categorized musical primitives.

    primitives: {category: [Slice, ...]} from select_primitives()
    """
    sample_tracks = []
    category_indices: dict[str, list[int]] = {}
    track_idx = 0

    # Category display order
    category_order = ["foundation", "groove", "bass", "harmonic_bed", "hook", "texture", "accent"]

    for category in category_order:
        slices = primitives.get(category, [])
        if not slices:
            continue

        category_indices[category] = []
        mode_def = CATEGORY_MODES[category]
        color = CATEGORY_COLORS.get(category, "#aaa")
        volume = CATEGORY_VOLUMES.get(category, -8)

        for i, sl in enumerate(slices):
            display_name = f"{category.replace('_', ' ').title()} {i + 1}"
            mode = mode_def["mode"]

            track = {
                "name": display_name,
                "file": sl.path.name,
                "color": color,
                "category": category,
                "volume": volume,
                "sends": {
                    "reverb": DEFAULT_REVERB_SEND_DB,
                    "delay": DEFAULT_DELAY_SEND_DB,
                },
                "mode": mode,
            }

            if mode == "loop":
                default_interval = mode_def["interval"] or "2m"
                track["interval"] = _infer_interval(sl.duration_ms, bpm, default_interval)

            # Muted-in-scenes: muted in any scene where this category is NOT active
            # Hook and accent are always unmuted (gesture-triggered, not scene-controlled)
            if category not in ("hook", "accent"):
                muted_scenes = []
                for scene_idx, scene in enumerate(DENSITY_SCENES):
                    if category not in scene["active"]:
                        muted_scenes.append(scene_idx)
                if muted_scenes:
                    track["muted_in_scenes"] = muted_scenes

            sample_tracks.append(track)
            category_indices[category].append(track_idx)
            track_idx += 1

    # Build scenes (no synth track mutes — pure sample engine)
    scenes = []
    for scene in DENSITY_SCENES:
        scenes.append({
            "name": scene["name"],
            "mutes": [],  # no synth tracks
            "desc": f"Active: {', '.join(scene['active'])}",
        })

    # Build intent pools using category indices
    hook_indices = category_indices.get("hook", [])
    accent_indices = category_indices.get("accent", [])
    bass_indices = category_indices.get("bass", [])

    def _trigger_pool(indices, weight=1):
        return [{"action": "trigger_sample", "args": {"track": i}, "weight": weight} for i in indices]

    config = {
        "version": "0.2",
        "name": f"{song_name} (Blended)",
        "bpm": bpm,
        "swing": 0,
        "swing_subdivision": "16n",

        "tracks": [],

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
            "strip_energy": [
                {"action": "scene_down", "weight": 3},
                {"action": "filter_sweep", "args": {"freq": 300, "duration": 3000}, "weight": 2},
                {"action": "hush_master", "args": {"drop": 0.4, "duration": 2500}, "weight": 1},
            ],
            "add_energy": [
                {"action": "scene_up", "weight": 3},
                {"action": "trigger_hook", "weight": 2},
            ] + _trigger_pool(accent_indices, 2),
            "shift_structure": [
                {"action": "swap_variant", "weight": 3},
                {"action": "breakdown", "args": {"duration": 6000}, "weight": 2},
                {"action": "trigger_hook", "weight": 1},
            ],
            "frantic_strip": [
                {"action": "scene_down", "weight": 2},
                {"action": "breakdown", "args": {"duration": 8000}, "weight": 2},
                {"action": "hush_master", "args": {"drop": 0.6, "duration": 4000}, "weight": 1},
            ],
            "explosive_build": [
                {"action": "scene_up", "weight": 2},
                {"action": "trigger_hook", "weight": 2},
                {"action": "bass_drop", "weight": 1},
            ],
            "total_reset": [
                {"action": "fire_scene", "args": {"scene": 0}, "weight": 2},
                {"action": "bass_drop", "weight": 1},
            ],
            "peak_frenzy": [
                {"action": "fire_scene", "args": {"scene": 4}, "weight": 2},
            ] + _trigger_pool(hook_indices, 1) + _trigger_pool(accent_indices, 1),
            "minor_shift": [
                {"action": "trigger_accent", "weight": 2},
                {"action": "swap_variant", "weight": 1},
            ],
            "breakthrough": [
                {"action": "scene_up", "weight": 3},
                {"action": "trigger_hook", "weight": 2},
                {"action": "bass_drop", "weight": 1},
            ],
            "full_breakdown": [
                {"action": "fire_scene", "args": {"scene": 0}, "weight": 2},
                {"action": "breakdown", "args": {"duration": 10000}, "weight": 2},
            ],
            "scene_advance": [
                {"action": "scene_up", "weight": 3},
                {"action": "trigger_accent", "weight": 1},
            ],
            "structure_payoff": [
                {"action": "swap_variant", "weight": 2},
                {"action": "scene_up", "weight": 2},
                {"action": "trigger_hook", "weight": 1},
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

        "scenes": scenes,
        "sample_tracks": sample_tracks,
        "starting_scene": STARTING_SCENE,

        # Category index map for engine actions (trigger_hook, trigger_accent, swap_variant)
        "category_indices": {k: v for k, v in category_indices.items() if v},
    }

    # Filter out empty intent pools
    config["intents"] = {k: v for k, v in config["intents"].items() if v}

    return config


def write_config(config: dict, output_path: Path) -> None:
    """Write .perf.json to disk."""
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
