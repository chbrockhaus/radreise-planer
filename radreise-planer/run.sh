#!/bin/sh
# Radreise Planer — Startskript für Home Assistant Add-on
set -e

DATA_DIR="/data"
BROUTER_DIR="/opt/brouter"
SEGMENTS_DIR="${DATA_DIR}/segments4"

# Zeitstempel-Hilfsfunktion
ts() { date -u '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*"; }

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
    FORCE_REFRESH=$(python3 -c "
import json
try:
    opts = json.load(open('${OPTS_FILE}'))
    print('true' if opts.get('force_segment_refresh', False) else 'false')
except:
    print('false')
" 2>/dev/null)
else
    SEGMENTS="E5_N50 E10_N50"
    MEM=256
    FORCE_REFRESH="false"
fi

log "=== Radreise Planer ==="
log "  BRouter-Segmente : ${SEGMENTS}"
log "  BRouter-Speicher : ${MEM} MB"

# ── Routing-Daten herunterladen ───────────────────────────────────────────────
SEGMENT_BASE="https://brouter.de/brouter/segments4"
REFRESHED_SEGS=""

# Bei force_segment_refresh: vorhandene Kacheln löschen → erzwingt Neudownload
if [ "${FORCE_REFRESH}" = "true" ]; then
    log "  ⚠ force_segment_refresh=true — lösche vorhandene Kacheln für Neudownload"
    rm -f "${SEGMENTS_DIR}"/*.rd5
fi

for seg in ${SEGMENTS}; do
    FILE="${SEGMENTS_DIR}/${seg}.rd5"
    if [ ! -f "${FILE}" ]; then
        log "  Lade Routing-Daten: ${seg}.rd5 (~100 MB) ..."
        if curl -fsSL --retry 3 -o "${FILE}.tmp" "${SEGMENT_BASE}/${seg}.rd5"; then
            mv "${FILE}.tmp" "${FILE}"
            log "  ✓ ${seg}.rd5 heruntergeladen"
            REFRESHED_SEGS="${REFRESHED_SEGS} ${seg}"
        else
            rm -f "${FILE}.tmp"
            log "  ⚠ Konnte ${seg}.rd5 nicht laden — Routing in dieser Region nicht verfügbar"
        fi
    fi
done

# Wenn Kacheln aktualisiert wurden: Marker-Datei schreiben (wird im UI angezeigt)
if [ "${FORCE_REFRESH}" = "true" ] && [ -n "${REFRESHED_SEGS}" ]; then
    REFRESHED_SEGS_TRIMMED=$(echo "${REFRESHED_SEGS}" | sed 's/^ *//')
    python3 -c "
import json, datetime
segs = '${REFRESHED_SEGS_TRIMMED}'.split()
data = {
    'refreshed_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'segments': segs
}
with open('/data/segments_refreshed.json', 'w') as f:
    json.dump(data, f)
print('  ✓ Kacheln aktualisiert — Hinweis wird im Browser angezeigt')
"
fi

# ── Server starten ────────────────────────────────────────────────────────────
export DATA_DIR="${DATA_DIR}"
export BROUTER_DIR="${BROUTER_DIR}"
export SEGMENTS_DIR="${SEGMENTS_DIR}"
export BROUTER_MEMORY_MB="${MEM}"

log "  ✓ Starte Server auf Port 3000 ..."
exec python3 /app/server.py
