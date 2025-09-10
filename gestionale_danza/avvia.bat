@echo off
title Gestionale Scuola di Danza
color 0A

echo.
echo  ============================================
echo  ^|      GESTIONALE SCUOLA DI DANZA        ^|
echo  ^|                                        ^|
echo  ^|         Avvio Automatico...            ^|
echo  ============================================
echo.

REM Impostazioni base
set PORTA=5000
set LOG_FILE=gestionale.log

REM Verifica se esiste l'eseguibile compilato
if exist "gestionale_danza.exe" (
    echo [INFO] Trovato eseguibile compilato - Avvio in modalita' produzione
    echo [INFO] Avvio gestionale_danza.exe sulla porta %PORTA%
    echo.
    echo Apri il browser all'indirizzo: http://localhost:%PORTA%
    echo.
    echo Per chiudere l'applicazione, premi CTRL+C in questa finestra
    echo.
    start "Browser" http://localhost:%PORTA%
    gestionale_danza.exe %PORTA%
    goto :fine
)

REM Se non esiste l'eseguibile, prova con Python
echo [INFO] Eseguibile non trovato - Tentativo avvio con Python
echo.

REM Verifica se Python e' disponibile
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato nel sistema
    echo.
    echo Opzioni disponibili:
    echo 1. Installa Python da https://python.org
    echo 2. Usa l'eseguibile compilato gestionale_danza.exe
    echo.
    pause
    goto :fine
)

REM Verifica se esiste app.py
if not exist "app.py" (
    echo [ERRORE] File app.py non trovato nella directory corrente
    echo Assicurati di essere nella cartella corretta del progetto
    echo.
    pause
    goto :fine
)

REM Verifica se esiste requirements.txt e installa dipendenze
if exist "requirements.txt" (
    echo [INFO] Controllo dipendenze Python...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [ATTENZIONE] Alcune dipendenze potrebbero non essere state installate
        echo Continuo comunque con l'avvio...
        echo.
    )
) else (
    echo [ATTENZIONE] File requirements.txt non trovato
    echo Alcune dipendenze potrebbero mancare
    echo.
)

REM Avvia l'applicazione Flask
echo [INFO] Avvio applicazione Flask sulla porta %PORTA%
echo.
echo Apri il browser all'indirizzo: http://localhost:%PORTA%
echo.
echo Login predefinito:
echo   Username: admin
echo   Password: admin123
echo.
echo Per chiudere l'applicazione, premi CTRL+C in questa finestra
echo.

REM Apri il browser automaticamente dopo 3 secondi
timeout /t 3 /nobreak >nul
start "Browser" http://localhost:%PORTA%

REM Avvia Flask con logging
python app.py %PORTA% 2>&1 | tee %LOG_FILE%

:fine
echo.
echo [INFO] Applicazione terminata
if exist "%LOG_FILE%" (
    echo [INFO] Log salvato in %LOG_FILE%
)
echo.
pause