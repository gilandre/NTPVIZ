@echo off
echo =============================================
echo   COMMIT FINAL - CORRECTION MYSQL ERREUR 502
echo =============================================
echo Ajout des scripts de correction MySQL...

git add fix_mysql_auth_final.sh
git add deploy_fix_mysql.sh
git add SOLUTION_URGENCE_502.md

echo Commit des corrections MySQL finales...
git commit -m "Correction erreur 502 - Authentification MySQL complete"

echo Push vers GitHub...
git push origin dev

echo.
echo =============================================
echo   SCRIPTS MYSQL DISPONIBLES SUR GITHUB
echo =============================================
echo.
echo SCRIPTS MYSQL SPECIALISES:
echo - fix_mysql_auth_final.sh
echo - deploy_fix_mysql.sh
echo.
echo SOLUTION URGENCE MISE A JOUR:
echo - SOLUTION_URGENCE_502.md (avec correction MySQL)
echo.
echo =============================================
echo   USAGE SUR LE SERVEUR POUR ERREUR 1698
echo =============================================
echo.
echo SOLUTION AUTOMATIQUE MYSQL:
echo curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_fix_mysql.sh ^| sudo bash
echo.
echo SOLUTION MANUELLE (voir SOLUTION_URGENCE_502.md):
echo 1. sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root_password_123';"
echo 2. Creer utilisateur ntp_monitor
echo 3. Mettre a jour .env
echo 4. Redemarrer service
echo.
echo =============================================

pause 