# Test notes: DigiArp on core 5.3 with Drum Mode

Emulator: digiemu at 6f2d619. Firmwares: original = core 4.1.1 + DigiArp 0.9-dev11 (sha256 of the .elemod b82506a6…); combined = DMA1, sha256 48e9a258…

## DigiArp's own tests (exit code, run time)

| Test | Original | Combined |
| --- | --- | --- |
| regression27 | exit 0, 184s | exit 0, 192s |
| tracks27 | exit 0, 88s | exit 0, 84s |
| toggle_mid27 | exit 0, 48s | exit 0, 46s |
| verify27 | exit 0, 62s | exit 0, 64s |
| synth27 | exit 0, 17s | exit 0, 17s |
| stress_real27 | exit 0, 61s | exit 0, 63s |
| card_menu27 | exit 0, 54s | exit 0, 51s |
| load_card27 | exit 0, 24s | exit 0, 24s |

## Key lines, original vs combined

```
--- regression27 (original)
LENGTH 16 ON [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 60, 61, 62, 63, 64
PASS emulator pattern lengths, chord release, shortcut all modes
--- regression27 (combined)
LENGTH 16 ON [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 60, 61, 62, 63, 64
PASS emulator pattern lengths, chord release, shortcut all modes
--- verify27 (original)
MEDIAN 20 29.33
MEDIAN 64 88.0
MEDIAN 110 148.93
--- verify27 (combined)
MEDIAN 20 28.67
MEDIAN 64 88.66
MEDIAN 110 149.34
--- stress_real27 (original)
SUMMARY 622 622 mean 8.335008051529792 max 14.670000000000073
--- stress_real27 (combined)
SUMMARY 622 622 mean 8.336038647342995 max 16.040000000000873
```

## Arp + Drum Mode side by side (tests/test_with_drum_mode.py, Drum Mode 0.8)

```
PASS  the arp plays on MIDI A (trig 9 held: C5 repeated)
PASS  and every arp note is released  (39 on, 39 off)
PASS  MIDI B selected
PASS  Drum Mode is on for MIDI B only  (0b10)
PASS  B's pads play the kit (36, 38, 42) and no arp
PASS  the arp stayed off on B
PASS  MIDI A selected again
PASS  while playing: B's kicks come out (4 per bar, ~2 bars at 120 BPM)  (7)
PASS  and A's arp at the same time  (138)
PASS  nothing else (no stray notes from either mod)
PASS  every note is released  (145 on, 145 off)
PASS  arp and Drum Mode both on B: a pad plays its drum only
PASS  the firmware is still running

13 passed, 0 failed
```

## Drum Mode's test sets on the combined firmware

| Set | Result |
| --- | --- |
| test_live_lanes | 21 passed |
| test_assign_notes | 21 passed |
| test_live_record | 15 passed |
| test_lane_mute | 10 passed |
| test_strip_playback | 11 passed |
| test_grid_edit | 26 passed |
| test_drum_page | 15 passed |

## How DigiArp's tests were run

DigiArp's tests read `test-artifacts/DA27.syx` and its `.map.json`, and import digiemu from
`PYTHONPATH`. Each build ran in its own folder with the firmware copied in as `DA27.syx`:

```
PYTHONPATH=$DIGIEMU uv run --project $DIGIEMU python tests/regression27.py
```

The symbols the tests use (`proxies`, `arp_enabled`, `semaphore`, ...) are in the combined
map too, so they ran unchanged.

## What wasn't tested

- Real hardware with real MIDI devices: the emulator checks the notes sent, not how a drum
  machine or synth receives them.
- DigiArp's ARP settings page and its +Drive saving beyond what its own tests cover.
