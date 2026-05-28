#!/bin/sh
# Radreise Planer — Startskript für Home Assistant Add-on
set -e

DATA_DIR="/data"
BROUTER_DIR="/opt/brouter"
SEGMENTS_DIR="${DATA_DIR}/segments4"

# Verzeichnisse anlegen
mkdir -p "${DATA_DIR}/tours" "${SEGMENTS_DIR}"

# ── BRouter-Segmente aus HA-Optionen lesen ────────────────────────────────────
OPTS_FILE="/data/options.json"
if [ -f "${OPTS_FILE}" ]; then
    SEGMENTS=$(python3 -c "
import json, sys
try:
    opts = json.load(open('${OPTS_FILE}'))
    segs = opts.get('brouter_segments', ['E5_N50','E10_N50'])
    print(' '.join(segs))
except Exception as e:
    print('E5_N50 E10_N50')
" 2>/dev/null)
    MEM=$(python3 -c "
import json
try:
    opts = json.load(open('${OPTS_FILE}'))
    print(opts.get('brouter_memory_mb', 256))
except:
    print(256)
" 2>/dev/null)
else
    SEGMENTS="E5_N50 E10_N50"
    MEM=256
fi

echo "=== Radreise Planer ==="
echo "  BRouter-Segmente : ${SEGMENTS}"
echo "  BRouter-Speicher : ${MEM} MB"

# ── Routing-Daten herunterladen (nur wenn fehlend) ────────────────────────────
SEGMENT_BASE="https://brouter.de/brouter/segments4"
for seg in ${SEGMENTS}; do
    FILE="${SEGMENTS_DIR}/${seg}.rd5"
    if [ ! -f "${FILE}" ]; then
        echo "  Lade Routing-Daten: ${seg}.rd5 (~100 MB) ..."
        if wget -q -O "${FILE}.tmp" "${SEGMENT_BASE}/${seg}.rd5"; then
            mv "${FILE}.tmp" "${FILE}"
            echo "  ✓ ${seg}.rd5 heruntergeladen"
        else
            rm -f "${FILE}.tmp"
            echo "  ⚠ Konnte ${seg}.rd5 nicht laden — Routing in dieser Region nicht verfügbar"
        fi
    fi
done

# ── Server starten ────────────────────────────────────────────────────────────
export DATA_DIR="${DATA_DIR}"
export BROUTER_DIR="${BROUTER_DIR}"
export SEGMENTS_DIR="${SEGMENTS_DIR}"
export BROUTER_MEMORY_MB="${MEM}"

echo "  ✓ Starte Server auf Port 3000 ..."
exec python3 /app/server.py
