#!/bin/bash

# Script de déploiement pour correction finale NTP Monitor
# Installe tous les modules manquants (python-dotenv, pytz, etc.)

echo "======================================================="
echo "   CORRECTION FINALE - DÉPLOIEMENT AUTOMATIQUE       "
echo "======================================================="  
echo "Installation des modules manquants identifiés :"
echo "- python-dotenv (configuration .env)"
echo "- pytz (fuseaux horaires)"
echo "- Test complet de tous les modules"
echo "- Vérification application Flask complète"
echo ""

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash deploy_fix_final.sh"
   exit 1
fi

TEMP_DIR="/tmp/ntp-monitor-final-fix"
GITHUB_RAW="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev"

# Nettoyage préalable
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "📥 Téléchargement du script de correction finale..."

# Téléchargement du script de correction finale
if curl -fsSL "$GITHUB_RAW/fix_502_final.sh" -o fix_502_final.sh; then
    echo "✅ Script téléchargé avec succès"
else
    echo "❌ Erreur de téléchargement du script"
    echo "Vérifiez votre connexion Internet et l'URL du dépôt"
    exit 1
fi

# Rendre le script exécutable
chmod +x fix_502_final.sh

echo ""
echo "🚀 Exécution de la correction finale..."
echo "Ce processus peut prendre 10-15 minutes pour installer et tester tous les modules..."
echo ""

# Exécution du script de correction finale
./fix_502_final.sh

# Vérification finale et rapport
echo ""
echo "🔍 RAPPORT FINAL"
echo "==============="

if systemctl is-active --quiet ntp-monitor; then
    echo "✅ Service ntp-monitor actif"
    
    # Attente supplémentaire pour stabilisation
    echo "⏳ Attente de stabilisation (30 secondes)..."
    sleep 30
    
    if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
        echo "✅ Port 5000 accessible"
        
        # Test de connectivité finale
        if curl -f -s -m 10 http://localhost:5000/ > /dev/null 2>&1; then
            echo "✅ Application web accessible"
            echo ""
            echo "🎉 CORRECTION FINALE RÉUSSIE !"
            echo "================================================"
            echo "🌐 Application NTP Monitor Enterprise disponible sur :"
            echo "   http://79.137.36.66/"
            echo ""
            echo "👤 Comptes utilisateur :"
            echo "   Admin:    admin / admin123"
            echo "   Operator: operator / operator123"
            echo "   Viewer:   viewer / viewer123"
            echo ""
            echo "📋 Surveillance continue :"
            echo "   journalctl -u ntp-monitor -f"
            echo "   systemctl status ntp-monitor"
            echo ""
            echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
        else
            echo "⚠️ Service actif, port ouvert, mais application pas encore totalement accessible"
            echo "L'application peut nécessiter quelques minutes supplémentaires pour être complètement opérationnelle."
        fi
    else
        echo "⚠️ Service actif mais port 5000 non encore accessible"
        echo "Surveillez les logs : journalctl -u ntp-monitor -f"
    fi
else
    echo "❌ Service ntp-monitor toujours inactif"
    echo ""
    echo "🔧 Diagnostic avancé :"
    echo "   journalctl -u ntp-monitor -n 30"
    echo "   systemctl status ntp-monitor -l"
    echo ""
    echo "📞 Modules Python installés :"
    cd /opt/ntp-monitor && source .venv/bin/activate && pip list | grep -E "(flask|redis|celery|psutil|ntplib|pymysql|dotenv|pytz)" 2>/dev/null || echo "Erreur accès environnement virtuel"
fi

# Nettoyage
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "📋 AIDE ET SUPPORT"  
echo "=================="
echo "Logs service     : journalctl -u ntp-monitor -f"
echo "Statut service   : systemctl status ntp-monitor -l"
echo "Redémarrage      : systemctl restart ntp-monitor"
echo "Test manuel      : cd /opt/ntp-monitor && source .venv/bin/activate && python app.py"
echo "Modules installés: cd /opt/ntp-monitor && source .venv/bin/activate && pip list" 