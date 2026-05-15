#!/bin/sh
# Da Flatpak seine eigene Struktur hat, müssen wir Pfade korrekt setzen
export PATH="/app/bin:$PATH"
python3 /app/bin/main.py