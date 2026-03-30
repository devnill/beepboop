#!/bin/bash
# Regenerate all beepboop sounds using the synth submodule.
set -e
cd "$(dirname "$0")"

# Use a local venv to avoid conflicts with system/homebrew Python.
if [ ! -d ".venv" ]; then
  python3 -m venv .venv --quiet
fi

.venv/bin/pip install -e synth/ -q
.venv/bin/synth generate --config synth.toml

echo "Done. WAV files written to plugin/sounds/"
