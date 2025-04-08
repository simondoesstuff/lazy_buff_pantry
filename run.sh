#!/bin/bash

# this is a nix-script
if [ -z "$IN_NIX_SHELL" ]; then
  if ! command -v nix &> /dev/null; then
    export PATH=/nix/var/nix/profiles/default/bin:$PATH
  fi
  exec nix develop "$(dirname "$0")" -c "$0" "$@"
fi

cd "$(dirname "$0")"
date >> log
uv run main.py | tee -a log
echo >> log
