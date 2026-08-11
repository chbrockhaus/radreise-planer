# Changelog — Radreise Planer

## v1.10.2 (2026-08-11)
- **Das OSM-Protokollfenster ist jetzt deutlich größer und in der Größe verstellbar.** Standard ist gut doppelt so breit und doppelt so hoch wie bisher (640 × 560 statt 310 Pixel breit). Am blau schraffierten Griff oben links lässt es sich beliebig größer oder kleiner ziehen — das Fenster hängt unten rechts fest, wächst also nach oben und links und läuft nie über den Kartenrand hinaus. Die eingestellte Größe bleibt für das nächste Mal gespeichert. Die Abfrageliste wächst dabei mit.

## v1.10.1 (2026-08-11)
- **Fix: „811 Treffer" gemeldet, aber keine Punkte auf der Karte** — erst Aus- und Wiedereinschalten der Kategorie machte sie sichtbar. Ursache: Die App merkt sich je Kategorie, welche Orte schon gezeichnet sind (damit beim Verschieben keine doppelten Punkte entstehen). An zwei Stellen wurden die Punkte von der Karte genommen, ohne diese Merkliste zu leeren — danach galt jeder Treffer als „schon vorhanden" und wurde übersprungen. Betraf vor allem den Fall „zu weit herausgezoomt, dann wieder hinein" sowie den Abbrechen-Knopf. Beides läuft jetzt über eine gemeinsame Funktion, die immer beides zurücksetzt.
- **Mehr Infos im OSM-Protokollfenster** (🛰-Schaltfläche):
  - Jede erfolgreiche Abfrage zeigt jetzt zusätzlich, **welcher Server geantwortet hat**, die **Antwortgröße** und — falls es nicht der erste Versuch war — den wievielten (z. B. „177 Treffer · 4,1 s · 75 kB · lambert").
  - Neu darüber eine **Übersicht aller OSM-Server** mit ihrer gemessenen Antwortzeit, laufenden Abfragen und einer Restzeit, falls ein Server nach Fehlern gerade übersprungen wird (z. B. „kumi — gesperrt 1 min", „lambert — 936 ms"). Damit ist ohne Umweg sichtbar, ob der bevorzugte Server wieder läuft.

## v1.10.0 (2026-08-11)
- **`overpass.kumi.systems` ist wieder erste Wahl** (derselbe Server, den auch BRouter-Web benutzt). Die übrigen Server bleiben als Rückfall dahinter.
- **Neu: Die Sperre für einen ausgefallenen Server verdoppelt sich** bei jedem weiteren Fehlversuch (90 s, 3 min, 6 min … bis 15 min), statt immer nach 90 Sekunden erneut anzulaufen. Ein Server, der längere Zeit nicht antwortet, kostet dadurch nur noch selten Wartezeit — sobald er wieder da ist, ist er sofort wieder erste Wahl.

## v1.9.9 (2026-08-11)
- **Fix: OSM-Abfragen waren weiterhin zeitweise langsam und brachen ab.** Ursache waren gleich mehrere Punkte, die sich gegenseitig verstärkt haben. Zum Vergleich wurde angesehen, wie es BRouter-Web macht (es nutzt die Bibliothek `overpass-frontend`) — die entscheidenden Prinzipien von dort sind jetzt übernommen:
  - **Alle POI-Kategorien kommen in eine gemeinsame Abfrage.** Bisher löste jede aktive Kategorie eine eigene Abfrage aus, alle gleichzeitig — bei acht Kategorien also acht Abfragen, obwohl die OSM-Server nur zwei gleichzeitig erlauben. Der Rest wurde ohne Antwort in deren Warteschlange gestellt und lief bei uns in die Zeitüberschreitung. Jetzt: höchstens vier Kategorien je Abfrage, die Treffer werden anschließend anhand ihrer Merkmale wieder den Kategorien zugeordnet. Gemessen: acht Kategorien entlang der Strecke = 2 Abfragen statt 8.
  - **Nur noch fehlende Kategorien werden nachgeladen.** Schaltet man eine weitere Kategorie hinzu, wird ausschließlich diese abgefragt; die übrigen kommen aus dem Zwischenspeicher (gemessen: 0 statt 5 Abfragen).
  - **Statt Abbrechen wird eingereiht.** Beim Verschieben der Karte wurde die laufende Abfrage bisher abgebrochen — das half aber nicht, weil der Server sie trotzdem zu Ende rechnet und dabei weiter einen der zwei erlaubten Plätze belegt; die neue Abfrage lief dadurch in die Drosselung. Jetzt läuft immer nur eine Abfrage, eine dazwischen angeforderte wird gemerkt und danach einmal mit dem dann aktuellen Kartenausschnitt nachgeholt. Gemessen: drei schnelle Kartenbewegungen = 2 Abfragen statt 6, ohne Fehler.
  - **Server fragt gestaffelt statt alle gleichzeitig an.** Bisher wurden bei jeder Abfrage alle drei OSM-Server parallel angefragt; die beiden Verlierer liefen im Hintergrund bis zu 25 Sekunden weiter (abbrechen lässt sich das nicht) und belegten so lange Plätze. Nach wenigen Abfragen blockierte die App sich damit selbst. Jetzt wird zuerst nur der schnellste Server gefragt und ein zweiter erst zugeschaltet, wenn nach 2,5 Sekunden keine Antwort da ist.
  - **Zwei Server waren in Wahrheit einer.** `overpass.private.coffee` und `overpass.kumi.systems` laufen auf derselben Maschine — nach Namen gezählt hat die App ihr doppelt so viele gleichzeitige Abfragen geschickt wie erlaubt. Die Zählung hängt jetzt an der Serveradresse, nicht am Namen.
  - **Zwei zusätzliche Server aufgenommen.** `overpass-api.de` verteilt auf zwei Rechner und erwischte zeitweise einen überlasteten (Fehler 504), während der andere dieselbe Abfrage in 0,5 Sekunden beantwortete. Beide sind jetzt direkt ansprechbar; welcher zuerst gefragt wird, entscheidet die gemessene Antwortzeit. Wer Fehler liefert, wird 90 Sekunden lang übersprungen.
  - **Drosselung führt nicht mehr sofort zum Fehler**, sondern zu einer kurzen Wartepause mit erneutem Versuch (0,5 s, dann 1,5 s).
  - Antworten werden komprimiert übertragen (gzip), und der Browser gibt nicht mehr früher auf als der Server selbst — bisher konnte er eine Abfrage abbrechen, die gerade noch beantwortet worden wäre.

## v1.9.8 (2026-08-11)
- **Fix: Mehrere POI-Kategorien gleichzeitig liefen zwangsläufig in die Drosselung.** Die öffentlichen OSM-Server erlauben laut ihrer eigenen Statusauskunft nur **2 gleichzeitige Abfragen pro Nutzer** — wurden mehrere Kategorien auf einmal geladen, wies der Server alle darüber hinaus mit „429 Too Many Requests" ab. Der Server stellt Abfragen jetzt in eine Warteschlange und lässt höchstens zwei gleichzeitig durch (weitere warten bis zu 20 Sekunden, statt sofort abgewiesen zu werden). Damit bleibt die App dauerhaft innerhalb des erlaubten Rahmens, statt sich selbst auszusperren.

## v1.9.7 (2026-08-11)
- **Fehlermeldungen bei OSM-Abfragen sagen jetzt, was wirklich los ist.** Bisher hieß es pauschal „Overpass nicht erreichbar (Wartung/Überlastung?)" — egal ob die Server gedrosselt haben, überlastet waren oder tatsächlich ausgefallen sind. Jetzt wird unterschieden: Bei Drosselung (429) oder Überlastung (504/Zeitüberschreitung) steht sinngemäß „Server gerade überlastet — legt sich meist nach ein paar Minuten, bereits geladene Ergebnisse bleiben nutzbar", statt einen Ausfall zu suggerieren. Im OSM-Aktivitätsprotokoll steht zudem pro Server der genaue Grund (z. B. „overpass-api.de: HTTP 504; kumi.systems: Zeitüberschreitung"), sodass man sieht, ob es an einem einzelnen Server liegt oder an allen.

## v1.9.6 (2026-08-11)
- **Fix: „Erst schnell, danach viel zu langsam".** Wurde die Karte verschoben oder gezoomt, während eine OSM-Abfrage lief, startete die App zusätzliche Abfragen, ohne die alten abzubrechen — bei mehrmaligem Verschieben stapelten sich die Anfragen. Die öffentlichen OSM-Server drosseln daraufhin, wodurch alles Folgende zäh wurde. Jetzt wird eine überholte Abfrage derselben Kategorie sofort abgebrochen (gemessen: nach 50–500 ms statt bis zum Ende). Zusätzlich behoben: es wurde nur die jeweils letzte Abfrage als abbrechbar vermerkt, ältere liefen unkontrolliert weiter.
- **Neu: OSM-Aktivitätsprotokoll** (🛰-Schaltfläche bei den Kartensteuerelementen). Zeigt laufende Abfragen mit mitlaufender Dauer sowie beendete mit Ergebnis: Trefferzahl, Dauer, ob die Antwort aus dem Zwischenspeicher kam, abgebrochen oder fehlgeschlagen. Damit ist nachvollziehbar, was im Hintergrund passiert.
- Aufgeräumt: Der Notfall-Umweg über einen fremden CORS-Proxy wurde entfernt. Seit die Abfragen über den eigenen Server laufen, baute er nur noch eine unsinnige Adresse zusammen und erzeugte Fehlermeldungen in der Browser-Konsole.

## v1.9.5 (2026-08-11)
- **Fix: App war insgesamt zäh — jeder einzelne Server-Aufruf kostete ~2 Sekunden.** Der Server lauschte nur auf IPv4, während `localhost` zuerst zu IPv6 (`::1`) aufgelöst wird. Dadurch lief JEDER Aufruf (Kartenkacheln, Routing, POI-Suche, Speichern) erst in einen ~2-Sekunden-Verbindungs-Timeout, bevor er auf IPv4 zurückfiel. Gemessen: 2,057 s → 0,019 s pro Aufruf. Der Server lauscht jetzt gleichzeitig auf IPv6 und IPv4.
- **Fix: OSM-Abfragen probierten die Server nacheinander durch statt gleichzeitig.** Der erste Server in der Liste (overpass-api.de) ist regelmäßig überlastet (gemessen ~23 s), ein weiterer war gar nicht erreichbar — deren Timeouts summierten sich, bevor die schnellen Server (~2–3 s) überhaupt gefragt wurden. Jetzt werden alle gleichzeitig angefragt, die erste Antwort gewinnt. Der dauerhaft nicht erreichbare Server wurde entfernt.
- **Fix: Strecken-POI-Suche funktionierte gar nicht.** Lange Abfragen entlang der Route werden per POST geschickt — das POST-Format war falsch (Formular-kodiert statt roher Abfrage), sodass die Server jedes Mal ins Timeout liefen. Im lokalen Server fehlte die POST-Behandlung zudem komplett (404).
- **Neu: Serverseitiger Zwischenspeicher für OSM-Abfragen** (10 Minuten). Identische Abfragen — POI-Kategorie aus- und wieder einschalten, gleicher Kartenausschnitt, Seiten-Reload — kommen jetzt sofort aus dem Speicher (gemessen 360 ms → 3 ms) statt erneut über das Netz. Das entlastet auch die öffentlichen OSM-Server, die bei häufigen Wiederholungen drosseln.

## v1.9.4 (2026-08-11)
- **Neu: Ortssuche auf der Karte.** Neuer 🔍-Button in den Kartensteuerelementen — Ort, Adresse oder POI eingeben, aus den Treffern wählen, die Karte springt dorthin und setzt einen Marker. Läuft über einen neuen serverseitigen Proxy zu Nominatim (`/api/geocode`), damit kein CORS-Problem im Browser entsteht und Nominatims Nutzungsbedingungen (eigener User-Agent) eingehalten werden.

## v1.9.3 (2026-08-11)
- **Neu: Klick ins Höhenprofil zeigt den Punkt auf der Karte.** Bisher gab es nur beim Hover einen kleinen Marker an der entsprechenden Stelle — die Karte selbst blieb aber unverändert, auch wenn der Punkt weit außerhalb des sichtbaren Ausschnitts lag. Ein Klick auf eine Stelle im Höhenprofil verschiebt (und zoomt bei Bedarf) die Karte jetzt so, dass der Punkt sichtbar wird. Ist er bereits ausreichend nah sichtbar, bewegt sich die Karte nicht unnötig.

## v1.9.2 (2026-07-19)
- Fix: Im Plan-Modus („+ Neue Tour" → „✏ Tour planen") blieben die Karte und die Etappen-Sidebar einer bereits geladenen Tour während des gesamten Planens sichtbar — verwirrend, da alte und neu geklickte Route sich überlagerten. Karte und Sidebar werden jetzt beim Start des Plan-Modus geleert; bricht man ab, erscheint die alte Tour unverändert wieder (nichts wird bis zum tatsächlichen Fertigstellen zerstört).

## v1.9.1 (2026-07-19)
- **Neu: Tour verlängern.** Neuer Header-Button „🧭 Verlängern" — Klick auf die Karte setzt ein neues Ziel, die App routet vom bisherigen Streckenende dorthin und hängt den neuen Abschnitt an die bestehende Tour an. Bestehende Etappen (Länge, Camp-Ziele, Notizen) bleiben dabei komplett unangetastet — es werden nur so viele neue Etappen wie nötig ergänzt, um den neu hinzugekommenen Abschnitt abzudecken, benannt nach dem neuen Ziel.

## v1.9.0 (2026-07-19)
- **Fix: Beim Start wurde manchmal eine alte Route geladen statt der aktuellen.** Die App lud beim Öffnen zuerst die aktuell gespeicherte Route korrekt, hat sie danach aber automatisch durch die zuletzt über „💾 Touren" geöffnete/gespeicherte Tour ersetzt (`localStorage`-Auto-Load) — das überschrieb still den Titel, die Kilometerangabe und alles andere im Header mit alten Daten, unabhängig davon was zuletzt tatsächlich aktiv war. Dieses automatische Nachladen wurde komplett entfernt: Beim Start zählt jetzt nur noch die aktuell auf dem Server gespeicherte Route.

## v1.8.9 (2026-07-19)
- **Fix: Abzweigpunkt bei Camp-Ziel warf noch immer zu viel der Originalroute weg.** v1.8.6 verglich mehrere Kandidaten-Abzweigpunkte nach reiner Gesamtstrecke (Route bis dahin + echte BRouter-Distanz zum Ziel) — dabei gewinnt fast immer ein früher Abzweig, weil JEDE direkte BRouter-Verbindung numerisch kürzer ist als eine kurvige, aber sinnvoll fortschreitende Originalstrecke, auch wenn diese gar keine Schleife fährt (Beispiel: Etappe bei Siegen). Jetzt wird zuerst per Luftlinie geprüft, ob die Route überhaupt eine ECHTE Schleife fährt (sich vom Ziel entfernt und länger als 5 km nicht wieder annähert) — nur dann wird vor der Schleife abgebogen. Ohne Schleife bleibt die komplette Originalroute bis zur nächsten Annäherung erhalten; die echte BRouter-Distanz wird nur noch in einem schmalen ±3-km-Fenster um diesen Punkt zur Feinjustierung genutzt (z. B. bei einer Flussquerung in der Nähe), nicht mehr über die ganze Etappe.

## v1.8.8 (2026-07-19)
- **Fix: „🔁 Neu routen" veränderte die Strecke viel zu stark.** BRouter bekam bisher pro Etappe (bzw. bei „alle Etappen" sogar über die komplette Tour) nur Start- und Endpunkt als Wegpunkte — dazwischen hatte BRouter völlig freie Wahl und konnte einen komplett anderen Weg picken als die ursprünglich aufgezeichnete Route (z. B. eine andere Talseite oder einen großen Umweg). Jetzt werden zusätzlich Zwischenpunkte aus der Originalroute (alle ~8 km) als Wegpunkte mitgegeben, sodass die neu berechnete Strecke nah am ursprünglichen Verlauf bleibt und wirklich nur mit dem aktuellen BRouter-Profil aktualisiert wird, statt großflächig neu erfunden zu werden. Betrifft sowohl den Reroute einzelner Etappen als auch „Alle Etappen".

## v1.8.7 (2026-07-19)
- Fix: Versionsnummer im Header (Logo oben links) war hartcodiert und blieb bei den letzten Versionsbumps auf „v1.8.3" stehen, obwohl `config.yaml` schon weiter war. Jetzt synchron mit der tatsächlichen Version.

## v1.8.6 (2026-07-19)
- **Fix: Abzweigpunkt bei Camp-Ziel per echter BRouter-Distanz statt Luftlinie** — behebt eine Überkorrektur aus v1.8.4. Luftlinie ist als Schätzung für die tatsächliche Straßenlänge unzuverlässig: mal zu optimistisch (v1.8.3 und früher — der Abzweig landete NACH einer unnötigen Schleife der Originalroute, die man zurückfahren musste), mal zu pessimistisch für kurze Reststrecken (v1.8.4 — fast die komplette Originalroute wurde verworfen, weil jede Luftlinien-Abkürzung besser aussah als sie in Wirklichkeit war). Jetzt werden mehrere Kandidaten-Abzweigpunkte entlang der Route real bei BRouter angefragt (Route bis zum Kandidat + echte BRouter-Distanz zum Ziel) und der günstigste gewählt. Am Testfall (Etappe Marburg → Amöneburg) wählt der Algorithmus jetzt korrekt den Abzweig bei Cölbe statt sofort am Etappenanfang oder erst kurz vor dem Ziel.

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
