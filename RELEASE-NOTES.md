# Version 1.0.0

## Deutsch

**VirusTotal: 9/71 Erkennungen am 04.10.2026, einschließlich Microsoft Defender. Ursache ungeklärt. Kein Nachweis für „virenfrei“.** [Scanbericht](https://www.virustotal.com/gui/file/83ba51bcef3d871d3e65b486e2da976692d0617d9255235d26358c509f247cf6).

Verwalte deine installierten Foxhole-Mods bequem: verfügbare Updates gesammelt installieren sowie Mods mit einem Klick aktivieren und deaktivieren. Gespeicherte Quellen ersparen dir die erneute Suche nach deinen Mods.

Portable Windows-Version mit automatischer Steam-Bibliothekssuche.

- Mod-Erkennung, bekannte Quellenvorschläge und Browser-Suche auf itch.io/Nexus.
- Kostenlose itch.io-PAK-Downloads, Versionsvergleich und Downgrade-Sperre.
- Einzel- und Sammelupdates mit Vorschau, Download-/Installationsfortschritt.
- Sicherungen, Wiederherstellung, Deaktivieren/Aktivieren und Dublettenbereinigung.
- Originaldateischutz einschließlich Datei-Verweisen; Prozessprüfung ohne Testausnahme.
- Bildschirmangepasste Fenster und scrollbar erreichbare Aktionen.
- Sperre gegen parallele Instanzen im selben Programmordner.

## Validierung

Offline-Regressionstests prüfen Versionen, Originaldateischutz, Hardlinks,
Aktivieren/Deaktivieren, Mehrdatei-Austausch, Sicherung, Wiederherstellung,
Downgrade-Sperre, Dialoge, Fortschritt und das Entfernen der Testausnahme.
Die gebaute Windows-EXE wurde auf diesem Rechner gestartet und auf Tk- und
Versionsfunktion geprüft. Ein Foxhole-Spieltest und Tests auf weiteren Rechnern
wurden nicht durchgeführt.

## Grenzen

Bezahl-/Login-Downloads und Archive benötigen Browserdownload und PAK-Import.
Versionen ohne erkennbares Dateisuffix bleiben unbekannt. Die App prüft nicht die
Spielkompatibilität. Die EXE ist nicht digital signiert.

## Distribution

ZIP enthält EXE, Quellcode, Buildskript, Regressionstests, Anleitung und Lizenzen.
Keine Mods, Spieldateien, persönlichen Einstellungen, Sicherungen oder Testdaten.


## English

**VirusTotal: 9/71 detections on October 4, 2026, including Microsoft Defender. Cause unresolved. This is not a “virus-free” result.** [Scan report](https://www.virustotal.com/gui/file/83ba51bcef3d871d3e65b486e2da976692d0617d9255235d26358c509f247cf6).

Manage your installed Foxhole mods easily: install available updates together and enable or disable mods with one click. Saved sources mean you do not have to search for your mods again for each update.

- Portable Windows app with automatic Steam library detection; no separate Python installation required.
- Supported free itch.io PAK downloads, version comparison and downgrade prevention.
- Individual and batch updates with a preview and download/installation progress.
- Backups, restoration, reversible enable/disable and duplicate consolidation.
- Protection for `War-WindowsNoEditor.pak`, including references to the original file.
- Known source suggestions and browser searches on itch.io and Nexus Mods.

The interface is currently in German. German and English instructions are available in the repository README.

### Download

Download the Windows x64 ZIP attached to this release, extract it completely and run `FoxholeModUpdater.exe`. The SHA-256 file is provided to verify the ZIP.

### Validation and limitations

Offline regression tests and an EXE startup check passed on the development machine. No in-game Foxhole test or testing on other machines has been performed. The EXE is unsigned.

Login-required downloads, paid content and archives require a browser download and PAK import. Versions without recognizable filename suffixes remain unknown. Game compatibility is not automatically checked.

The release contains the EXE, source code, build script, tests, documentation and licenses. No mods, game files, personal settings, backups or test data are included.
