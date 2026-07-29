#!/usr/bin/env bash
export DISPLAY=:0
echo "=== windows known to the WM ==="
wmctrl -lG || echo "wmctrl failed"
echo "=== move/resize the launcher on-screen and raise it ==="
# -e gravity,x,y,w,h ; match by title substring
wmctrl -r "Banjo-Tooie" -e 0,80,80,580,484 2>/dev/null && echo "moved" || echo "no window titled Banjo-Tooie"
wmctrl -a "Banjo-Tooie" 2>/dev/null && echo "activated" || true
