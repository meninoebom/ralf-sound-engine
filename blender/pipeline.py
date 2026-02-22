"""Pipeline orchestrator — runs all stages in sequence."""

import shutil
import tempfile
from pathlib import Path

from .separator import separate
from .detector import detect_bpm, detect_bar_boundaries
from .slicer import slice_at_bars
from .categorizer import select_primitives
from .config_generator import generate_config, write_config
from .defaults import STEM_NAMES


def blend(
    song_path: str | Path,
    output_dir: str | Path | None = None,
    bpm_override: float | None = None,
    stems_filter: list[str] | None = None,
    verbose: bool = False,
) -> Path:
    """Run the full Blender pipeline: separate → detect bars → slice → select → config.

    Returns path to the generated .perf.json.
    """
    song_path = Path(song_path).resolve()
    song_name = song_path.stem

    if not song_path.exists():
        raise FileNotFoundError(f"Song not found: {song_path}")

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

        # === Stage 3: Detect bar boundaries and slice each stem ===
        print("\nSlicing at bar boundaries...")
        stem_slices: dict[str, list] = {}

        for stem_name in stem_names:
            stem_path = stems[stem_name]
            log(f"  Analyzing {stem_name}...")

            bar_boundaries = detect_bar_boundaries(stem_path, bpm)
            log(f"    {len(bar_boundaries)} bar boundaries detected")

            slices = slice_at_bars(stem_path, bar_boundaries, samples_dir, stem_name)
            log(f"    {len(slices)} bar slices")
            stem_slices[stem_name] = slices
            print(f"  {stem_name}: {len(slices)} bars")

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    # === Stage 4: Select musical primitives (7 categories) ===
    print("\nSelecting musical primitives...")
    primitives = select_primitives(stem_slices)

    total_samples = 0
    for category, slices in primitives.items():
        if slices:
            print(f"  {category}: {len(slices)} sample(s)")
            total_samples += len(slices)

    # === Stage 5: Generate config ===
    config = generate_config(primitives, bpm, song_name, samples_dir)
    config_path = output_dir / f"{song_name}.perf.json"
    write_config(config, config_path)

    print(f"\nDone! {total_samples} samples + {config_path.name}")
    print(f"\nNext: npm start → open http://localhost:8080 → load {config_path.name}")

    return config_path
