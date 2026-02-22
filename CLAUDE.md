# Sound Engine

A browser-based music engine for synthesizing, sequencing, and performing music with code. Built on Tone.js and the Web Audio API.

## Origin

Started as a test bed for RALF gesture recognition — a way to hear the output of gesture-to-music mapping without needing Ableton Live. The soulful house demo proved that browser-based synthesis + a reactive gesture engine can produce genuinely good music. Now growing into a standalone tool for designing and performing generative/interactive music.

## What This Is

A **programmable music environment** that runs in a browser. Not a DAW replacement — a creative tool for people who think about music structurally and want to design systems that make music, not just sequences that play music.

Think of it as: **"What if your music could listen and respond?"**

## Architecture

```
server.js      — Node.js: HTTP server + OSC→WebSocket bridge
index.html     — Browser: Tone.js audio engine + reactive gesture system + UI
```

Currently a single-file browser app. As we add primitives, we'll extract modules.

## The Four-System Engine (Current)

The existing reactive layer maps gestures to musical actions through four systems:

1. **Streams** — Rate-based windowed counters ("6 energy-down gestures in 5 seconds")
2. **Stacks** — Accumulation counters with threshold triggers ("every 15 total moves")
3. **Intents** — Weighted random action pools (non-deterministic musical choices)
4. **Signals** — Gated direct commands (conditional on state)

This is the *reactive/performance* layer. The primitives below are the *sound design* layer underneath it.

## Quick Start

```bash
npm install
npm start
# Open http://localhost:8080
# Click START, then click gesture buttons or send OSC
```

## Commands

```bash
npm start        # Run the server (http://localhost:8080)
```

## Development Workflow

Use judgment to plan appropriately for the task:
- Simple changes: just implement directly.
- Larger changes: think through the approach before coding.
- Always create a feature branch, commit with descriptive messages, and create a PR.

## After Completing Work

Before wrapping up a non-trivial PR, self-assess:
- What was the hardest decision or trickiest problem?
- Did anything surprise you or require a workaround?
- Would a future session benefit from knowing this?
If yes, update CLAUDE.md with the pattern or gotcha.
