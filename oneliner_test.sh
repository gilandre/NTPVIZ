#!/bin/bash
# One-liner ultra-compact pour test immédiat NTP Monitor Ubuntu 24.04
# Usage: bash <(curl -fsSL URL_DE_CE_SCRIPT)

echo "🚀 Test NTP Monitor Ubuntu 24.04" && \
[[ $EUID -eq 0 ]] || { echo "❌ Utilisez sudo"; exit 1; } && \
source /etc/os-release && [[ "$ID" == "ubuntu" ]] || { echo "❌ Non Ubuntu"; exit 1; } && \
echo "✅ Ubuntu $VERSION_ID" && \
echo "📦 Installation..." && \
apt update >/dev/null 2>&1 && \
apt install -y curl git python3 python3-pip mysql-server apache2 redis-server ntp >/dev/null 2>&1 && \
echo "⚙️ Configuration..." && \
systemctl start mysql apache2 redis-server ntp >/dev/null 2>&1 && \
systemctl enable mysql apache2 redis-server ntp >/dev/null 2>&1 && \
a2enmod wsgi >/dev/null 2>&1 && \
python3 -m pip install --quiet flask sqlalchemy pymysql redis >/dev/null 2>&1 && \
echo "🔍 Tests..." && \
for s in mysql apache2 redis-server ntp; do systemctl is-active --quiet "$s" && echo "✅ $s" || echo "❌ $s"; done && \
python3 -c "import flask,sqlalchemy,pymysql,redis; print('✅ Python OK')" 2>/dev/null || echo "❌ Python KO" && \
mysql -u root -e "SELECT 'MySQL OK';" >/dev/null 2>&1 && echo "✅ MySQL OK" || echo "❌ MySQL KO" && \
echo "🎉 Installation terminée ! Serveur prêt pour NTP Monitor Enterprise" && \
echo "📋 Prochaines étapes:" && \
echo "   git clone https://github.com/gilandre/NTPVIZ.git" && \
echo "   cd NTPVIZ && sudo ./deploy_ubuntu_production.sh" 