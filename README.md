# Foxhole Mod Updater 1.0.0

**[Windows-Version herunterladen](https://github.com/GeneralRurra/Foxhole_Mod_Updater/releases/latest)**

Im Release die Datei `FoxholeModUpdater-v1.0.0-Windows-x64.zip` herunterladen,
vollständig entpacken und die EXE starten. Unter „Code → Download ZIP“ liegt der
Quellcode; die startbare Windows-App befindet sich im Release.

Eine portable Windows-App zum Verwalten lokaler Foxhole-Mods. Kein separates
Python erforderlich. Unabhängiges Community-Projekt, ohne Verbindung zu Siege Camp.
Mods und Spieldateien sind nicht im Download enthalten.

## Start

ZIP vollständig in einen beschreibbaren Ordner entpacken und
`FoxholeModUpdater.exe` starten. Foxhole wird über Steam-Bibliotheken gesucht.
Falls es nicht gefunden wird, `Foxhole/War/Content/Paks` manuell auswählen.
Einstellungen, Sicherungen und deaktivierte Mods bleiben neben der EXE.
Bei späteren Programmupdates diese Datenordner behalten.

## Updates

1. **Alle auf Updates prüfen** lädt passende kostenlose itch.io-PAK-Dateien.
2. **Alle Updates installieren** zeigt zuerst neue und zu ersetzende Dateien.
3. **Updates jetzt installieren** sichert alte Dateien und installiert Updates.

Download- und Installationsfortschritt zeigen den aktuellen Vorgang. Alte
Versionen derselben Variante und identische Dubletten derselben Quelle werden
zusammengeführt. Dateinamen entsprechen den Downloads. Sprache und Varianten
werden berücksichtigt. Unbekannte Umbenennungen benötigen eine Zuordnung.

Versionen stammen aus Dateinamen und gespeicherten Installationen. Erkennbare
ältere Versionen werden nicht als Update angeboten. Buchstabensuffixe werden
nach der numerischen Version geordnet, beispielsweise 1.3a nach 1.3.
Ohne Versionsnummer erkennt der Updater nur unterschiedliche Dateiinhalte.
Das bedeutet nicht zwingend neuer. Spielkompatibilität wird nicht automatisch geprüft.

## Mods und Quellen

**Aktivieren / Deaktivieren** lagert eine Mod reversibel in `disabled` aus.
Deaktivierte Mods werden nicht aktualisiert. Andere aktive Kopien bleiben eigene Einträge.
**Quellen finden** schlägt bekannte Seiten vor und öffnet Suchanfragen auf
itch.io oder Nexus Mods. Unbekannte Quellen lassen sich manuell zuordnen.

Nexus-Downloads mit Anmeldung, bezahlte Inhalte und ZIP/RAR-Downloads werden
über die Mod-Seite geladen. Archive entpacken und die passende **PAK importieren**.
Die App umgeht keine Bezahl- oder Login-Freigaben. Bei nicht erreichbaren Quellen
bleiben installierte Mods erhalten. Nicht jede PAK lässt sich als Mod identifizieren.

## Sicherungen und Schutz

**Sicherungen verwalten** zeigt Datum, Version und Größe. Wiederherstellung bringt
die damaligen Dateien zurück; Namenskollisionen werden blockiert. Sicherungen
können nach Bestätigung gelöscht werden. `backups` und `disabled` beim Umzug behalten.

**War-WindowsNoEditor.pak ist gesperrt.** Auch Verweise auf die Originaldatei
werden blockiert. Foxhole muss vor Dateiänderungen geschlossen sein. Es gibt
keine Testausnahme für die Prozessprüfung.

## Daten und Anforderungen

- Windows 64 Bit, Steam-Installation oder manuell ausgewählter Paks-Ordner.
- Keine Anmeldung und kein API-Schlüssel für kostenlose itch.io-Downloads.
- Internetzugriff erfolgt beim Prüfen/Herunterladen; Browser-Suche nur nach Klick.
- Kein Telemetrieversand. Mod-Quellen und Dateipfade werden lokal in `mods.json` gespeichert.
- Cache wird beim regulären Beenden entfernt. Eine Programm-Instanz pro Ordner.
- Portable EXE ist nicht digital signiert.

## Quellcode und Build

`source/updater.py` enthält den Quellcode. Python 3.11 mit Tkinter und PyInstaller
6.22.3 wurden für diesen Build verwendet. `source/build.ps1` erstellt eine EXE.
`source/test_release.py` prüft Dateioperationen mit temporären Testdateien.
Die App steht unter MIT-Lizenz, die eingebetteten Laufzeitkomponenten haben eigene
Lizenzen in `licenses`. Spiel- und Mod-Inhalte bleiben Eigentum ihrer Rechteinhaber.
