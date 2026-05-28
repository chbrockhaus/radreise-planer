@echo off
:: Kopiert die aktuelle App-Datei ins Addon-Verzeichnis und pusht auf GitHub
:: Aufruf: sync.bat [commit-nachricht]

set MSG=%~1
if "%MSG%"=="" set MSG=Update Radreise Planer App

echo Kopiere radreise_planer.html ins Addon-Verzeichnis...
copy /Y "..\radreise_planer.html" "radreise-planer\radreise_planer.html"

echo.
echo Committe und pushe...
git add radreise-planer\radreise_planer.html
git commit -m "%MSG%"
git push origin master

echo.
echo Fertig! Home Assistant kann das Add-on jetzt neu bauen.
pause
