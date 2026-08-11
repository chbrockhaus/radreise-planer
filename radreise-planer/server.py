#!/usr/bin/env python3
"""
Radreise Planer – HTTP-Server für Docker / Home Assistant Add-on.

Änderungen gegenüber der Windows-Version:
  • Pfade über Umgebungsvariablen konfigurierbar (DATA_DIR, BROUTER_DIR, …)
  • Java-Aufruf über PATH (kein Windows-spezifischer Pfad)
  • HA-Ingress-Unterstützung: injiziert Fetch-Interceptor in die HTML-Seite,
    damit /api/-Aufrufe des Browsers korrekt durch den Ingress-Proxy geleitet werden.
"""

import concurrent.futures
import gzip
import http.server
import json
import os
import re as _re
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
import datetime

def log(msg: str) -> None:
    """Gibt eine Logzeile mit UTC-Zeitstempel aus."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)

# ── Konfiguration ─────────────────────────────────────────────────────────────
PORT         = int(os.environ.get('PORT', 3000))
DATA_DIR     = os.environ.get('DATA_DIR',     '/data')
BROUTER_DIR  = os.environ.get('BROUTER_DIR',  '/opt/brouter')
SEGMENTS_DIR = os.environ.get('SEGMENTS_DIR', os.path.join(DATA_DIR, 'segments4'))
PROFILES_DIR = os.environ.get('PROFILES_DIR', os.path.join(BROUTER_DIR, 'profiles2'))
CUSTOM_DIR   = os.environ.get('CUSTOM_DIR',   os.path.join(BROUTER_DIR, 'customprofiles'))
BROUTER_MEM  = os.environ.get('BROUTER_MEMORY_MB', '256')

WEBSITES_FILE          = os.path.join(DATA_DIR, 'camping_websites.json')
TARGETS_FILE           = os.path.join(DATA_DIR, 'routing_targets.json')
MANUAL_CAMPS_FILE      = os.path.join(DATA_DIR, 'manual_camps.json')
ROUTE_DATA_FILE        = os.path.join(DATA_DIR, 'route_data_custom.json')
TOURS_DIR              = os.path.join(DATA_DIR, 'tours')
SEGMENTS_REFRESHED_FILE = os.path.join(DATA_DIR, 'segments_refreshed.json')

BROUTER_PORT    = 17777
# Timeout pro Endpoint. Die Endpoints werden GESTAFFELT angefragt (siehe
# _overpass_race), ein langsamer blockiert die schnellen also nicht.
OVERPASS_TIMEOUT      = 20   # Sekunden pro Endpoint (GET)
OVERPASS_TIMEOUT_POST = 40   # POST (around-Route) darf länger dauern
APP_DIR         = os.path.dirname(os.path.abspath(__file__))
TILE_CACHE_DIR  = os.path.join(DATA_DIR, 'tile_cache')

TILE_SOURCES = {
    'osm':     'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'cyclosm': 'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
    'topo':    'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
}

brouter_proc = None

# ── On-demand Kachel-Download ─────────────────────────────────────────────────
_segment_status = {}   # segment -> 'downloading' | 'ready' | 'error: ...'
_download_lock  = threading.Lock()

def _segment_name_ok(seg):
    return bool(_re.match(r'^[EW]\d+_[NS]\d+$', seg))

def _download_segment_bg(segment):
    global brouter_proc, _segment_status
    seg_file = os.path.join(SEGMENTS_DIR, f'{segment}.rd5')
    tmp      = seg_file + '.tmp'
    try:
        url = f'https://brouter.de/brouter/segments4/{segment}.rd5'
        log(f'  Lade Segment {segment} …')
        urllib.request.urlretrieve(url, tmp)
        os.rename(tmp, seg_file)
        log(f'  ✓ {segment}.rd5 heruntergeladen ({os.path.getsize(seg_file)//1024//1024} MB)')
        # BRouter neu starten damit er das neue Segment lädt
        if brouter_proc:
            brouter_proc.terminate()
            try: brouter_proc.wait(timeout=10)
            except Exception: pass
        start_brouter()
        import time; time.sleep(5)   # BRouter braucht ein paar Sekunden zum Starten
        _segment_status[segment] = 'ready'
        log(f'  ✓ BRouter neu gestartet mit {segment}')
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except Exception: pass
        _segment_status[segment] = f'error: {e}'
        log(f'  ✗ Segment {segment} Fehler: {e}')

# ── BRouter ───────────────────────────────────────────────────────────────────
def start_brouter():
    global brouter_proc
    jar = os.path.join(BROUTER_DIR, 'brouter.jar')
    if not os.path.exists(jar):
        log(f'  BRouter: brouter.jar nicht gefunden: {jar}')
        return
    if not os.listdir(SEGMENTS_DIR):
        log('  BRouter: Keine Routing-Daten in segments4/ — Routing nicht verfügbar')
        return
    cmd = [
        'java', f'-Xmx{BROUTER_MEM}m', '-cp', jar,
        'btools.server.RouteServer',
        SEGMENTS_DIR, PROFILES_DIR, CUSTOM_DIR,
        str(BROUTER_PORT), '1'
    ]
    try:
        brouter_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log(f'  BRouter gestartet (PID {brouter_proc.pid}) auf Port {BROUTER_PORT}')
    except Exception as e:
        log(f'  BRouter Startfehler: {e}')

# ── Datei-Hilfsfunktionen ─────────────────────────────────────────────────────
def _load_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def load_ws():            return _load_json(WEBSITES_FILE, {})
def save_ws(d):           _save_json(WEBSITES_FILE, d)
def load_targets():       return _load_json(TARGETS_FILE, {})
def save_targets(d):      _save_json(TARGETS_FILE, d)
def load_manual_camps():  return _load_json(MANUAL_CAMPS_FILE, {})
def save_manual_camps(d): _save_json(MANUAL_CAMPS_FILE, d)

# ── Tour-Management ───────────────────────────────────────────────────────────
def _safe_id(tid):
    return ''.join(c for c in str(tid) if c.isalnum() or c in '-_')

def list_tours():
    os.makedirs(TOURS_DIR, exist_ok=True)
    tours = []
    for fname in os.listdir(TOURS_DIR):
        if not fname.endswith('.json'):
            continue
        d = _load_json(os.path.join(TOURS_DIR, fname))
        if d:
            tours.append({
                'id':            d.get('id', fname[:-5]),
                'name':          d.get('name', 'Unbekannt'),
                'route_name':    d.get('route_name', ''),
                'created':       d.get('created', ''),
                'modified':      d.get('modified', ''),
                'total_km':      d.get('total_km', 0),
                'num_stages':    d.get('num_stages', 0),
                'route_preview': d.get('route_preview', []),
            })
    return sorted(tours, key=lambda t: t.get('modified') or t.get('created', ''), reverse=True)

def save_tour(data):
    os.makedirs(TOURS_DIR, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    tid = _safe_id(data.get('id') or '') or str(int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000))
    data['id'] = tid
    if not data.get('created'):
        data['created'] = now
    data['modified'] = now
    with open(os.path.join(TOURS_DIR, f'{tid}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return tid

def load_tour(tid):
    fname = os.path.join(TOURS_DIR, f'{_safe_id(tid)}.json')
    return _load_json(fname)

def delete_tour(tid):
    fname = os.path.join(TOURS_DIR, f'{_safe_id(tid)}.json')
    if os.path.exists(fname):
        os.remove(fname)
        return True
    return False

# ── Overpass: gestaffelt statt alle gleichzeitig ──────────────────────────────
# Startreihenfolge wird zur Laufzeit nach gemessener Antwortzeit sortiert
# (siehe _ep_order) — diese Liste gibt nur die Kandidaten vor.
# gall/lambert sind die beiden ECHTEN Server hinter overpass-api.de. Sie stehen
# hier extra drin, weil der Lastverteiler overpass-api.de zeitweise auf einen
# überlasteten Knoten schickt (gemessen 2026-08: overpass-api.de HTTP 504, während
# lambert dieselbe Abfrage in 0,53 s beantwortete). Doppelt gezählt wird dadurch
# nichts — die Slots hängen an der IP, nicht am Namen (siehe _ep_key).
OVERPASS_ENDPOINTS = [
    'https://lambert.openstreetmap.de/api/interpreter',   # OSM-DE Server B
    'https://gall.openstreetmap.de/api/interpreter',      # OSM-DE Server A
    'https://overpass.private.coffee/api/interpreter',    # eigene Maschine …
    'https://overpass.kumi.systems/api/interpreter',      # … dieselbe wie private.coffee
    'https://overpass-api.de/api/interpreter',            # Lastverteiler auf A/B
]

# Mehr als drei Versuche pro Abfrage bringen nichts und würden nur das Zeitbudget
# aufblähen (jeder weitere Endpoint verlängert die Frist um OVERPASS_STAGGER).
OVERPASS_MAX_TRIES = 3

# WARUM NICHT MEHR ALLE ENDPOINTS GLEICHZEITIG (bis v1.9.8):
# Sockets/Threads lassen sich in Python nicht abbrechen — nach dem Gewinner eines
# Rennens liefen die beiden Verlierer bis zu OVERPASS_TIMEOUT weiter und belegten
# so lange je einen der nur ZWEI Slots, die Overpass pro IP erlaubt. Bei mehreren
# POI-Abfragen kurz hintereinander stapelten sich diese Nachzügler, bis alle drei
# Server nur noch in die Warteschlange stellten → Zeitüberschreitung bzw. 504
# ("overpass-api.de: HTTP 504; private.coffee: Zeitüberschreitung; …").
# Jetzt: erst den schnellsten Endpoint fragen, einen zweiten NUR wenn nach
# OVERPASS_STAGGER Sekunden noch keine Antwort da ist. Im Normalfall entsteht so
# eine einzige Anfrage statt drei — ein Drittel der Last, keine Nachzügler.
OVERPASS_STAGGER  = 2.5   # Sekunden bis zusätzlich der nächste Endpoint startet
OVERPASS_HOST_MAX = 2     # gleichzeitige Anfragen je Endpoint ("Rate limit: 2")
OVERPASS_COOLDOWN = 90    # Sekunden, die ein Endpoint nach einem Fehler hintenansteht

_OVERPASS_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=32, thread_name_prefix='overpass')

# Slots werden pro MASCHINE (IP) gezählt, nicht pro Hostname:
# overpass.private.coffee und overpass.kumi.systems zeigen auf denselben Rechner
# (193.219.97.30 / 2a0d:f302:126:78ea::1, geprüft 2026-08). Nach Hostnamen gezählt
# hätten wir ihm doppelt so viele gleichzeitige Anfragen geschickt wie erlaubt —
# er nimmt die Verbindung dann zwar an, lässt sie aber ohne Antwort stehen, bis
# unser Timeout zuschlägt (Fehlerbild "Zeitüberschreitung" trotz freier Leitung).
EP_IP_TTL      = 600        # Sekunden, die eine aufgelöste IP wiederverwendet wird
_ep_ip_cache   = {}         # host -> (zeitstempel, ip)
_ep_avg        = {}         # endpoint -> geglättete Antwortzeit
_slots         = {}         # ip -> {'inflight': n, 'cool_until': t}
_ep_lock       = threading.Lock()


def _ep_key(ep):
    """Slot-Schlüssel eines Endpoints: seine IP (siehe Kommentar oben)."""
    host = ep.split('/')[2]
    now  = time.time()
    with _ep_lock:
        hit = _ep_ip_cache.get(host)
    if hit and now - hit[0] < EP_IP_TTL:
        return hit[1]
    try:   # außerhalb des Locks — getaddrinfo kann blockieren
        key = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)[0][4][0]
    except Exception:
        key = host
    with _ep_lock:
        _ep_ip_cache[host] = (now, key)
    return key


def _slot(key):
    return _slots.setdefault(key, {'inflight': 0, 'cool_until': 0.0})


def _ep_order():
    """Endpoints nach Erfolgsaussicht: nicht gesperrt, wenig belegt, schnell."""
    keys = {ep: _ep_key(ep) for ep in OVERPASS_ENDPOINTS}   # ggf. DNS, ohne Lock
    now  = time.time()
    with _ep_lock:
        return sorted(OVERPASS_ENDPOINTS, key=lambda ep: (
            _slot(keys[ep])['cool_until'] > now,
            _slot(keys[ep])['inflight'],
            _ep_avg.get(ep) if _ep_avg.get(ep) is not None else 5.0,
        ))


def _ep_reserve(ep):
    """Belegt einen Slot der Maschine; False wenn schon OVERPASS_HOST_MAX laufen."""
    key = _ep_key(ep)
    with _ep_lock:
        st = _slot(key)
        if st['inflight'] >= OVERPASS_HOST_MAX:
            return False
        st['inflight'] += 1
        return True


def _ep_release(ep, secs=None):
    """Gibt den Slot frei. secs=None bedeutet Fehler → Maschine kurz sperren."""
    key = _ep_key(ep)
    with _ep_lock:
        st = _slot(key)
        st['inflight'] = max(0, st['inflight'] - 1)
        if secs is None:
            st['cool_until'] = time.time() + OVERPASS_COOLDOWN
        else:
            prev = _ep_avg.get(ep)
            _ep_avg[ep] = secs if prev is None else 0.7 * prev + 0.3 * secs
            st['cool_until'] = 0.0

# Vorbild ist `requestIsActive` aus der Bibliothek overpass-frontend, die
# brouter-web benutzt: dort läuft nie mehr als eine Overpass-Anfrage, alles
# andere wartet in einer Warteschlange. Hier sind es ZWEI Warteplätze, nicht
# einer — denn bricht der Browser eine Abfrage ab (Karte verschoben), merkt der
# Python-Handler das nicht: er rechnet die verwaiste Anfrage zu Ende und hielte
# mit nur einem Platz die Folgeanfrage bis zu OVERPASS_QUEUE_WAIT auf (gemessen:
# genau 15 s Wartezeit, dann Fehler). Das Limit der OSM-Server wird davon nicht
# berührt — das hängt an OVERPASS_HOST_MAX je Maschine, nicht an dieser Zahl.
OVERPASS_MAX_PARALLEL = 2
OVERPASS_QUEUE_WAIT   = 15   # Sekunden, die eine wartende Abfrage max. ansteht
_overpass_gate = threading.Semaphore(OVERPASS_MAX_PARALLEL)

# Drosselung ist kein Ausfall: overpass-frontend wartet bei 429 exponentiell
# (500 ms, ×3 je Versuch, max. 3 Versuche) statt aufzugeben. Genauso hier — aber
# nur bei SCHNELLEN Fehlern (429/504); nach einer Zeitüberschreitung ist das
# Zeitbudget ohnehin aufgebraucht.
OVERPASS_RETRIES = 2         # zusätzliche Versuche nach Drosselung
OVERPASS_BACKOFF = 0.5       # Sekunden, verdreifacht sich je Versuch


# Kurzzeit-Cache für identische Abfragen (POI-Kategorie aus-/wieder einschalten,
# Seiten-Reload, gleicher Kartenausschnitt). Entlastet die öffentlichen Overpass-
# Server spürbar — die drosseln bei häufigen Wiederholungen und antworten dann
# minutenlang zäh oder gar nicht.
OVERPASS_CACHE_TTL  = 600   # Sekunden
OVERPASS_CACHE_MAX  = 200   # Einträge
_overpass_cache      = {}   # key -> (zeitstempel, daten)
_overpass_cache_lock = threading.Lock()


def _overpass_cache_get(key):
    with _overpass_cache_lock:
        hit = _overpass_cache.get(key)
        if not hit:
            return None
        if time.time() - hit[0] >= OVERPASS_CACHE_TTL:
            del _overpass_cache[key]
            return None
        return hit[1]


def _overpass_cache_put(key, data):
    with _overpass_cache_lock:
        _overpass_cache[key] = (time.time(), data)
        if len(_overpass_cache) > OVERPASS_CACHE_MAX:
            oldest = min(_overpass_cache, key=lambda k: _overpass_cache[k][0])
            del _overpass_cache[oldest]


def _overpass_fetch_one(ep, qs, body, timeout):
    """Eine einzelne Overpass-Anfrage; wirft bei Fehler.

    `body` ist der ROHE Query (bytes). Das früher benutzte Formular-Format
    ('data=<urlencodiert>' mit Content-Type x-www-form-urlencoded) nahmen die
    Endpoints nicht an — die Anfrage lief jedes Mal ins Timeout, wodurch die
    Strecken-POI-Suche gar nicht funktionierte.
    """
    headers = {'User-Agent': 'RadreisePlaner/1.0', 'Accept': 'application/json',
               'Accept-Encoding': 'gzip'}   # POI-Antworten sind groß, gzip spart Zeit
    t0, ok = time.time(), False
    try:
        if body is None:
            req = urllib.request.Request(ep + qs, headers=headers)
        else:
            req = urllib.request.Request(ep, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if (resp.headers.get('Content-Encoding') or '').lower() == 'gzip':
                raw = gzip.decompress(raw)
        ok = True
        return raw
    finally:
        # Slot erst hier freigeben: ein Nachzügler hält seine Verbindung wirklich
        # bis zum Ende offen und belegt so lange auch beim Server einen Platz.
        _ep_release(ep, time.time() - t0 if ok else None)


def _overpass_raw_query(body: bytes) -> bytes:
    """Holt den rohen Query aus dem Request-Body des Frontends.
    Das Frontend schickt 'data=<urlencodiert>'; ältere/direkte Aufrufer den Query pur."""
    text = body.decode('utf-8', 'replace')
    if text.startswith('data='):
        return urllib.parse.unquote_plus(text[5:]).encode('utf-8')
    return body


def _overpass_race(qs='', body=None, timeout=OVERPASS_TIMEOUT):
    """Fragt den aussichtsreichsten Endpoint an und schaltet nur bei Bedarf nach.

    Ein zweiter (bzw. dritter) Endpoint wird erst gestartet, wenn nach
    OVERPASS_STAGGER Sekunden noch keine Antwort da ist — die erste gültige
    Antwort gewinnt. Dadurch entsteht im Normalfall EINE Anfrage statt drei; die
    früher übliche Wolke aus nicht abbrechbaren Verlierer-Anfragen (die die zwei
    erlaubten Slots je Server dauerhaft belegte) gibt es nicht mehr.
    Wird alles gedrosselt, wird nach kurzer Pause wiederholt (siehe unten).
    Identische Abfragen kommen aus dem Cache (siehe _overpass_cache_get).
    Rückgabe: (daten_bytes, None) oder (None, fehlertext).
    """
    ckey = body if body is not None else qs
    cached = _overpass_cache_get(ckey)
    if cached is not None:
        return cached, 'CACHE'   # Sonderfall: kein Fehler, sondern Cache-Treffer

    # Anstellen statt losstürmen (siehe OVERPASS_MAX_PARALLEL): mehrere Abfragen
    # gleichzeitig überschritten sonst das Limit gleichzeitiger Abfragen je IP
    # und wurden allesamt mit 429 abgewiesen.
    if not _overpass_gate.acquire(timeout=OVERPASS_QUEUE_WAIT):
        return None, f'zu viele gleichzeitige Abfragen (> {OVERPASS_QUEUE_WAIT}s gewartet)'
    try:
        # Während des Wartens kann eine gleichlautende Abfrage die Antwort bereits
        # eingetragen haben — dann gar nicht erst ins Netz gehen.
        cached = _overpass_cache_get(ckey)
        if cached is not None:
            return cached, 'CACHE'

        gesamtfrist = time.time() + timeout + 8   # Obergrenze inkl. Wiederholungen

        def versuch():
            """Ein Durchgang über die Endpoints. Rückgabe: (daten|None, fehlerliste)."""
            pending  = _ep_order()[:OVERPASS_MAX_TRIES]   # noch nicht gestartete
            futures  = {}                                 # future -> endpoint
            errs     = []
            frist    = min(gesamtfrist,
                           time.time() + timeout + OVERPASS_STAGGER * (len(pending) - 1))

            def start_next():
                """Startet den ersten Endpoint, bei dem noch ein Slot frei ist."""
                for i, ep in enumerate(pending):
                    if not _ep_reserve(ep):
                        continue           # alle Slots dieser Maschine belegt
                    pending.pop(i)
                    try:
                        futures[_OVERPASS_POOL.submit(
                            _overpass_fetch_one, ep, qs, body, timeout)] = ep
                    except Exception:
                        _ep_release(ep, None)
                        raise
                    return True
                return False

            while time.time() < frist:
                start_next()
                if not futures:
                    if not pending:
                        break
                    time.sleep(0.25)       # alle Maschinen ausgelastet — kurz warten
                    continue
                rest = frist - time.time()
                if rest <= 0:
                    break
                done, _ = concurrent.futures.wait(
                    futures,
                    timeout=min(OVERPASS_STAGGER, rest) if pending else rest,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    host = futures.pop(fut).split('/')[2]
                    try:
                        data = fut.result()
                        if data:
                            return data, errs
                        errs.append(f'{host}: leere Antwort')
                    except urllib.error.HTTPError as e:
                        # 429 = Drosselung wegen zu vieler Abfragen — für den Nutzer klar
                        # unterscheidbar von "Server weg", denn hier hilft nur abwarten.
                        errs.append(f'{host}: {"Drosselung (429)" if e.code == 429 else f"HTTP {e.code}"}')
                    except Exception as e:
                        errs.append(f'{host}: {"Zeitüberschreitung" if isinstance(e, (TimeoutError, socket.timeout)) else type(e).__name__}')
                if not futures and not pending:
                    break
            if futures and not errs:
                errs.append('Gesamt-Zeitüberschreitung')
            return None, errs

        errs = []
        for n in range(OVERPASS_RETRIES + 1):
            data, errs = versuch()
            if data is not None:
                _overpass_cache_put(ckey, data)
                return data, None
            # Nur bei Drosselung/Überlastung wiederholen: die kommen schnell zurück,
            # eine Zeitüberschreitung hat das Budget dagegen schon aufgebraucht.
            gedrosselt = bool(errs) and all(('429' in e or '504' in e or '503' in e)
                                            for e in errs)
            pause = OVERPASS_BACKOFF * (3 ** n)
            if (not gedrosselt or n == OVERPASS_RETRIES
                    or time.time() + pause + 5 > gesamtfrist):
                break
            time.sleep(pause)
        return None, '; '.join(errs) or 'alle Endpoints ausgelastet'
    finally:
        _overpass_gate.release()


# ── HTTP-Handler ──────────────────────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def _path(self):
        return self.path.split('?')[0].rstrip('/')

    def _ingress_path(self):
        """HA setzt diesen Header wenn die App über Ingress aufgerufen wird."""
        return self.headers.get('X-Ingress-Path', '').rstrip('/')

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        p = self._path()
        if p in ('', '/', '/radreise_planer.html'):
            self._serve_html()
        elif p == '/api/websites':
            self._json(200, load_ws())
        elif p == '/api/targets':
            self._json(200, load_targets())
        elif p == '/api/manual-camps':
            self._json(200, load_manual_camps())
        elif p == '/api/route-data':
            if os.path.exists(ROUTE_DATA_FILE):
                self._json(200, _load_json(ROUTE_DATA_FILE))
            else:
                self._json(404, {'error': 'Keine gespeicherte Route'})
        elif p == '/api/tours':
            try:    self._json(200, list_tours())
            except Exception as e: self._json(500, {'error': str(e)})
        elif p.startswith('/api/tours/'):
            d = load_tour(p[len('/api/tours/'):])
            self._json(200, d) if d else self._json(404, {'error': 'Tour nicht gefunden'})
        elif p == '/api/segments-refreshed':
            d = _load_json(SEGMENTS_REFRESHED_FILE)
            self._json(200, d if d else None)
        elif p.startswith('/api/segment-status/'):
            seg = p[len('/api/segment-status/'):]
            if not _segment_name_ok(seg):
                self._json(400, {'error': 'Ungültiger Segment-Name'})
            else:
                seg_file = os.path.join(SEGMENTS_DIR, f'{seg}.rd5')
                if os.path.exists(seg_file) and _segment_status.get(seg) != 'downloading':
                    self._json(200, {'status': 'ready', 'segment': seg})
                else:
                    status = _segment_status.get(seg, 'unknown')
                    self._json(200, {'status': status, 'segment': seg})
        elif p.startswith('/api/tiles/'):
            # /api/tiles/{layer}/{z}/{x}/{y}.png
            parts = p[len('/api/tiles/'):].split('/')
            if len(parts) == 4 and parts[3].endswith('.png'):
                self._proxy_tile(parts[0], parts[1], parts[2], parts[3][:-4])
            else:
                self.send_response(404); self.end_headers()
        elif p.startswith('/api/brouter'):
            self._proxy_brouter()
        elif p.startswith('/api/overpass'):
            self._proxy_overpass()
        elif p.startswith('/api/geocode'):
            self._proxy_geocode()
        else:
            super().do_GET()

    def _serve_html(self):
        """
        Liefert radreise_planer.html aus.
        Bei HA-Ingress wird ein kleiner JS-Patch eingefügt, der alle fetch('/api/...')-
        Aufrufe des Browsers mit dem Ingress-Pfad-Präfix versieht.
        """
        html_path = os.path.join(APP_DIR, 'radreise_planer.html')
        try:
            with open(html_path, 'rb') as f:
                content = f.read()
        except FileNotFoundError:
            self._json(404, {'error': 'radreise_planer.html nicht gefunden'})
            return

        ingress = self._ingress_path()
        if ingress:
            # Fetch-Interceptor: /api/-Pfade über den Ingress-Proxy leiten.
            # _TILE_BASE wird von TILE_LAYERS genutzt damit auch <img>-Kacheln
            # den richtigen Pfad bekommen (Leaflet nutzt kein fetch() für Tiles).
            patch = (
                f'<script>/* HA-Ingress patch */'
                f'(function(){{var b={json.dumps(ingress)};'
                f'window._TILE_BASE=b;'
                f'var F=window.fetch;'
                f'window.fetch=function(u,o){{if(typeof u==="string"&&u.startsWith("/api/"))u=b+u;'
                f'return F.call(this,u,o)}};'
                f'}})();</script>'
            ).encode()
            content = content.replace(b'</head>', patch + b'</head>', 1)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self._cors()
        self.end_headers()
        self.wfile.write(content)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        p    = self._path()
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if p == '/api/websites':
            save_ws(json.loads(body));           self._json(200, {'ok': True})
        elif p == '/api/targets':
            save_targets(json.loads(body));      self._json(200, {'ok': True})
        elif p == '/api/manual-camps':
            save_manual_camps(json.loads(body)); self._json(200, {'ok': True})
        elif p == '/api/route-data':
            _save_json(ROUTE_DATA_FILE, json.loads(body))
            self._json(200, {'ok': True})
        elif p == '/api/download-segment':
            body_data = json.loads(body)
            seg = body_data.get('segment', '')
            if not _segment_name_ok(seg):
                self._json(400, {'error': 'Ungültiger Segment-Name'})
            else:
                seg_file = os.path.join(SEGMENTS_DIR, f'{seg}.rd5')
                if os.path.exists(seg_file):
                    self._json(200, {'status': 'ready', 'segment': seg})
                elif _segment_status.get(seg) == 'downloading':
                    self._json(200, {'status': 'downloading', 'segment': seg})
                else:
                    _segment_status[seg] = 'downloading'
                    t = threading.Thread(target=_download_segment_bg, args=(seg,), daemon=True)
                    t.start()
                    self._json(200, {'status': 'downloading', 'segment': seg})
        elif p == '/api/tours':
            try:    self._json(200, {'ok': True, 'id': save_tour(json.loads(body))})
            except Exception as e: self._json(500, {'error': str(e)})
        elif p == '/api/overpass':
            # POST-Variante: body ist 'data=<url-encoded-query>'
            # Wird für lange around-Abfragen (Route-Modus) verwendet
            self._proxy_overpass_post(body)
        else:
            self.send_response(404); self.end_headers()

    # ── DELETE ────────────────────────────────────────────────────────────────
    def do_DELETE(self):
        p = self._path()
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if p.startswith('/api/tours/'):
            ok = delete_tour(p[len('/api/tours/'):])
            self._json(200 if ok else 404, {'ok': ok})
        elif p == '/api/segments-refreshed':
            if os.path.exists(SEGMENTS_REFRESHED_FILE):
                os.remove(SEGMENTS_REFRESHED_FILE)
            self._json(200, {'ok': True})
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    # ── Kachel-Proxy ──────────────────────────────────────────────────────────
    def _proxy_tile(self, layer, z, x, y):
        """
        Proxied OSM-Kacheln – umgeht Browser-Referrer-Policies (z.B. Firefox/HA-Ingress).
        Kacheln werden lokal gecacht (7 Tage) um OSM-Server zu entlasten.
        """
        if layer not in TILE_SOURCES:
            self.send_response(404); self.end_headers(); return
        try:
            int(z); int(x); int(y)
        except ValueError:
            self.send_response(400); self.end_headers(); return

        # Cache-Lookup
        cache_path = os.path.join(TILE_CACHE_DIR, layer, z, x, f'{y}.png')
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'public, max-age=604800')
                self._cors()
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                pass  # Fallback: neu laden

        # Upstream-Fetch
        s   = ['a', 'b', 'c'][(int(x) + int(y)) % 3]
        url = TILE_SOURCES[layer].format(s=s, z=z, x=x, y=y)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; RadreisePlaner/1.2; +https://github.com/chbrockhaus/radreise-planer)',
                'Referer':    'https://www.openstreetmap.org/',
                'Accept':     'image/png,image/*,*/*',
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                ct   = resp.headers.get('Content-Type', 'image/png')
            # Atomisches Cache-Schreiben
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            tmp = cache_path + '.tmp'
            with open(tmp, 'wb') as f: f.write(data)
            os.replace(tmp, cache_path)
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Cache-Control', 'public, max-age=604800')
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code); self.end_headers()
        except Exception:
            self.send_response(502); self.end_headers()

    # ── Overpass-Proxy ────────────────────────────────────────────────────────
    def _send_overpass(self, data, err):
        """Gemeinsame Antwort für GET- und POST-Variante.
        err == 'CACHE' bedeutet Erfolg aus dem Zwischenspeicher."""
        if data is None:
            # 'detail' enthält NUR die Gründe je Server — das Frontend baut daraus
            # seinen eigenen Satz (sonst verschachteln sich zwei Meldungen).
            self._json(502, {'error': f'Overpass nicht erreichbar ({err})', 'detail': err})
            return
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('X-Overpass-Cache', 'hit' if err == 'CACHE' else 'miss')
        self._cors()
        self.end_headers()
        self._safe_write(data)

    def _proxy_overpass(self):
        """GET-Variante: leitet ?data=... weiter (kurze Abfragen).
        Alle Endpoints werden parallel angefragt (siehe _overpass_race)."""
        data, err = _overpass_race(qs=self.path[len('/api/overpass'):])
        self._send_overpass(data, err)

    def _proxy_geocode(self):
        """Proxied Nominatim-Ortssuche serverseitig — Nominatims Nutzungsbedingungen
        verlangen einen aussagekräftigen User-Agent statt Browser-Referrer."""
        qs = self.path[len('/api/geocode'):]  # ?q=...&format=json&limit=5
        url = 'https://nominatim.openstreetmap.org/search' + qs
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'RadreisePlaner/1.0 (Bikepacking-Routenplaner)', 'Accept': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self._safe_write(data)
        except urllib.error.HTTPError as e:
            self._json(e.code, {'error': f'Nominatim HTTP {e.code}'})
        except Exception as e:
            self._json(502, {'error': f'Nominatim nicht erreichbar ({type(e).__name__})'})

    def _proxy_overpass_post(self, body: bytes):
        """POST-Variante für lange around-Abfragen (sprengen das URL-Längenlimit).
        Alle Endpoints werden parallel angefragt (siehe _overpass_race)."""
        data, err = _overpass_race(body=_overpass_raw_query(body),
                                   timeout=OVERPASS_TIMEOUT_POST)
        self._send_overpass(data, err)

    def _proxy_brouter(self):
        qs  = self.path[len('/api/brouter'):]
        url = f'http://localhost:{BROUTER_PORT}/brouter{qs}'
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self._json(502, {'error': str(e)})

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────
    def _safe_write(self, data):
        # Client kann abbrechen (paralleles Promise.any, Navigation) – kein Traceback.
        try:
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self._cors()
        self.end_headers()
        self._safe_write(data)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        pass  # HTTP-Request-Logging unterdrückt

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    for d in [DATA_DIR, TOURS_DIR, SEGMENTS_DIR]:
        os.makedirs(d, exist_ok=True)

    start_brouter()

    log('=== Radreise Planer (Docker/HA) ===')
    log(f'  App      : {APP_DIR}')
    log(f'  Daten    : {DATA_DIR}')
    log(f'  Segmente : {SEGMENTS_DIR}')
    log(f'  Port     : {PORT}')

    class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True  # Threads sterben mit dem Server
        # Auf IPv6 UND IPv4 lauschen. Lauscht der Server nur auf IPv4, während der
        # aufrufende Client "localhost" zuerst zu ::1 (IPv6) auflöst, läuft JEDER
        # Request erst in einen ~2 s langen Verbindungs-Timeout, bevor er auf IPv4
        # zurückfällt — das machte die gesamte App zäh.
        address_family = socket.AF_INET6
        def server_bind(self):
            # IPV6_V6ONLY explizit abschalten, damit IPv4-Clients weiter verbinden.
            try:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except OSError:
                pass
            super().server_bind()
        def handle_error(self, request, client_address):
            # Vom Client abgebrochene Verbindungen sind normal – kein Traceback.
            exc = sys.exc_info()[1]
            if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
                return
            super().handle_error(request, client_address)

    try:
        srv = ThreadingHTTPServer(('::', PORT), Handler)
    except OSError:
        # Container/System ohne IPv6 — auf reines IPv4 zurückfallen
        ThreadingHTTPServer.address_family = socket.AF_INET
        srv = ThreadingHTTPServer(('', PORT), Handler)
    log(f'  ✓ Bereit: http://localhost:{PORT}/')
    with srv:
        try:
            srv.serve_forever()
        finally:
            if brouter_proc:
                brouter_proc.terminate()
