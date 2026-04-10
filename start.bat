@echo off
echo ====================================
echo  TechPilot - Reflex (Python)
echo ====================================
echo.
cd /d "%~dp0"

:: Verifier si l'env virtuel existe
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)

:: Activer l'env virtuel
call .venv\Scripts\activate.bat

:: Installer les dependances
echo Installation des dependances...
pip install -r requirements.txt -q

:: Initialiser Reflex si besoin
if not exist ".web" (
    echo Initialisation Reflex (premiere fois - peut prendre 2-3 minutes)...
    reflex init
)

:: Demarrer
echo.
echo Demarrage TechPilot sur http://localhost:3000
echo.
reflex run

pause
