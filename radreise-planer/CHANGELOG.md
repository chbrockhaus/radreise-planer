# Changelog — Radreise Planer

## v1.8.5 (2026-07-19)
- Fix: Wurde ein Campingplatz direkt auf der Karte (OSM-Overlay „⛳ Route hierher") als Etappenziel gesetzt, blieb die bereits gesuchte Campingplatz-Liste in der Sidebar unverändert vollständig ausgeklappt stehen — statt sich wie beim Setzen eines Ziels aus der Suchliste selbst zu reduzieren. War dieselbe Etappe zuvor schon durchsucht worden, tauchte der Campingplatz dadurch optisch doppelt auf (einmal als normaler Listeneintrag, einmal als „⛳ Ziel"). Die Suchliste klappt jetzt bei JEDEM gesetzten Ziel ein (auch bei Karten-/manuellen Zielen), nicht nur bei Zielen aus der eigenen Suche.
- Fix: Die +/− Buttons zum Anpassen der Etappenlänge in der Sidebar veränderten bisher nur die angeklickte Etappe selbst — der Ausgleich landete unsichtbar in der letzten Restetappe, egal welche Etappe verändert wurde. Jetzt gleicht nur die unmittelbar ANSCHLIESSENDE Etappe aus (wird kürzer, wenn die aktuelle länger gemacht wird, und umgekehrt) — die Buttons sind zusätzlich gesperrt, wenn die anschließende Etappe durch eine eigene Camp-Route festgelegt ist oder selbst am Längenlimit steht.

## v1.8.4 (2026-07-19)
- Fix: Beim Setzen eines neuen Etappenziels (Campingplatz) wurde der Abzweigpunkt bisher rein nach Luftlinien-Nähe zum Ziel gewählt. Lag die Originalroute in einer Schleife (z. B. eine Autobahnauffahrt-Schleife), landete der nächste Punkt oft *hinter* der Schleife — die komplette Schleife musste unnötig mitgefahren werden, obwohl ein viel kürzerer direkter Weg zum neuen Ziel existierte. Der Abzweigpunkt wird jetzt so gewählt, dass die Gesamtstrecke (bereits gefahrene Route + Luftlinie zum Ziel) minimal ist, nicht mehr nur die Luftlinie allein.

## v1.8.3 (2026-07-18)
- Fix: Popup „Als Etappenziel setzen" an gefundenen Campingplätzen (orangene/grüne Punkte) ließ sich nicht öffnen. Ursache: Der Klick löste zusätzlich `selectCamp()` aus, das alle Kartenmarker zerstört und neu aufbaut (inkl. Kartenschwenk zum Camp) — dabei wurde der gerade angeklickte Marker samt Popup sofort wieder entfernt, noch bevor er sichtbar war. Wirkte wie „das Fenster bewegt sich immer mit der Maus weg". Popup wird jetzt gezielt auf dem neu aufgebauten Marker geöffnet. Betraf auch manuell angelegte Campingplätze (dort jetzt ebenfalls ein expliziter Klick-Handler statt implizitem Leaflet-Verhalten).

## v1.8.2 (2026-07-18)
- **Fix: Viel zu hohe Höhenmeter-Anzeige (bis zu 30% und mehr zu viel).** Die Etappen-Höhenmeter wurden bisher durch reine Punkt-zu-Punkt-Summierung des Höhenprofils berechnet — jedes kleine Rauschen im GPS-/DEM-Höhenprofil zählte voll mit, was gegenüber gefilterten Referenzwerten (z. B. BRouter-Web) massiv zu hoch lag (in Tests bis zu +250%). Umgestellt auf ein Hysterese-Verfahren (Standardansatz für dieses Problem, z. B. bei Garmin/Strava): nur Höhenänderungen über 6 m zählen, gemessen ab dem letzten Wendepunkt. An echten BRouter-„filtered ascend"-Werten kalibriert und verifiziert (Ø ~10% Abweichung über mehrere Streckenabschnitte, vorher >100%). Betrifft sowohl die Etappen-Anzeige in der Sidebar als auch den Hover-Tooltip im Höhenprofil-Chart (beide nutzten bisher unterschiedliche, inkonsistente Berechnungen — jetzt vereinheitlicht).

## v1.8.1 (2026-07-18)
- Fix: Bei einer Etappe, die *sowohl* einen Rückweg vom Camp der Vorgänger-Etappe (`campFromPrev`) *als auch* ein eigenes Camp-Ziel (`campTarget`) hatte, zeigte die Sidebar nur den km-Anteil des eigenen Camp-Ziels — der Rückweg-Anteil fehlte in der Anzeige (bis zu mehrere km Abweichung von der tatsächlichen Strecke, die auch exportiert wird). Die Etappenlänge wird jetzt in allen Camp-Fällen direkt aus der tatsächlichen Streckengeometrie berechnet, nicht mehr aus zwei separaten, potenziell auseinanderlaufenden Teilwerten.

