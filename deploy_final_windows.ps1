# Script PowerShell Final - Corrections NTP Monitor Windows
# Compatible Windows 10/11 - Execution simple

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  CORRECTIONS FINALES - NTP MONITOR" -ForegroundColor Cyan  
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Correction erreur 'partitioned' + MySQL fallback" -ForegroundColor Green
Write-Host ""

# Execution du script de correction
Write-Host "1. Execution des corrections..." -ForegroundColor Yellow
python fix_universal_clean.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "2. Corrections appliquees avec succes!" -ForegroundColor Green
    
    # Test de l'application
    Write-Host "3. Test de l'application..." -ForegroundColor Yellow
    $testResult = python -c "from backend.app import create_app; print('OK')"
    
    if ($testResult -eq "OK") {
        Write-Host "4. Application testee avec succes!" -ForegroundColor Green
        
        # Proposer de demarrer
        Write-Host ""
        Write-Host "Demarrer l'application maintenant? (O/N): " -ForegroundColor Yellow -NoNewline
        $choice = Read-Host
        
        if ($choice -match '^[OoYy]') {
            Write-Host "5. Demarrage de l'application..." -ForegroundColor Green
            Write-Host "URL: http://localhost:5000" -ForegroundColor Cyan
            Write-Host "Comptes: admin/admin123" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Appuyez sur Ctrl+C pour arreter l'application" -ForegroundColor Yellow
            Write-Host ""
            
            # Demarrage
            python app.py
        } else {
            Write-Host "5. Pour demarrer plus tard:" -ForegroundColor Cyan
            Write-Host "   - Executer: python app.py" -ForegroundColor White
            Write-Host "   - Ou: start_ntp.bat" -ForegroundColor White
        }
    } else {
        Write-Host "4. Erreur lors du test de l'application" -ForegroundColor Red
        Write-Host "Verifiez les logs: Get-Content logs/app.log -Tail 20" -ForegroundColor Yellow
    }
} else {
    Write-Host "2. Erreur lors des corrections" -ForegroundColor Red
    Write-Host "Verifiez la sortie ci-dessus pour plus de details" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Script termine." -ForegroundColor Cyan
Read-Host "Appuyez sur Entree pour fermer" 