#!/usr/bin/env python3
"""
Radreise Planer – HTTP-Server für Docker / Home Assistant Add-on.

Änderungen gegenüber der Windows-Version:
  • Pfade über Umgebungsvariablen konfigurierbar (DATA_DIR, BROUTER_DIR, …)
  • Java-Aufruf über PATH (kein Windows-spezifischer Pfad)
  • HA-Ingress-Unterstützung: injiziert Fetch-Interceptor in die HTML-Seite,
    damit /api/-Aufrufe des Browsers korrekt durch den Ingress-Proxy geleitet werden.
"""

import http.server
import json
import os
import subprocess
import sys
import urllib.request
import datetime

# ── Konfiguration ─────────────────────────────────────────────────────────────
PORT         = int(os.environ.get('PORT', 3000))
DATA_DIR     = os.environ.get('DATA_DIR',     '/data')
BROUTER_DIR  = os.environ.get('BROUTER_DIR',  '/opt/brouter')
SEGMENTS_DIR = os.environ.get('SEGMENTS_DIR', os.path.join(DATA_DIR, 'segments4'))
PROFILES_DIR = os.environ.get('PROFILES_DIR', os.path.join(BROUTER_DIR, 'profiles2'))
CUSTOM_DIR   = os.environ.get('CUSTOM_DIR',   os.path.join(BROUTER_DIR, 'customprofiles'))
BROUTER_MEM  = os.environ.get('BROUTER_MEMORY_MB', '256')

WEBSITES_FILE     = os.path.join(DATA_DIR, 'camping_websites.json')
TARGETS_FILE      = os.path.join(DATA_DIR, 'routing_targets.json')
MANUAL_CAMPS_FILE = os.path.join(DATA_DIR, 'manual_camps.json')
ROUTE_DATA_FILE   = os.path.join(DATA_DIR, 'route_data_custom.json')
TOURS_DIR         = os.path.join(DATA_DIR, 'tours')

BROUTER_PORT = 17777
APP_DIR      = os.path.dirname(os.path.abspath(__file__))

brouter_proc = None

# ── BRouter ───────────────────────────────────────────────────────────────────
def start_brouter():
    global brouter_proc
    jar = os.path.join(BROUTER_DIR, 'brouter.jar')
    if not os.path.exists(jar):
        print(f'  BRouter: brouter.jar nicht gefunden: {jar}', flush=True)
        return
    if not os.listdir(SEGMENTS_DIR):
        print('  BRouter: Keine Routing-Daten in segments4/ — Routing nicht verfügbar', flush=True)
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
        print(f'  BRouter gestartet (PID {brouter_proc.pid}) auf Port {BROUTER_PORT}', flush=True)
    except Exception as e:
        print(f'  BRouter Startfehler: {e}', flush=True)

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
                'id':         d.get('id', fname[:-5]),
                'name':       d.get('name', 'Unbekannt'),
                'route_name': d.get('route_name', ''),
                'created':    d.get('created', ''),
                'modified':   d.get('modified', ''),
                'total_km':   d.get('total_km', 0),
                'num_stages': d.get('num_stages', 0),
            })
    return sorted(tours, key=lambda t: t.get('modified') or t.get('created', ''), reverse=True)

def save_tour(data):
    os.makedirs(TOURS_DIR, exist_ok=True)
    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    tid = _safe_id(data.get('id') or '') or str(int(datetime.datetime.utcnow().timestamp() * 1000))
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
        elif p.startswith('/api/brouter'):
            self._proxy_brouter()
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
            # Minimaler Fetch-Interceptor: leitet absolute /api/-Pfade über den Ingress-Proxy
            patch = (
                f'<script>/* HA-Ingress fetch-patch */'
                f'(function(){{var b={json.dumps(ingress)};var F=window.fetch;'
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
        elif p == '/api/tours':
            try:    self._json(200, {'ok': True, 'id': save_tour(json.loads(body))})
            except Exception as e: self._json(500, {'error': str(e)})
        else:
            self.send_response(404); self.end_headers()

    # ── DELETE ────────────────────────────────────────────────────────────────
    def do_DELETE(self):
        p = self._path()
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if p.startswith('/api/tours/'):
            ok = delete_tour(p[len('/api/tours/'):])
            self._json(200 if ok else 404, {'ok': ok})
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    # ── BRouter-Proxy ─────────────────────────────────────────────────────────
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
    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self._cors()
        self.end_headers()
        self.wfile.write(data)

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

    print('=== Radreise Planer (Docker/HA) ===', flush=True)
    print(f'  App      : {APP_DIR}', flush=True)
    print(f'  Daten    : {DATA_DIR}', flush=True)
    print(f'  Segmente : {SEGMENTS_DIR}', flush=True)
    print(f'  Port     : {PORT}', flush=True)

    srv = http.server.HTTPServer(('', PORT), Handler)
    print(f'  ✓ Bereit: http://localhost:{PORT}/', flush=True)
    with srv:
        try:
            srv.serve_forever()
        finally:
            if brouter_proc:
                brouter_proc.terminate()
