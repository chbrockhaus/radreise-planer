# Changelog — Radreise Planer

## v1.4.3 (2026-07-18)
- Fix: Beim Neuberechnen **aller** Etappen gingen verschobene Etappengrenzen verloren. Ursache: `STAGE_ENDS` wird beim Verschieben einer Grenze nicht mitgeführt (dort ändert sich nur `adjustKm`), diente aber als Wegpunkt-Quelle — zusätzlich wurden die Grenzen danach wieder gleichmäßig verteilt. Jetzt wird durch die **tatsächlichen** Grenzen geroutet und diese bleiben danach erhalten (Etappenlängen aus den echten Abständen abgeleitet).

## v1.4.2 (2026-07-18)
- Fix: Bei einem Campingplatz als Ziel der **letzten** Etappe blieb die alte Zielstrecke sichtbar. Die Route endet jetzt korrekt am Campingplatz — der blaue Rest vom Abzweig bis zum alten Ziel wird nicht mehr gezeichnet. (km und GPX-Export waren bereits korrekt.)
- CHANGELOG.md liegt jetzt im Add-on-Verzeichnis, damit Home Assistant ihn anzeigt.

## v1.4.1 (2026-07-18)
- Fix: Beim Neuberechnen der Route nach Ändern des Routing-Profils gingen die gesetzten Etappenziele (Campingplätze) verloren. Sie werden jetzt vor dem Reroute gesichert und danach auf der neuen Route mit dem neuen Profil automatisch neu berechnet (Such- und manuelle Camps, auf ihrer ursprünglichen Etappe).

## v1.4.0 (2026-07-18)
- **Neu: Campingplatz direkt aus der Karte zur Etappe routen.** Im Popup eines Camp-POI gibt es den Button „⛳ Route hierher (nächste Etappe)". Er ändert automatisch die Etappe, deren aktuelles Ende am nächsten liegt, und routet dorthin.
- **Fix: Höhenmeter berücksichtigen jetzt den Camp-Abstecher.** Bisher zeigte die Sidebar beim Umrouten zu einem Camp nur die Höhenmeter der Hauptroute. Jetzt werden die BRouter-Höhendaten des Abstechers gespeichert und die Etappen-Höhenmeter (↑/↓) korrekt aus dem tatsächlich gefahrenen Verlauf berechnet (auch km waren schon korrekt). Gilt für Such-Camps und manuelle Camps, inkl. Persistenz in gespeicherten Touren.
- **Overpass-Härtung:** Bei Overpass-Ausfall scheitert die Abfrage schnell (Timeout 8s statt 32s) mit klarer Meldung in der UI („Overpass nicht erreichbar – Karte läuft, später erneut versuchen") statt langem Hängen. Server-Log wird nicht mehr mit Verbindungsabbruch-Tracebacks geflutet.
- Code-Sync: Addon-HTML mit der refaktorierten lokalen Version zusammengeführt (Route-Bearbeiten-Helfer).

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
