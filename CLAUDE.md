# Sound Engine

A browser-based music engine for synthesizing, sequencing, and performing music with code. Built on Tone.js and the Web Audio API.

## Origin

Started as a test bed for RALF gesture recognition — a way to hear the output of gesture-to-music mapping without needing Ableton Live. The soulful house demo proved that browser-based synthesis + a reactive gesture engine can produce genuinely good music. Now growing into a standalone tool for designing and performing generative/interactive music.

## What This Is

A **programmable music environment** that runs in a browser. Not a DAW replacement — a creative tool for people who think about music structurally and want to design systems that make music, not just sequences that play music.

Think of it as: **"What if your music could listen and respond?"**

## Key Architectural Principle: Performance Config is Portable Data

The system has a strict separation between **what should happen** (performance config) and **how it happens** (runtime):

```
┌─────────────────────────────────────┐
│  PERFORMANCE CONFIG (portable data) │  ← .perf.json
│  gestures, streams, stacks,         │
│  intents, signals, scenes           │
└──────────────┬──────────────────────┘
               │ consumed by
       ┌───────┴───────┐
       │               │
  ┌────▼─────┐   ┌─────▼──────┐
  │ Sound    │   │ Max4Live   │
  │ Engine   │   │ / Ableton  │
  │ (browser)│   │ / anything │
  └──────────┘   └────────────┘
```

**Rules for performance configs:**
- Pure JSON, no code — no functions, no runtime-specific references
- Track references by **name** (e.g., `"perc"`), not by index
- Conditions expressed as data (e.g., `{ "state": "playing", "min_elapsed_ms": 300000 }`)
- Action names are a shared **action vocabulary** — each runtime implements them differently

This means you design a performance once and run it in the browser, in Ableton, or in any future runtime.

## The Four-System Reactive Engine

The reactive layer maps input events to musical actions through four systems:

1. **Streams** — Rate-based windowed counters. "How fast is this happening?" Fires when rate exceeds threshold within a time window. (e.g., "6 energy-down gestures in 5 seconds → frantic_strip")
2. **Stacks** — Accumulation counters with threshold triggers. "How many times has this happened total?" Fires at milestones, optionally resets. (e.g., "every 15 total moves → breakthrough")
3. **Intents** — Weighted random action pools. Non-deterministic musical choices. The same intent resolves to different actions each time, creating organic variation. (e.g., "strip_energy" might filter sweep OR mute perc OR drench in reverb)
4. **Signals** — Gated direct commands. Conditional on system state, deterministic. (e.g., "stop" only fires if playing and elapsed > 5 minutes)

**Data flow:** Input event → feed streams + stacks → check thresholds → resolve intents → execute actions

This is an emerging language for describing reactive musical behavior. Future direction: visual UX for designing and manipulating these mappings.

## Action Vocabulary

Actions are the contract between performance config and runtime. Current vocabulary:

| Action | Args | Description |
|--------|------|-------------|
| `start_playing` | — | Begin transport |
| `stop_playing` | — | Stop transport |
| `fire_scene` | `scene` | Jump to scene by index |
| `fire_next_scene` | — | Advance to next scene |
| `mute_track` | `track` | Mute a track |
| `unmute_track` | `track` | Unmute a track |
| `timed_unmute` | `track`, `duration` | Unmute temporarily |
| `emphasis_track` | `track`, `boost`, `duration` | Temporary volume boost |
| `hush_master` | `drop`, `duration` | Temporary master volume dip |
| `filter_sweep` | `freq`, `duration` | Sweep master filter to target Hz |
| `breakdown` | `duration` | Kill kick+perc, drench in reverb, sweep down |
| `reverb_throw` | `track`, `duration` | Momentarily drench track in reverb |
| `bass_drop` | — | Silence → kick+bass slam back |
| `tempo_shift` | `bpm`, `duration` | Temporary BPM change |
| `trigger_sample` | `track` | Play a one-shot sample track |

New runtimes (Max4Live, etc.) implement this same vocabulary using their native tools.

## Sample Tracks

Sample tracks are declared in the performance config and created dynamically at load time. Audio files live in `samples/`.

**Config format** (in `.perf.json` → `sample_tracks` array):

```json
{
  "name": "Break",
  "file": "my-loop-120bpm.wav",
  "color": "#f90",
  "volume": -10,
  "sends": { "reverb": -18, "delay": -14 },
  "mode": "loop",
  "interval": "2m",
  "muted_in_scenes": [0, 4]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Display name in UI |
| `file` | yes | Filename in `samples/` directory |
| `color` | no | UI color (default: #aaa) |
| `volume` | no | Channel volume in dB (default: -6) |
| `sends` | no | `{ "reverb": dB, "delay": dB }` send levels |
| `mode` | yes | `"loop"` (transport-synced repeat) or `"oneshot"` (action-triggered) |
| `interval` | loop only | Tone.js time value for loop interval (e.g., `"2m"`, `"1m"`, `"4n"`) |
| `muted_in_scenes` | no | Array of scene indices where this track is muted |

**Track indexing:** Synth tracks occupy indices 0–5, sample tracks start at 6+. All existing actions (mute, unmute, emphasis, reverb throw, etc.) work on sample tracks by index.

**Test samples:** Generate with `node tools/generate-test-samples.js`. Creates synthetic WAV files in `samples/`.

## Architecture

```
server.js                — Node.js: HTTP server + OSC→WebSocket bridge + sample serving
index.html               — Browser: Tone.js audio engine + UI
soulful-house.perf.json  — Performance config (portable, runtime-agnostic)
samples/                 — Audio sample files (wav, mp3, ogg, aac, flac)
tools/                   — Development utilities (sample generation, etc.)
docs/roadmap.md          — Project roadmap and future directions
```

## Current Demo: Soulful House (120 BPM, C minor)

Six synth tracks: Kick, Hats, Sub Bass, Chords (Rhodes-ish), Pad, Perc (congas/claps). Two sample tracks: Break (loop), Hit (one-shot). Three gesture mappings: pull-back (energy down), push (energy up), structure shift. Six scenes from Intro through Peak to Drop. Swing at 0.2 on 16ths.

## Quick Start

```bash
npm install
npm start
# Open http://localhost:8080
# Click START, then click gesture buttons or send OSC to port 12000
```

## Commands

```bash
npm start        # Run the server (http://localhost:8080)
```

## Dependencies

- **Tone.js** (CDN, v14.7.77) — Synthesis, scheduling, effects
- **ws** (npm) — WebSocket server for OSC bridge

## OSC Integration

- Input: UDP port 12000, expects `/gesture/N` messages (float arg, typically 1.0)
- Bridges to browser via WebSocket on the same HTTP port (8080)
- Compatible with RALF Gesture Studio output

## Development Workflow

Use judgment to plan appropriately for the task:
- Simple changes: just implement directly.
- Larger changes: think through the approach before coding.
- Always create a feature branch, commit with descriptive messages, and create a PR.

## Code Quality

- Keep performance config strictly as data (no functions in JSON)
- Action names should be descriptive verbs: `mute_track`, not `mt`
- New actions must be documented in the Action Vocabulary table above

## After Completing Work

Before wrapping up a non-trivial PR, self-assess:
- What was the hardest decision or trickiest problem?
- Did anything surprise you or require a workaround?
- Would a future session benefit from knowing this?
If yes, update CLAUDE.md with the pattern or gotcha.
