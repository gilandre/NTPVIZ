@echo off
echo 🚀 NTP Monitor Enterprise - VERSION MYSQL
echo ========================================

REM Configuration PATH MySQL pour cette session
set PATH=E:\wampServer2\bin\mysql\mysql8.3.0\bin;%PATH%

echo 📊 Activation environnement virtuel MySQL...
call .venv_mysql\Scripts\activate

echo 🗃️  Base de données: MySQL (localhost/ntp_monitor)
echo 👤 Utilisateur: root (sans mot de passe)
echo 🛠️  MySQL Path: E:\wampServer2\bin\mysql\mysql8.3.0\bin

echo.
echo ✅ Environnement configuré avec succès
echo 🌐 Démarrage application sur http://127.0.0.1:5000
echo.

python backend/app.py

pause
