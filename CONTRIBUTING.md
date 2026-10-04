# Fehler melden und beitragen

Fehler bitte als GitHub Issue mit Windows-Version, Updater-Version, Mod-Seite,
genauer Fehlermeldung und Schritten zum Nachstellen melden. Keine Zugangsdaten,
persönlichen Einstellungen, Spieldateien oder Mod-Dateien hochladen.

Entwicklung benötigt Python 3.11 mit Tkinter. Offline-Tests:

```powershell
python source/test_release.py
```

Windows-EXE erstellen:

```powershell
powershell -ExecutionPolicy Bypass -File source/build.ps1
```

Änderungen am Dateizugriff müssen Originaldateischutz, Spielsperre, Sicherungen
und Wiederherstellung erhalten. Die Regressionstests benutzen temporäre Dateien.
