@echo off
echo ========================================
echo   COMMIT FINAL - CORRECTION ERREUR 502
echo ========================================
echo Ajout de tous les scripts de correction...

git add fix_502_final.sh
git add deploy_fix_final.sh
git add SOLUTION_URGENCE_502.md
git add CORRECTION_ERREUR_502.md

echo Commit des corrections finales...
git commit -m "Correction erreur 502 - Solution complete finale"

echo Push vers GitHub...
git push origin dev

echo.
echo ========================================
echo   SCRIPTS DISPONIBLES SUR GITHUB
echo ========================================
echo.
echo SOLUTION URGENCE (5 minutes):
echo - SOLUTION_URGENCE_502.md
echo.
echo SCRIPTS AUTOMATIQUES:
echo - deploy_fix_final.sh (RECOMMANDE)
echo - deploy_fix_502.sh
echo - deploy_fix_dependencies.sh
echo.
echo SCRIPTS MANUELS:
echo - fix_502_final.sh
echo - fix_502_complete.sh
echo - fix_502_dependencies.sh
echo.
echo GUIDE COMPLET:
echo - CORRECTION_ERREUR_502.md
echo.
echo ========================================
echo   USAGE SUR LE SERVEUR
echo ========================================
echo.
echo SOLUTION RAPIDE (5 min):
echo Voir SOLUTION_URGENCE_502.md
echo.
echo SOLUTION AUTOMATIQUE:
echo curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_fix_final.sh ^| sudo bash
echo.
echo ========================================

pause 