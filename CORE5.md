# DigiArp MIDI on elekloader core 5.3 (branch `core-5.3`)

This fork of [DigiArp MIDI](https://github.com/aleks-karachevtsev/Digitone-MIDI-Arpeggiator) by
aleks-karachevtsev rebuilds it on elekloader's **core 5.3**, so it can go into one firmware with
mods that need core 5.x, such as [Drum Mode](https://github.com/morriess/Digitone-Drum-Mode).
The version in the elekloader Mod Shop (0.9.0-beta, `0.9-dev11`) is built on **core 4.1**.

> **Status: tested in the emulator, not yet on a unit.** DigiArp's author hasn't reviewed
> this change. The branch starts from the original's `2a853b7` (the Mod Shop's build).

## Why core 5.3 refused DigiArp

```
core 5.3 and digiarp-midi 0.9-dev11 both export fw_note_off
core 5.3 and digiarp-midi 0.9-dev11 both export fw_note_on
```

- DigiArp names the Digitone's MIDI send routines itself: `fw_note_on` = 0x400ee232
  `(channel, note, velocity)` and `fw_note_off` = 0x400ee29e `(channel, note)`. Core 4.1 had no
  such names.
- Core 5.3 added `fw_note_on` and `fw_note_off` of its own, for a **different** routine: the
  track-level note on/off that KEYBOARD mode uses, with six and three arguments.
- One name can't point to two routines, so the build tool refuses. The routines aren't the
  same, so DigiArp can't use core's.

## The change (one commit)

| File | Change |
| --- | --- |
| `firmware/trig-hook.s` | `fw_note_on` / `fw_note_off` renamed to `digiarp_midi_on` / `digiarp_midi_off` (the same two `jmp`s to 0x400ee232 / 0x400ee29e) |
| `firmware/live.c` | its one call site uses the new names |
| `mod.json` | version `0.9-dev11-core5`; core `5.2.1` (5.2.1 moved two of core's own hooks to make room for DigiArp's; the rename covers 5.3) |

Nothing else changes: the same code, the same 12 firmware sites, the same settings. The same
rename in the original would let the official version combine with core 5.x mods in the Mod
Shop; offering it to the author as a pull request is the next step.

## Building

```
./build-core5.sh /path/to/Digitone_and_Digitone_Keys_OS1.44.syx
```

It fetches Drum Mode (whose build fetches elekloader at the pinned commit and builds core 5.3
and seq-events), builds DigiArp from this branch, and writes:

| File | Contents | OS version on the unit |
| --- | --- | --- |
| `out/Digitone_OS1.44_DigiArp_core5.syx` | core 5.3 + DigiArp | **DAC5** |
| `out/Digitone_OS1.44_DrumMode_DigiArp.syx` | core 5.3 + seq-events 0.1 + Drum Mode + DigiArp | **DMA1** |

Install as in the [Drum Mode manual](https://github.com/morriess/Digitone-Drum-Mode/blob/main/drum-mode/docs/MANUAL.md#installing).
Both files are built from your own copy of Elektron's OS, so they're for your own unit only:
don't upload or pass them on. This repo never contains them.

## Using it with Drum Mode

They work on separate MIDI tracks:

- **DigiArp:** on a MIDI track, FUNC + KEYBOARD switches the arp on or off; held keys are then
  arpeggiated. See [HARDWARE_CONTROLS.md](HARDWARE_CONTROLS.md).
- **Drum Mode:** on another MIDI track, hold its track key → DRUM MODE. See its
  [manual](https://github.com/morriess/Digitone-Drum-Mode/blob/main/drum-mode/docs/MANUAL.md).

For example an arp on MIDI A for a bass synth and drums on MIDI B for a drum machine, both
from the same pattern. **Both on the same track:** Drum Mode's pads take the trig keys, so the
arp stays quiet there. DigiArp adds no Mod Menu tile, and the LEDs don't clash (DigiArp lights
only the KEYBOARD key).

## Tested (emulator, digiemu)

| Test | Result |
| --- | --- |
| DigiArp's own 8 emulator tests (`tests/*27.py`: arp patterns of length 1–16, chord release, all modes' shortcut, 4 tracks, switching off mid-note, gate lengths, synth tracks untouched, 5 s stress at 300 BPM, saving to and loading from +Drive), with Drum Mode 0.8 | all pass, on the original build and the combined one |
| Their output compared line by line, original vs combined | same notes and checks; only timing jitter of a few ms, code addresses and the saved project's checksum differ |
| [tests/test_with_drum_mode.py](tests/test_with_drum_mode.py): arp on A, Drum Mode on B, both at once while playing, then both on one track | 13 of 13 pass (with Drum Mode 0.8 and 0.9.3) |

Details: [CORE5-NOTES.md](CORE5-NOTES.md). Not tested: real hardware with real MIDI devices.

## The safety net (not done)

A possible extra: release arp notes on the physical key-up through core's `ev_key`, against
stuck or extra pitches reported with the original. Not reproduced in the emulator, so not
added; waiting for a decision.
