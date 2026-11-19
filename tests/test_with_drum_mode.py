# SPDX-License-Identifier: GPL-2.0-or-later
"""DigiArp MIDI (rebuilt for core 5.3) and Drum Mode in one firmware, in digiemu.

    uv run --project $DIGIEMU python tests/test_with_drum_mode.py out/Digitone_OS1.44_DrumMode_DigiArp.syx [workdir]

Uses Drum Mode's emulator harness from the copy build-core5.sh fetches (.cache/drum-mode).

Arp on MIDI A, Drum Mode on MIDI B, then both at once while the sequencer plays: B's drum pattern and A's arp come
out together, each from its own track, and neither mod reacts to the other's track. Last, both on the same track:
Drum Mode's pads take the trig keys, so the arp stays quiet there. The arp is set up as DigiArp's own regression test
does (its settings written to its per-track proxy, mode 2, 1/16, its "enabled" flag for the track).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '.cache', 'drum-mode', 'drum-mode', 'tests'))
from emu_session import Digitone          # noqa: E402

results = []


def check(name, ok, detail=''):
    results.append((name, ok))
    print('%s  %s%s' % ('PASS' if ok else 'FAIL', name, ('  (%s)' % detail) if detail else ''))


def main():
    syx = os.path.abspath(sys.argv[1])
    work = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else 'emu-work')
    os.makedirs(work, exist_ok=True)
    d = Digitone(syx, os.path.join(work, 'home'), audio=True)
    S = d.symbols
    proxy = int(S['proxies'], 16) + 4 if isinstance(S['proxies'], str) else S['proxies'] + 4
    en = int(S['arp_enabled'], 16) if isinstance(S['arp_enabled'], str) else S['arp_enabled']

    def ons(msgs):
        return [(m[0] & 0x0F, m[1]) for m in msgs if (m[0] & 0xF0) == 0x90 and m[2] > 0]

    def offs(msgs):
        return [(m[0] & 0x0F, m[1]) for m in msgs
                if (m[0] & 0xF0) == 0x80 or ((m[0] & 0xF0) == 0x90 and m[2] == 0)]

    def arp_on(track_index):
        """DigiArp on for MIDI A-D (0-3), as its regression27 sets it: 1/16, mode 2 (up), 4 steps, all on."""
        base = proxy + 812 * track_index
        d.s.m.uc.mem_write(base + 0x110, b'\x11')
        d.s.m.uc.mem_write(base + 0x111, b'\x00')
        d.s.m.uc.mem_write(base + 0x113, b'\x03')
        d.s.m.uc.mem_write(base + 0x114, b'\xff\xff' + bytes(16))
        d.s.m.uc.mem_write(base + 0x10f, b'\x02')
        d.s.m.uc.mem_write(en + track_index, b'\x01')

    # MIDI A: channel on, the arp on.
    d.setup_midi_track_a()
    d.wait(800)
    arp_on(0)
    d.take_midi()
    d.press('9', after_ms=1100)
    d.release('9', after_ms=300)
    a = d.take_midi()
    arp = [n for c, n in ons(a)]
    check('the arp plays on MIDI A (trig 9 held: C5 repeated)', len(arp) >= 4 and set(arp) == {60}, str(arp[:12]))
    check('and every arp note is released', sorted(ons(a)) == sorted(offs(a)), '%d on, %d off' % (len(ons(a)), len(offs(a))))

    # MIDI B: channel on, Drum Mode on (the Mod Menu's only entry: DigiArp adds none).
    d.tap('T2', after_ms=400)
    check('MIDI B selected', d.active_track() == 5, str(d.active_track()))
    d.tap('SYN1', after_ms=400)
    d.press('FUNC')
    d.tap('A', after_ms=200)
    d.release('FUNC', after_ms=400)
    d.hold('T2', 700)
    d.tap('YES', after_ms=500)
    d.wait(2600)
    enabled = d.mem(S['dm'] + 1, 1)[0]
    check('Drum Mode is on for MIDI B only', enabled == 0b10, bin(enabled))
    d.take_midi()
    for pad in ('1', '2', '3'):
        d.tap(pad, after_ms=200)
    b = d.take_midi()
    check('B\'s pads play the kit (36, 38, 42) and no arp', [n for c, n in ons(b)] == [36, 38, 42], str(ons(b)))
    check('the arp stayed off on B', d.mem(en + 1, 1)[0] == 0)

    # A kick on every beat of B's pattern, placed in GRID RECORDING. Since Drum Mode 0.9 a pad selects its lane, so
    # pad 1 again makes the kick the selected lane (pad 3 left the hat selected).
    d.tap('1', after_ms=200)
    d.take_midi()
    d.tap('RECORD', after_ms=400)
    for key in ('1', '5', '9', '13'):
        d.tap(key, after_ms=150)
    d.tap('RECORD', after_ms=400)

    # Both at once: back to A, PLAY, hold an arp key while B's pattern plays.
    d.tap('T1', after_ms=400)
    check('MIDI A selected again', d.active_track() == 4, str(d.active_track()))
    d.take_midi()
    d.tap('PLAY', after_ms=0)
    d.press('9', after_ms=4000)
    d.release('9', after_ms=300)
    d.tap('STOP', after_ms=500)
    both = d.take_midi()
    notes = [n for c, n in ons(both)]
    kicks, arp = notes.count(36), notes.count(60)
    others = sorted(set(notes) - {36, 60})
    check('while playing: B\'s kicks come out (4 per bar, ~2 bars at 120 BPM)', 6 <= kicks <= 10, str(kicks))
    check('and A\'s arp at the same time', arp >= 12, str(arp))
    check('nothing else (no stray notes from either mod)', not others, str(others))
    check('every note is released', sorted(ons(both)) == sorted(offs(both)),
          '%d on, %d off' % (len(ons(both)), len(offs(both))))

    # Both mods on the same track: Drum Mode takes the trig keys, the arp gets none.
    arp_on(1)
    d.tap('T2', after_ms=400)
    d.take_midi()
    d.press('1', after_ms=800)
    d.release('1', after_ms=300)
    same = d.take_midi()
    check('arp and Drum Mode both on B: a pad plays its drum only', [n for c, n in ons(same)] == [36], str(ons(same)))
    check('the firmware is still running', not d.halted, str(d.halted))

    failed = [n for n, ok in results if not ok]
    print('\n%d passed, %d failed' % (len(results) - len(failed), len(failed)))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
