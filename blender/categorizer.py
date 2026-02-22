"""Select musical primitives from bar-aligned slices.

7 categories, 12-18 total samples per song:
  foundation  — rhythmic anchor (kick pattern)           1-2 loops
  groove      — secondary rhythm (hats, shakers)         1-2 loops
  bass        — distinct bass phrases                    2-3 loops
  harmonic_bed — chord/harmony backbone                  1-2 loops
  hook        — most recognizable melodic fragment       1-2 oneshots
  texture     — atmospheric, ambient, sustained          1-2 loops
  accent      — short punchy moments (ad-libs, fills)    3-5 oneshots
"""

from pathlib import Path

from .slicer import Slice
from .defaults import CATEGORY_LIMITS


def select_primitives(
    stem_slices: dict[str, list[Slice]],
) -> dict[str, list[Slice]]:
    """Select the best samples from each stem into 7 musical primitive categories.

    Args:
        stem_slices: {stem_name: [Slice, ...]} from bar-aligned slicing.
                     Each slice has pre-computed energy and spectral_centroid.

    Returns:
        {category: [Slice, ...]} with each slice's .category field set.
    """
    drums = stem_slices.get("drums", [])
    bass = stem_slices.get("bass", [])
    vocals = stem_slices.get("vocals", [])
    other = stem_slices.get("other", [])

    primitives: dict[str, list[Slice]] = {cat: [] for cat in CATEGORY_LIMITS}

    # --- Foundation: highest transient density bars from drums ---
    if drums:
        by_energy = sorted(drums, key=lambda s: s.energy, reverse=True)
        primitives["foundation"] = _take(by_energy, CATEGORY_LIMITS["foundation"], "foundation")

    # --- Groove: next-best drum bars (different from foundation) ---
    if drums:
        used = {s.start_time for s in primitives["foundation"]}
        remaining = [s for s in drums if s.start_time not in used]
        # Prefer high centroid (hats/shakers tend to be brighter)
        by_centroid = sorted(remaining, key=lambda s: s.spectral_centroid, reverse=True)
        primitives["groove"] = _take(by_centroid, CATEGORY_LIMITS["groove"], "groove")

    # --- Bass: most distinct bass phrases (by spectral contrast) ---
    if bass:
        # Pick most energetic, then most spectrally different
        by_energy = sorted(bass, key=lambda s: s.energy, reverse=True)
        primitives["bass"] = _take_diverse(by_energy, CATEGORY_LIMITS["bass"], "bass")

    # --- Harmonic Bed: longest, most stable section from 'other' stem ---
    if other:
        by_duration = sorted(other, key=lambda s: s.duration_ms, reverse=True)
        primitives["harmonic_bed"] = _take(by_duration, CATEGORY_LIMITS["harmonic_bed"], "harmonic_bed")

    # --- Hook: highest energy + most distinct from vocals ---
    if vocals:
        by_energy = sorted(vocals, key=lambda s: s.energy, reverse=True)
        primitives["hook"] = _take(by_energy, CATEGORY_LIMITS["hook"], "hook")

    # --- Texture: lowest energy sections across all stems ---
    all_slices = drums + bass + vocals + other
    used_paths = {s.path for cat_slices in primitives.values() for s in cat_slices}
    available = [s for s in all_slices if s.path not in used_paths]
    by_low_energy = sorted(available, key=lambda s: s.energy)
    primitives["texture"] = _take(by_low_energy, CATEGORY_LIMITS["texture"], "texture")

    # --- Accent: sharpest transients, shortest duration, across all stems ---
    used_paths = {s.path for cat_slices in primitives.values() for s in cat_slices}
    available = [s for s in all_slices if s.path not in used_paths]
    # Short + high energy = punchy accent
    by_punch = sorted(available, key=lambda s: s.energy / max(s.duration_ms, 1), reverse=True)
    primitives["accent"] = _take(by_punch, CATEGORY_LIMITS["accent"], "accent")

    # Rename all selected files with category prefix
    for category, slices in primitives.items():
        for i, sl in enumerate(slices):
            new_name = f"{category}-{i + 1:02d}.wav"
            new_path = sl.path.parent / new_name
            if sl.path.exists() and sl.path != new_path:
                sl.path.rename(new_path)
                sl.path = new_path

    # Delete unused files
    all_kept = {s.path for cat_slices in primitives.values() for s in cat_slices}
    for stem_slices_list in stem_slices.values():
        for sl in stem_slices_list:
            if sl.path not in all_kept and sl.path.exists():
                sl.path.unlink(missing_ok=True)

    return primitives


def _take(slices: list[Slice], n: int, category: str) -> list[Slice]:
    """Take up to n slices, setting their category."""
    result = slices[:n]
    for s in result:
        s.category = category
    return result


def _take_diverse(slices: list[Slice], n: int, category: str) -> list[Slice]:
    """Take up to n spectrally diverse slices (greedy selection)."""
    if not slices:
        return []
    selected = [slices[0]]
    slices[0].category = category
    for s in slices[1:]:
        if len(selected) >= n:
            break
        # Only add if spectrally different from all selected
        min_dist = min(abs(s.spectral_centroid - sel.spectral_centroid) for sel in selected)
        if min_dist > 200:  # Hz threshold for "different enough"
            s.category = category
            selected.append(s)
    # If we didn't get enough diverse ones, fill with remaining
    if len(selected) < n:
        for s in slices:
            if s not in selected and len(selected) < n:
                s.category = category
                selected.append(s)
    return selected