## v1.8.0 (2026-07-18)
- **Neu: Fehlende Höhendaten automatisch per BRouter ergänzen.** Fehlt einer importierten GPX-Datei das Höhenprofil, erscheint eine Checkbox „⛰ Höhendaten per BRouter ergänzen" (vorausgewählt) — die Route wird dabei entlang der aufgezeichneten Punkte nachgeroutet, BRouters Geländemodell liefert die Höhe mit. Funktioniert im Single-GPX-Import **und** im Mehrfach-Etappen-Import (dort nur für die Dateien, denen tatsächlich Höhendaten fehlen — vorhandene Profile bleiben unangetastet). Ein einzelner unroutbarer Zwischenpunkt lässt dabei nicht den ganzen Abschnitt scheitern: bei einem Fehler wird die Wegpunktdichte automatisch halbiert und erneut versucht.

## v1.7.0 (2026-07-18)
- **Neu: Mehrere einzelne Etappen-GPX zu einer Reise importieren.** Neuer Tab „🧩 Etappen importieren" im Tour-Dialog: pro Etappe eine eigene GPX-Datei hochladen (Mehrfachauswahl), Reihenfolge per ▲▼ anpassen, Etappen umbenennen oder entfernen. Jede Datei wird exakt eine Etappe — die Etappengrenzen liegen an den Datei-Grenzen, nicht gleichmäßig verteilt. Schließen zwei Dateien nicht nahtlos an (Lücke > 50 m), wird die Verbindung automatisch per BRouter berechnet.
- Intern: Vereinfachung (Douglas-Peucker) und GPS-Lücken-Reparatur aus dem bestehenden Single-GPX-Import wurden als wiederverwendbare Bausteine extrahiert, ohne das bisherige Verhalten zu verändern.

## v1.6.0 (2026-07-18)
- **Neu: Rückgängig-Button** („↶ Rückgängig", oben im Header). Macht die letzten Aktionen schrittweise rückgängig — bis zu 20 Schritte. Der Tooltip zeigt jeweils, was rückgängig gemacht wird.
- Erfasst werden: Campingplatz als Etappenziel setzen/entfernen, Etappengrenze verschieben, Etappenanzahl ändern, Etappenlänge anpassen, Route neu berechnen, manuellen Campingplatz anlegen/löschen sowie das Routen zu einem Camp-POI von der Karte.
- Zusammengesetzte Aktionen (z.B. Neuberechnung mit anschließender Wiederherstellung der Etappenziele) erzeugen bewusst nur **einen** Rückgängig-Schritt. Beim Rückgängig bleibt der Kartenausschnitt erhalten.

## v1.5.0 (2026-07-18)
- **Neu: Etappenziel direkt vom Kartenpunkt setzen.** Klick auf einen Campingplatz-Punkt öffnet jetzt ein Popup mit Name, Etappe, Entfernung, Tagesgäste-Status und einem Button „⛳ Als Etappenziel setzen" bzw. „✗ Ziel entfernen" — der Umweg über die Sidebar entfällt. Funktioniert für Suchergebnisse **und** manuell angelegte Campingplätze (die hatten bisher gar keinen Klick). Der Hover-Tooltip zeigt weiterhin die Kurzinfo und weist auf die Klick-Aktion hin.

## v1.4.6 (2026-07-18)
- Fix: Nach dem Laden (Seitenstart oder gespeicherte Tour) wurde der als Ziel gesetzte Campingplatz **nicht mehr gefunden**. Beim Wiederherstellen wird `campsites` auf den einen gespeicherten Platz reduziert, `campTarget.ci` behielt aber den ursprünglichen Index aus der damaligen Trefferliste (z.B. 3) und zeigte damit ins Leere. Folge: Ziel-Marker „Z" blieb am Routenende statt am Campingplatz, Etappenmarker wanderte nicht mit, GPX-Wegpunkt fiel auf das Etappenende zurück und die Sidebar zeigte nur „Campingplatz". Der Index wird jetzt beim Wiederherstellen korrigiert (Suche per Koordinaten, sonst 0) — eine vollständig wiederhergestellte Trefferliste bleibt unverändert.

## v1.4.5 (2026-07-18)
- Fix: `stageEndLatLon()` lieferte für die **letzte** Etappe ein falsches Ende, sobald Etappengrenzen verschoben waren. Sie leitete das Ende aus der Summe `BASE_KM_INT + adjustKm` ab — die trifft `TOTAL_KM` aber nicht, weil die letzte Etappe `restKm()` nutzt. Bei nach vorn verschobenen Grenzen lag das Ende bis zu 30 km zu früh, was u.a. die „nächste Etappe"-Auswahl beim Camp-POI-Routing verfälschte. Die letzte Etappe endet jetzt immer am Routenende (bzw. an ihrem Camp).

## v1.4.4 (2026-07-18)
- Fix: Der Ziel-Marker „Z" blieb am alten Ziel stehen, wenn für die letzte Etappe ein Campingplatz als Ziel gesetzt wurde. Die letzte Etappe hat keinen eigenen nummerierten Marker — sie wird allein durch „Z" dargestellt, und dessen Position war fest auf das Routenende verdrahtet. „Z" wandert jetzt zum Campingplatz (Tooltip zeigt den Camp-Namen).

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
