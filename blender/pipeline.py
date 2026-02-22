"""Pipeline orchestrator — runs all stages in sequence."""

import shutil
import tempfile
from pathlib import Path

from .separator import separate
from .detector import detect_bpm, detect_onsets
from .slicer import slice_stem, Slice
from .categorizer import categorize_and_rename
from .config_generator import generate_config, write_config
from .defaults import STEM_NAMES, MIN_SLICE_DURATION_MS


def blend(
    song_path: str | Path,
    output_dir: str | Path | None = None,
    bpm_override: float | None = None,
    min_duration_ms: int = MIN_SLICE_DURATION_MS,
    stems_filter: list[str] | None = None,
    verbose: bool = False,
) -> Path:
    """Run the full Blender pipeline: separate → detect → slice → categorize → config.

    Returns path to the generated .perf.json.
    """
    song_path = Path(song_path).resolve()
    song_name = song_path.stem

    if not song_path.exists():
        raise FileNotFoundError(f"Song not found: {song_path}")

    # Output directory defaults to current dir
    if output_dir is None:
        output_dir = Path.cwd()
    output_dir = Path(output_dir).resolve()

    samples_dir = output_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    log = print if verbose else lambda *a, **k: None

    # === Stage 1: Detect BPM ===
    if bpm_override:
        bpm = bpm_override
        print(f"  BPM: {bpm} (override)")
    else:
        print("  Detecting BPM...")
        bpm = detect_bpm(song_path)
        print(f"  BPM: {bpm}")

    # === Stage 2: Separate stems ===
    print("\nSeparating stems...")
    work_dir = Path(tempfile.mkdtemp(prefix="blender-"))
    try:
        stems = separate(song_path, work_dir)
        stem_names = [s for s in STEM_NAMES if s in stems]
        if stems_filter:
            stem_names = [s for s in stem_names if s in stems_filter]
        print(f"  {' / '.join(stem_names)}")

        # === Stage 3: Detect onsets and slice each stem ===
        print("\nSlicing samples...")
        sample_inventory: dict[str, list[Slice]] = {}
        total_samples = 0

        for stem_name in stem_names:
            stem_path = stems[stem_name]
            log(f"  Analyzing {stem_name}...")

            onsets = detect_onsets(stem_path, is_drums=(stem_name == "drums"))
            log(f"    {len(onsets)} onsets detected")

            slices = slice_stem(
                stem_path, onsets, samples_dir, stem_name,
                min_duration_ms=min_duration_ms,
            )
            log(f"    {len(slices)} slices after filtering")

            # === Stage 4: Categorize and rename ===
            categorized = categorize_and_rename(slices, stem_name)
            sample_inventory[stem_name] = categorized
            total_samples += len(categorized)

            # Count categories for display
            categories: dict[str, int] = {}
            for sl in categorized:
                cat = sl.path.stem.split("-")[1] if "-" in sl.path.stem else "sample"
                categories[cat] = categories.get(cat, 0) + 1
            cat_str = " / ".join(f"{n} {c}" for c, n in categories.items())
            print(f"  {stem_name}: {cat_str}")

    finally:
        # Clean up Demucs temp files
        shutil.rmtree(work_dir, ignore_errors=True)

    # === Stage 5: Generate config ===
    config = generate_config(sample_inventory, bpm, song_name, samples_dir)
    config_path = output_dir / f"{song_name}.perf.json"
    write_config(config, config_path)

    print(f"\nDone! {total_samples} samples + {config_path.name}")
    print(f"\nNext: npm start → open http://localhost:8080 → load {config_path.name}")

    return config_path
