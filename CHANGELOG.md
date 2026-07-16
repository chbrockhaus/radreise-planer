# Changelog — Radreise Planer

## v1.3.6 (2026-07-17)
- Neuer Button **↓ Gesamtroute**: exportiert die gesamte Route als einen einzelnen kontinuierlichen GPX-Track (ideal für GPS-Geräte)
- Bestehender **↓ GPX Etappen**-Button bleibt erhalten (separate Tracks pro Etappe)

## v1.3.5 (2026-06-18)
- BRouter-Profile in `profiles2/` kopiert
- Versionsanzeige im Header ergänzt

## v1.3.4
- Fix: Syntaxfehler in BRouter-Profildateien behoben

## v1.3.3
- BRouter-Profil-Auswahl per Dropdown in der Sidebar

## v1.3.2
- Neues BRouter-Profil: `fastbike-lowtraffic-no-bundesstrasse`

## v1.3.1
- Neues BRouter-Profil: `gravel_no_bundesstrasse`

## v1.3.0
- Versionsnummer im Header
- Buttons im Header gruppiert

## v1.2.x
- Automatisches Laden der letzten Tour beim Start
- Plan-Modus: Lange Segmente werden automatisch aufgeteilt (>250 km)
- Plan-Modus: Fehlende BRouter-Segmente werden erkannt und Download angeboten
- POI-Suche: Fehlermeldung wenn nichts gefunden, Debounce optimiert
- Overpass AbortController korrekt verdrahtet
- Zeitstempel in Server-Log
- Diverse Bugfixes im Plan-Modus
