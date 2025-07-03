#!/bin/bash
# Installation ultra-rapide NTP Monitor Enterprise pour Ubuntu 24.04
# One-liner qui télécharge et exécute l'installateur complet

# Vérifier Ubuntu et root
if [ ! -f /etc/os-release ]; then
    echo "❌ Impossible de détecter le système d'exploitation"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    echo "❌ Ce script est conçu pour Ubuntu (détecté: $ID)"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "❌ Ce script doit être exécuté en tant que root (sudo)"
    exit 1
fi

# Installer curl si nécessaire
if ! command -v curl &> /dev/null; then
    echo "📦 Installation de curl..."
    apt update && apt install -y curl
fi

# Télécharger et exécuter l'installateur
echo "🚀 Téléchargement et exécution de l'installateur NTP Monitor Enterprise..."
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/quick_install_ubuntu24.sh | bash

echo "✅ Installation terminée !" 