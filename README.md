# Foxhole Mod Updater

[Deutsch](#deutsch) · [English](#english)


## Deutsch


Mit diesem Tool kannst du deine installierten Foxhole-Mods einfach verwalten: verfügbare Updates gesammelt installieren und Mods mit einem Klick aktivieren oder deaktivieren. So musst du bekannte Mod-Seiten nicht bei jedem Update erneut suchen.

Für unterstützte kostenlose itch.io-Downloads übernimmt der Updater Download und Installation. Andere Quellen können einen manuellen Download benötigen.

**[Windows-Version herunterladen](https://github.com/GeneralRurra/Foxhole_Mod_Updater/releases/latest)**

Im Release die Datei `FoxholeModUpdater-v1.0.1-Windows-x64.zip` herunterladen,
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
6.22.3 wurden für diesen Build verwendet. `source/build.ps1` erstellt ab v1.0.1 einen Programmordner mit EXE und `runtime`. Beide müssen zusammen bleiben.
`source/test_release.py` prüft Dateioperationen mit temporären Testdateien.
Die App steht unter MIT-Lizenz, die eingebetteten Laufzeitkomponenten haben eigene
Lizenzen in `licenses`. Spiel- und Mod-Inhalte bleiben Eigentum ihrer Rechteinhaber.


## English


Foxhole Mod Updater helps you manage your installed Foxhole mods: install available updates together and enable or disable individual mods with one click. Save your mod sources so you do not have to search for them again whenever an update is released.

For supported free itch.io downloads, the updater handles downloading and installation. Other sources may require a manual download.

**[Download the Windows app](https://github.com/GeneralRurra/Foxhole_Mod_Updater/releases/latest)**

Download `FoxholeModUpdater-v1.0.1-Windows-x64.zip` from the release, extract the entire ZIP and run `FoxholeModUpdater.exe`. The GitHub **Code → Download ZIP** option contains the source code; the ready-to-run Windows app is provided in Releases.

This is a portable Windows app. No separate Python installation is required. This independent community project is not affiliated with Siege Camp. No mods or game files are included.

### Getting started

Extract the ZIP to a writable folder. The app searches your Steam libraries for Foxhole. If it cannot find the game, select `Foxhole/War/Content/Paks` manually.

Settings, backups and disabled mods are stored beside the EXE. Keep these data files and folders when updating or moving the app. The app interface is currently in German; this documentation is available in German and English.

### Updating your mods

1. Click **Alle auf Updates prüfen** (Check all for updates) to download matching supported free itch.io PAK files.
2. Click **Alle Updates installieren** (Install all updates) to review the new files and the old files that will be replaced.
3. Click **Updates jetzt installieren** (Install updates now) to back up old files and install the updates.

Download and installation progress show the current operation. Older files of the same mod variant and identical duplicates from the same source are consolidated. Installed filenames match the downloads. Language and variant choices are respected; unfamiliar renames may require a one-time selection.

Versions are read from filenames and saved installation information. Recognizably older versions are not offered as updates. Letter suffixes are ordered after the numeric version, such as 1.3a after 1.3. Without a version number, the app can only detect different file contents, which does not necessarily mean newer. Compatibility with your Foxhole version is not automatically checked.

### Enabling, disabling and finding mods

**Aktivieren / Deaktivieren** (Enable / Disable) reversibly moves the selected mod to the `disabled` folder or restores it to the game folder. Disabled mods are not updated. Other active copies remain separate entries.

**Quellen finden** (Find sources) suggests known mod pages and opens browser searches on itch.io or Nexus Mods. Unknown sources can be assigned manually.

Nexus downloads requiring login, paid content and ZIP/RAR downloads need to be downloaded through the mod page. Extract archives and use **PAK importieren** (Import PAK). The app does not bypass payment or login requirements. Installed mods are kept when a source is unavailable. Not every PAK can be reliably identified as a mod.

### Backups and protection

**Sicherungen verwalten** (Manage backups) shows dates, versions and sizes. Restoring a backup brings back the previous filenames and files. Existing filename conflicts are blocked. Backups can be deleted after confirmation. Keep the `backups` and `disabled` folders when moving the app.

**War-WindowsNoEditor.pak is protected.** References to the original game file are also blocked. Close Foxhole before modifying mod files; there is no test-mode exception.

### Requirements and local data

- 64-bit Windows and a Steam installation or a manually selected Paks folder.
- No account or API key needed for supported free itch.io downloads.
- Network access is used for checking and downloading; browser searches open only when clicked.
- No telemetry is sent. Mod sources and file paths are stored locally in `mods.json`.
- Temporary downloads are removed on normal exit. Run one app instance per folder.
- The portable EXE is not digitally signed.

### Source code, tests and license

The source code is in `source/updater.py`. This release was built using Python 3.11, Tkinter and PyInstaller 6.22.3. From v1.0.1, `source/build.ps1` builds a directory containing the Windows EXE and `runtime`; keep both together, and `source/test_release.py` tests file operations with temporary files.

The app is licensed under MIT. Embedded runtime components have their own licenses in `licenses`. Game and mod content remains the property of its respective rights holders.
