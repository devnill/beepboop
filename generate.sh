#!/bin/bash
# Regenerate all beepboop sounds using the synth submodule.
set -e
cd "$(dirname "$0")"

pip install -e synth/ -q          # installs synth as editable package (fast on repeat runs)
synth generate --config synth.toml

echo "Done. WAV files written to plugin/sounds/"
