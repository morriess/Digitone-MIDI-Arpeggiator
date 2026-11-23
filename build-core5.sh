#!/usr/bin/env bash
# Build DigiArp MIDI on elekloader core 5.3 (this branch), alone and in one firmware with Drum Mode.
#
#   ./build-core5.sh /path/to/Digitone_and_Digitone_Keys_OS1.44.syx
#
# Writes out/Digitone_OS1.44_DigiArp_core5.syx (DigiArp alone on core 5.3, OS version DAC5) and
# out/Digitone_OS1.44_DrumMode_DigiArp.syx (DigiArp and Drum Mode, OS version DMA1).
#
# Drum Mode (morriess/Digitone-Drum-Mode) is fetched into .cache; its build fetches elekloader at the commit it pins
# (core 5.3, seq-events 0.1) and builds core and seq-events, which this build uses too. Set DRUM_MODE_REPO to use
# another copy. Needs: git, python3, and an m68k cross toolchain. The stock OS file is yours: the firmware files
# built from it are for your own unit only, never to be shared.
set -euo pipefail

DRUM_MODE_REPO="${DRUM_MODE_REPO:-https://github.com/morriess/Digitone-Drum-Mode.git}"

here="$(cd "$(dirname "$0")" && pwd)"
stock="${1:?usage: ./build-core5.sh /path/to/Digitone_and_Digitone_Keys_OS1.44.syx}"
stock="$(cd "$(dirname "$stock")" && pwd)/$(basename "$stock")"
mkdir -p "$here/out" "$here/.cache"

dmr="$here/.cache/drum-mode"
if [ ! -d "$dmr/.git" ]; then
    git clone --quiet "$DRUM_MODE_REPO" "$dmr"
else
    git -C "$dmr" pull --quiet --ff-only || true
fi
dmd="$dmr"                                  # the repo root since 2026-11-23 (was drum-mode/ inside it)
[ -f "$dmd/build.sh" ] || dmd="$dmr/drum-mode"
"$dmd/build.sh" "$stock"

ek="$dmd/.cache/elekloader"
export PYTHONPATH="$ek"
if [ -z "${ELEKLOADER_CROSS:-}" ]; then
    if command -v m68k-elf-gcc >/dev/null; then export ELEKLOADER_CROSS=m68k-elf-
    else export ELEKLOADER_CROSS=m68k-linux-gnu-
    fi
fi

python3 -m elekloader.sdk.build "$here" --stock "$stock"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$here/mod.json")"
arp="$here/out/digiarp-midi-$version.elemod"

version_of() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$1"; }
core="$ek/mods/core-dn1/out/core-$(version_of "$ek/mods/core-dn1/mod.json")-os1.44.elemod"
seq="$ek/mods/seq-events-dn1/out/seq-events-$(version_of "$ek/mods/seq-events-dn1/mod.json")-os1.44.elemod"
dm_version="$(version_of "$dmd/src/mod.json")"
dm="$dmd/src/out/drummode-$dm_version-os1.44.elemod"
[ -f "$dm" ] || dm="$dmd/src/out/drummode-$dm_version.elemod"

python3 -m elekloader.lint "$arp" --stock "$stock" --with "$core" --with "$seq" --with "$dm"
python3 -m elekloader.patch --stock "$stock" --mod "$core" --mod "$arp" \
    --out "$here/out/Digitone_OS1.44_DigiArp_core5.syx" --version DAC5
python3 -m elekloader.patch --stock "$stock" --mod "$core" --mod "$seq" --mod "$dm" --mod "$arp" \
    --out "$here/out/Digitone_OS1.44_DrumMode_DigiArp.syx" --version DMA1

echo
echo "Built: $here/out/Digitone_OS1.44_DigiArp_core5.syx     (DigiArp alone on core 5.x; OS version DAC5)"
echo "       $here/out/Digitone_OS1.44_DrumMode_DigiArp.syx  (with Drum Mode $dm_version; OS version DMA1)"
