#!/bin/bash

# Script de téléchargement et d'installation NTPVIZ
# À exécuter sur le serveur Ubuntu

echo "🚀 TÉLÉCHARGEMENT ET INSTALLATION NTPVIZ"
echo "========================================="

# Variables
GITHUB_RAW="https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev"
INSTALL_SCRIPT="install_ntpviz_server.sh"

# Téléchargement du script d'installation
echo "📥 Téléchargement du script d'installation..."
wget -O $INSTALL_SCRIPT $GITHUB_RAW/$INSTALL_SCRIPT

# Rendre le script exécutable
chmod +x $INSTALL_SCRIPT

# Exécution du script d'installation
echo "🔧 Exécution du script d'installation..."
./$INSTALL_SCRIPT

echo "✅ Installation terminée!" 