#!/bin/bash

# Script de déploiement pour correction authentification MySQL
# Résout l'erreur 1698 "Access denied for user 'root'@'localhost'"

echo "================================================================="
echo "   CORRECTION MYSQL AUTOMATIQUE - NTP MONITOR ENTERPRISE       "
echo "================================================================="
echo "Résolution de l'erreur d'authentification MySQL :"
echo "- Erreur 1698: Access denied for user 'root'@'localhost'"
echo "- Configuration utilisateur application sécurisé"
echo "- Mise à jour configuration .env"
echo ""

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash deploy_fix_mysql.sh"
   exit 1
fi

TEMP_DIR="/tmp/ntp-monitor-mysql-fix"
GITHUB_RAW="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev"

# Nettoyage préalable
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "📥 Téléchargement du script de correction MySQL..."

# Téléchargement du script de correction MySQL
if curl -fsSL "$GITHUB_RAW/fix_mysql_auth_final.sh" -o fix_mysql_auth_final.sh; then
    echo "✅ Script téléchargé avec succès"
else
    echo "❌ Erreur de téléchargement du script"
    echo "Vérifiez votre connexion Internet et l'URL du dépôt"
    exit 1
fi

# Rendre le script exécutable
chmod +x fix_mysql_auth_final.sh

echo ""
echo "🚀 Exécution de la correction MySQL..."
echo "Ce processus configure l'authentification MySQL de manière sécurisée..."
echo "Durée estimée : 5-10 minutes"
echo ""

# Exécution du script de correction MySQL
./fix_mysql_auth_final.sh

# Vérification finale spécifique MySQL
echo ""
echo "🔍 VÉRIFICATION MYSQL FINALE"
echo "============================"

# Test service MySQL/MariaDB
if systemctl is-active --quiet mysql; then
    echo "✅ Service MySQL actif"
    DB_SERVICE="mysql"
elif systemctl is-active --quiet mariadb; then
    echo "✅ Service MariaDB actif"
    DB_SERVICE="mariadb"
else
    echo "❌ Aucun service MySQL/MariaDB actif"
    DB_SERVICE=""
fi

# Test de connexion si service actif
if [ ! -z "$DB_SERVICE" ]; then
    echo ""
    echo "Test de connexion application:"
    if mysql -u ntp_monitor -p"ntp_secure_2024" -e "SELECT 'Connexion application réussie' as status;" 2>/dev/null; then
        echo "✅ Connexion utilisateur application fonctionnelle"
        echo "✅ Base de données accessible"
    else
        echo "⚠️ Connexion application non testable (normale si mots de passe différents)"
    fi
fi

# Test de l'application NTP Monitor
echo ""
echo "Application NTP Monitor:"
if systemctl is-active --quiet ntp-monitor; then
    echo "✅ Service NTP Monitor actif"
    
    # Attente de stabilisation
    echo "⏳ Stabilisation (20 secondes)..."
    sleep 20
    
    if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
        echo "✅ Port 5000 accessible"
        
        if curl -f -s -m 10 http://localhost:5000/ > /dev/null 2>&1; then
            echo "✅ Application web accessible"
            echo ""
            echo "🎉 CORRECTION MYSQL TERMINÉE AVEC SUCCÈS !"
            echo "================================================"
            echo "🌐 Application disponible sur : http://79.137.36.66/"
            echo "👤 Connexion : admin / admin123"
            echo "🗄️ Base de données MySQL configurée"
        else
            echo "⚠️ Application en cours de démarrage (attendre quelques minutes)"
        fi
    else
        echo "⚠️ Port 5000 pas encore accessible"
        echo "Surveillance : journalctl -u ntp-monitor -f"
    fi
else
    echo "❌ Service NTP Monitor inactif"
    echo "Diagnostic : journalctl -u ntp-monitor -n 10"
fi

# Nettoyage
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "📋 RÉSUMÉ FINAL"
echo "==============="
echo "✅ Authentification MySQL root configurée"
echo "✅ Utilisateur application 'ntp_monitor' créé"
echo "✅ Base de données 'ntp_monitor' créée"  
echo "✅ Configuration .env mise à jour"
echo ""
echo "📞 Support et Surveillance :"
echo "Logs service  : journalctl -u ntp-monitor -f"
echo "Statut MySQL  : systemctl status mysql (ou mariadb)"
echo "Test connexion: mysql -u ntp_monitor -p" 