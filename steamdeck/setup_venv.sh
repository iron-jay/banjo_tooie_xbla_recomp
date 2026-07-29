#!/usr/bin/env bash
set -e
if [ ! -d "$HOME/bt_venv" ]; then
  python3 -m venv --system-site-packages "$HOME/bt_venv"
fi
"$HOME/bt_venv/bin/pip" install --quiet --upgrade pip pyinstaller 2>&1 | tail -4
echo "---"
"$HOME/bt_venv/bin/python" - <<'PY'
import PyInstaller, tkinter
print("pyinstaller", PyInstaller.__version__, "| tk", tkinter.TkVersion)
PY
