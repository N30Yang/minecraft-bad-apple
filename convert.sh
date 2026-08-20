#!/usr/bin/env sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR" || exit 1

if [ "$#" -eq 0 ]; then
    exec node "$SCRIPT_DIR/tui.js"
fi

exec python3 "$SCRIPT_DIR/generate.py" "$@"
