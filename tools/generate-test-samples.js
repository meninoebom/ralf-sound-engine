#!/usr/bin/env node
// generate-test-samples.js — Create synthetic test WAV files for sample engine testing
//
// Generates:
//   samples/test-loop-120bpm.wav  — 2-bar percussive loop at 120 BPM (4 seconds)
//   samples/test-hit.wav          — Short one-shot impact/hit (~200ms)
//
// Usage: node tools/generate-test-samples.js

const fs = require("fs");
const path = require("path");

const SAMPLE_RATE = 44100;
const BPM = 120;
const BEATS_PER_BAR = 4;
const BARS = 2;

const samplesDir = path.join(__dirname, "..", "samples");

// =============================================================================
// WAV writer (16-bit PCM mono)
// =============================================================================

function writeWav(filepath, samples) {
  const numSamples = samples.length;
  const byteRate = SAMPLE_RATE * 2; // 16-bit mono
  const dataSize = numSamples * 2;
  const fileSize = 44 + dataSize;

  const buf = Buffer.alloc(fileSize);
  let o = 0;

  // RIFF header
  buf.write("RIFF", o); o += 4;
  buf.writeUInt32LE(fileSize - 8, o); o += 4;
  buf.write("WAVE", o); o += 4;

  // fmt chunk
  buf.write("fmt ", o); o += 4;
  buf.writeUInt32LE(16, o); o += 4;       // chunk size
  buf.writeUInt16LE(1, o); o += 2;        // PCM format
  buf.writeUInt16LE(1, o); o += 2;        // mono
  buf.writeUInt32LE(SAMPLE_RATE, o); o += 4;
  buf.writeUInt32LE(byteRate, o); o += 4;
  buf.writeUInt16LE(2, o); o += 2;        // block align
  buf.writeUInt16LE(16, o); o += 2;       // bits per sample

  // data chunk
  buf.write("data", o); o += 4;
  buf.writeUInt32LE(dataSize, o); o += 4;

  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    buf.writeInt16LE(Math.round(s * 32767), o); o += 2;
  }

  fs.writeFileSync(filepath, buf);
  const duration = (numSamples / SAMPLE_RATE).toFixed(2);
  console.log(`  wrote ${filepath} (${duration}s, ${(fileSize / 1024).toFixed(1)}KB)`);
}

// =============================================================================
// Synthesis helpers
// =============================================================================

function noise() { return Math.random() * 2 - 1; }

function sineAt(freq, t) { return Math.sin(2 * Math.PI * freq * t); }

// Exponential decay envelope
function decay(t, duration) {
  return Math.exp(-t / duration);
}

// Kick-like sound: sine sweep from high to low with fast decay
function kickSample(startSample, out) {
  const dur = 0.15; // seconds
  const samples = Math.floor(dur * SAMPLE_RATE);
  for (let i = 0; i < samples && (startSample + i) < out.length; i++) {
    const t = i / SAMPLE_RATE;
    const freq = 150 * Math.exp(-t * 30) + 45; // sweep from ~195Hz to ~45Hz
    const env = decay(t, 0.06);
    out[startSample + i] += sineAt(freq, t) * env * 0.8;
  }
}

// Snare-like: noise burst + pitched body
function snareSample(startSample, out) {
  const dur = 0.1;
  const samples = Math.floor(dur * SAMPLE_RATE);
  for (let i = 0; i < samples && (startSample + i) < out.length; i++) {
    const t = i / SAMPLE_RATE;
    const noiseEnv = decay(t, 0.04);
    const bodyEnv = decay(t, 0.03);
    out[startSample + i] += noise() * noiseEnv * 0.4 + sineAt(200, t) * bodyEnv * 0.3;
  }
}

// Hi-hat: filtered noise
function hatSample(startSample, out, open) {
  const dur = open ? 0.08 : 0.03;
  const samples = Math.floor(dur * SAMPLE_RATE);
  for (let i = 0; i < samples && (startSample + i) < out.length; i++) {
    const t = i / SAMPLE_RATE;
    const env = decay(t, open ? 0.04 : 0.01);
    out[startSample + i] += noise() * env * 0.25;
  }
}

// =============================================================================
// Generate test-loop-120bpm.wav (2-bar breakbeat-ish pattern)
// =============================================================================

function generateLoop() {
  const beatsTotal = BARS * BEATS_PER_BAR;
  const beatDuration = 60 / BPM; // 0.5s at 120 BPM
  const totalDuration = beatsTotal * beatDuration;
  const totalSamples = Math.floor(totalDuration * SAMPLE_RATE);
  const out = new Float32Array(totalSamples);

  const sixteenth = beatDuration / 4;

  // Pattern (2 bars of 16 sixteenths each = 32 steps)
  // K = kick, S = snare, h = closed hat, H = open hat, . = rest
  const pattern = "K.h.S.hH K.h.S.h. K.hKS.hH ..h.S.h.";
  const steps = pattern.replace(/ /g, "").split("");

  for (let i = 0; i < steps.length; i++) {
    const sampleOffset = Math.floor(i * sixteenth * SAMPLE_RATE);
    switch (steps[i]) {
      case "K": kickSample(sampleOffset, out); break;
      case "S": snareSample(sampleOffset, out); break;
      case "h": hatSample(sampleOffset, out, false); break;
      case "H": hatSample(sampleOffset, out, true); break;
    }
  }

  writeWav(path.join(samplesDir, "test-loop-120bpm.wav"), out);
}

// =============================================================================
// Generate test-hit.wav (short impact)
// =============================================================================

function generateHit() {
  const dur = 0.25;
  const totalSamples = Math.floor(dur * SAMPLE_RATE);
  const out = new Float32Array(totalSamples);

  for (let i = 0; i < totalSamples; i++) {
    const t = i / SAMPLE_RATE;
    // Layered impact: low thud + mid crack + high transient
    const low = sineAt(80, t) * decay(t, 0.08) * 0.6;
    const mid = sineAt(400, t) * decay(t, 0.03) * 0.3;
    const hi = noise() * decay(t, 0.01) * 0.4;
    out[i] = low + mid + hi;
  }

  writeWav(path.join(samplesDir, "test-hit.wav"), out);
}

// =============================================================================
// Main
// =============================================================================

console.log("Generating test samples...");
generateLoop();
generateHit();
console.log("Done.");
