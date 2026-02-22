# Sound Engine Roadmap

## Vision

A programmable music environment where you describe *what you want to happen* and the system makes it sound good. Reactive, performable, portable.

---

## Phase 1: Foundation (current)

**Status: In progress**

- [x] Soulful house demo with Tone.js synthesis
- [x] Four-system reactive engine (streams, stacks, intents, signals)
- [x] OSC input via WebSocket bridge
- [x] Manual gesture trigger buttons in UI
- [x] Scene system with mute states
- [ ] Extract performance config to `.perf.json` (portable data)
- [ ] Load performance config at runtime (engine reads JSON, not hardcoded)
- [ ] Define `.perf.json` schema/format spec

## Phase 2: Sound Primitives

**Goal: Make it easy to create new pieces without rewriting synthesis code**

- [ ] **Sample Player** — Load wav/mp3 files, trigger with pitch/speed control. Unlocks drum breaks, vocal chops, found sounds.
- [ ] **Pattern primitive** — Sequences as data (note, velocity, duration, timing). Editable, swappable, generatable.
- [ ] **Track abstraction** — Source → effects → mixer as a composable unit. Named tracks referenced by performance config.
- [ ] **Effect chain** — Composable, reorderable effects per track (filter, reverb, delay, chorus, distortion, compressor).
- [ ] **Preset system** — Save/load synth patches, effect chains, patterns as JSON.

## Phase 3: Richer Sequencing

**Goal: More expressive time and pattern manipulation**

- [ ] **Timeline** — Ordered scenes with bar counts and transitions
- [ ] **Humanizer** — Tunable velocity/timing variation per pattern (currently ad-hoc Math.random)
- [ ] **Generative patterns** — Euclidean rhythms, probability-based hits, Markov chains
- [ ] **Polyrhythm/polymeter** — Multiple time signatures coexisting

## Phase 4: Expanded Input & Reactivity

**Goal: The engine responds to more than just gestures**

- [ ] **Input abstraction** — OSC, MIDI, keyboard, mouse, microphone level, accelerometer as interchangeable input sources
- [ ] **State machine** — Musical memory ("after 3 breakdowns, force a drop"). Conditions based on history, not just current state.
- [ ] **Rule editor UX** — Visual interface for designing stream/stack/intent/signal mappings. Drag-and-drop reactive music design.

## Phase 5: Multi-Runtime

**Goal: Same performance config, different sound engines**

- [ ] **Max4Live runtime** — Read `.perf.json`, execute actions via Live API
- [ ] **Action vocabulary parity** — Ensure all actions work in both browser and Ableton
- [ ] **Config sync** — Edit in browser, deploy to Ableton (or vice versa)

## Phase 6: Collaboration & Sharing

- [ ] **Performance library** — Browse and load community-shared `.perf.json` files
- [ ] **Sound pack system** — Bundled samples + synth presets + patterns as a shareable unit
- [ ] **Live performance mode** — Optimized UI for performing (large buttons, minimal chrome, MIDI controller mapping)

---

## Design Principles

1. **Data over code.** Musical logic lives in JSON, not in JavaScript or Max patches.
2. **Response-first, not timeline-first.** The interesting part is mapping human input to musical output. Timelines are secondary to reactivity.
3. **Name things well.** The four-system engine (streams, stacks, intents, signals) is becoming a language. Protect the vocabulary — clear names make the system learnable.
4. **Organic over mechanical.** Weighted randomness, humanization, and non-deterministic intent resolution create music that feels alive.
5. **Portable performances.** A `.perf.json` should work anywhere. Don't leak runtime details into the config.

---

## Learnings

*(Add hard-won insights here as the project evolves)*

- **Browser audio is surprisingly capable.** Tone.js + Web Audio API can produce genuinely musical output. The soulful house demo sounds good enough that people ask "what DAW is that?"
- **The four-system engine emerged from real use.** Streams and stacks came from needing both rate-based and accumulation-based responses to gesture input. Intents came from wanting variety (same gesture, different musical result each time). Signals came from needing deterministic gated commands. Each system earned its place.
- **Track references should be by name, not index.** Learned this when thinking about portability — `"track": 5` means nothing to a Max4Live runtime that has different channel ordering.
