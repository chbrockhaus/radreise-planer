# Changelog — Radreise Planer

## v1.3.8 (2026-07-18)
- Fix: Beim Camp-Abstecher fuhr die Route am Abzweig erst ein Stück über die Straßen-Abbiegung hinaus und dann zurück. Der Abzweig wird jetzt ~0,6 km *vor* dem nächstgelegenen Punkt angesetzt, sodass BRouter die Abbiegung natürlich anfährt (kein U-Turn). Hinweis: Ist der Campingplatz nur über eine Stichstraße erreichbar, bleibt das Hin- und Zurück auf dieser Zufahrt physikalisch bestehen.

## v1.3.7 (2026-07-18)
- Fix: Rückweg vom Campingplatz-Etappenziel führte zurück zum Abzweig statt vorwärts. Der Wiedereinstieg in die Route liegt jetzt in Fahrtrichtung *vor* dem Abzweig (Abstand proportional zur Entfernung des Camps von der Route) — der Umweg wird zu einem Bogen nach vorne statt einer Rückkehr.

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
