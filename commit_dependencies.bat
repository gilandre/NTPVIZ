@echo off
echo Ajout des scripts de correction des dependances...
git add fix_502_dependencies.sh
git add deploy_fix_dependencies.sh
git add CORRECTION_ERREUR_502.md

echo Commit des modifications...
git commit -m "Correction erreur 502 - Scripts dependances Python"

echo Push vers GitHub...
git push origin dev

echo Scripts de correction des dependances disponibles sur GitHub:
echo - fix_502_dependencies.sh
echo - deploy_fix_dependencies.sh  
echo - CORRECTION_ERREUR_502.md mis a jour

pause 