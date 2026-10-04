# Version 1.0.0

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
