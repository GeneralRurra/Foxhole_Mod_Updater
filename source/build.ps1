$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$releaseRoot = Split-Path -Parent $sourceRoot
$buildRoot = Join-Path $sourceRoot 'build'
python -m venv (Join-Path $buildRoot 'venv')
if ($LASTEXITCODE -ne 0) { throw 'Python-Umgebung konnte nicht erstellt werden.' }
$runtime = Join-Path $buildRoot 'venv\Scripts\python.exe'
& $runtime -m pip install 'pyinstaller==6.22.3'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller-Installation fehlgeschlagen.' }
& $runtime -m PyInstaller --noconfirm --onefile --windowed --name FoxholeModUpdater --distpath $releaseRoot --workpath (Join-Path $buildRoot 'work') --specpath $buildRoot (Join-Path $sourceRoot 'updater.py')
if ($LASTEXITCODE -ne 0) { throw 'Build fehlgeschlagen.' }
