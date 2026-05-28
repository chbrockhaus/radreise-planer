# Radreise Planer – Home Assistant Add-on Repository

Dieses Repository enthält das Home Assistant Add-on für den **Radreise Planer** –
einen Bikepacking-Routenplaner für mehrtägige Radreisen.

## Add-on hinzufügen

1. In Home Assistant: **Einstellungen → Add-ons → Add-on Store**
2. Oben rechts: **⋮ → Repositories**
3. URL dieses Repositories eintragen:
   ```
   https://github.com/DEIN-USERNAME/radreise-planer
   ```
4. **Radreise Planer** im Store suchen und installieren

## Konfiguration

| Option | Standard | Beschreibung |
|--------|----------|--------------|
| `brouter_segments` | `["E5_N50", "E10_N50"]` | BRouter-Routing-Daten-Segmente (5°×5°-Kacheln). Deutschland = E5_N50 + E10_N50 |
| `brouter_memory_mb` | `256` | Java-Heap für BRouter in MB. Bei Raspberry Pi ggf. auf 128 reduzieren |

### Segment-Auswahl

Die Segmente entsprechen 5°×5°-Kacheln des BRouter-Routing-Netzwerks.
Beim ersten Start werden fehlende Segmente automatisch heruntergeladen (~100 MB je Segment).

| Segment | Region |
|---------|--------|
| `E5_N50` | NRW, Hessen, Thüringen (West) |
| `E10_N50` | Sachsen, Thüringen (Ost), Sachsen-Anhalt |
| `E15_N50` | Brandenburg, Polen (West) |
| `E0_N50` | Belgien, Niederlande, Westdeutschland |

## Daten & Persistenz

Alle Benutzerdaten werden im HA-Datenpfad gespeichert und bleiben bei Updates erhalten:

```
/data/
├── tours/              ← gespeicherte Touren
├── segments4/          ← BRouter-Routing-Daten (automatisch geladen)
├── route_data_custom.json  ← aktive Route
├── routing_targets.json    ← Camping-Zielrouten
├── manual_camps.json       ← manuell hinzugefügte Campingplätze
└── camping_websites.json   ← Campingplatz-Website-Notizen
```

## Erste Schritte

1. Add-on installieren und starten
2. **Web UI öffnen** (erscheint in der HA-Sidebar als „Radreise Planer")
3. GPX-Datei laden oder neue Tour über die Kartenplanung erstellen
4. Etappen anpassen und Campingplätze suchen
