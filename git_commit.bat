@echo off
chcp 65001 >nul
echo Ajout des fichiers de correction erreur 502...
git add fix_502_complete.sh
git add deploy_fix_502.sh
git add CORRECTION_ERREUR_502.md
git add quick_fix_deployment.sh
git add deploy_complete_update.sh

echo Commit des modifications...
git commit -m "Scripts correction erreur 502 - NTP Monitor Enterprise"

echo Push vers GitHub...
git push origin dev

echo Termine!
pause 