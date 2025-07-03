# Commandes de Test pour Serveur Ubuntu 24.04

## 🚀 Option 1 : One-liner ultra-rapide

Copiez-collez cette commande directement sur votre serveur Ubuntu :

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/dependencies_checker_ubuntu24_simple.sh | sudo bash
```

## 🛠️ Option 2 : Script de test local

1. **Créer le script sur le serveur Ubuntu :**

```bash
sudo nano test_ntp.sh
```

2. **Copiez-collez ce contenu :**

```bash
#!/bin/bash
# Test NTP Monitor Enterprise Ubuntu 24.04
echo "=== TEST NTP MONITOR UBUNTU 24.04 ==="

# Vérifications
if [[ $EUID -ne 0 ]]; then echo "❌ Exécutez avec sudo"; exit 1; fi
source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then echo "❌ Non Ubuntu: $ID"; exit 1; fi
echo "✅ Ubuntu $VERSION_ID détecté"

# Installation rapide
echo "📦 Installation packages..."
apt update && apt install -y curl wget git python3 python3-pip mysql-server apache2 redis-server ntp

# Configuration services
echo "⚙️ Configuration services..."
systemctl start mysql apache2 redis-server ntp
systemctl enable mysql apache2 redis-server ntp
a2enmod wsgi

# Test MySQL
echo "🗄️ Test MySQL..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_test; SELECT 'MySQL OK' as status;"

# Test Python
echo "🐍 Test Python..."
python3 -m pip install --quiet flask sqlalchemy pymysql redis
python3 -c "import flask, sqlalchemy, pymysql, redis; print('✅ Python OK')"

# Tests services
echo "🔍 Test des services..."
for service in mysql apache2 redis-server ntp; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service actif"
    else
        echo "❌ $service inactif"
    fi
done

echo "🎉 Test terminé ! Prêt pour NTP Monitor Enterprise"
```

3. **Exécuter le script :**

```bash
chmod +x test_ntp.sh
sudo ./test_ntp.sh
```

## ⚡ Option 3 : Commandes manuelles étape par étape

Si vous préférez exécuter les commandes une par une :

```bash
# 1. Vérification système
sudo apt update
lsb_release -a

# 2. Installation packages
sudo apt install -y curl wget git python3 python3-pip python3-venv mysql-server apache2 redis-server ntp

# 3. Démarrage services
sudo systemctl start mysql apache2 redis-server ntp
sudo systemctl enable mysql apache2 redis-server ntp

# 4. Configuration Apache
sudo a2enmod wsgi rewrite ssl

# 5. Test Python
python3 -m pip install flask sqlalchemy pymysql redis python-dotenv
python3 -c "import flask, sqlalchemy, pymysql, redis; print('Python OK')"

# 6. Vérification services
sudo systemctl status mysql apache2 redis-server ntp
```

## 🔍 Commandes de diagnostic

Si quelque chose ne fonctionne pas :

```bash
# Vérifier les logs
sudo journalctl -xe

# Vérifier les services
sudo systemctl --failed

# Vérifier l'espace disque
df -h

# Vérifier la RAM
free -h

# Vérifier les ports
sudo netstat -tulpn | grep -E ':80|:443|:3306|:6379'
```

## ✅ Validation finale

Après l'installation, vérifiez que tout fonctionne :

```bash
# Test MySQL
sudo mysql -u root -e "SHOW DATABASES;"

# Test Apache
curl -I http://localhost

# Test Redis
redis-cli ping

# Test NTP
ntpq -p
```

## 🎯 Prochaines étapes

Une fois que tout fonctionne :

```bash
# Cloner le projet
git clone https://github.com/gilandre/NTPVIZ.git

# Déployer l'application
cd NTPVIZ
sudo ./deploy_ubuntu_production.sh
```

---

**Note :** Ces commandes sont optimisées pour Ubuntu 24.04 et installent automatiquement tous les prérequis pour NTP Monitor Enterprise. 