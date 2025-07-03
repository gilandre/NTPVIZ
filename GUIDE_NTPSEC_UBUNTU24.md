# Guide NTP Monitor Enterprise avec ntpsec sur Ubuntu 24.04

## 🎯 **Objectif**

Ce guide corrige les problèmes liés à l'utilisation forcée de chrony dans les scripts précédents et restaure/préserve votre configuration **ntpsec** existante sur Ubuntu 24.04.

## 🚨 **Problème Identifié**

Les scripts précédents imposaient l'utilisation de **chrony** au lieu de **ntpsec**, ce qui :
- Bloquait les configurations ntpsec existantes
- Désactivait ntpsec en faveur de chrony
- Perdait les configurations personnalisées ntpsec
- Créait des conflits entre services de temps

## ✅ **Solutions Disponibles**

### **Solution 1 : Restauration Rapide (Configuration Bloquée)**

Si chrony a déjà bloqué votre configuration ntpsec :

```bash
# Télécharger et exécuter le script de restauration
chmod +x restore_ntpsec_config.sh
sudo ./restore_ntpsec_config.sh
```

**Ce que fait ce script :**
1. Arrête et désactive chrony
2. Arrête et désactive systemd-timesyncd
3. Restaure/active ntpsec
4. Met à jour la configuration de l'application
5. Redémarre les services concernés

### **Solution 2 : Déploiement Complet avec ntpsec**

Pour une nouvelle installation qui préserve ntpsec :

```bash
# Télécharger le script de déploiement ntpsec
chmod +x deploy_ubuntu24_ntpsec.sh
sudo ./deploy_ubuntu24_ntpsec.sh
```

**Avantages :**
- Sauvegarde automatique de la configuration ntpsec existante
- Installation complète avec ntpsec maintenu
- Configuration de l'application optimisée pour ntpsec
- Résolution du problème mod_wsgi incluse

## 🔧 **Configuration ntpsec**

### **Fichiers Importants**

```bash
# Configuration principale
/etc/ntpsec/ntp.conf

# Logs ntpsec
/var/log/ntpsec/ntp.log
/var/log/ntpsec/loopstats
/var/log/ntpsec/peerstats

# Sauvegarde (créée par le script)
/root/ntpsec_backup/YYYYMMDD_HHMMSS/
```

### **Configuration Type ntpsec**

```bash
# Exemple de configuration /etc/ntpsec/ntp.conf
# Serveurs NTP publics
pool 0.ubuntu.pool.ntp.org iburst
pool 1.ubuntu.pool.ntp.org iburst
pool 2.ubuntu.pool.ntp.org iburst
pool 3.ubuntu.pool.ntp.org iburst

# Serveurs NTP locaux/enterprise (à adapter)
server 192.168.1.10 iburst prefer
server 10.0.0.50 iburst

# Fichiers de configuration
driftfile /var/lib/ntpsec/ntp.drift
statsdir /var/log/ntpsec/
logfile /var/log/ntpsec/ntp.log

# Statistiques détaillées
statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable
filegen clockstats file clockstats type day enable

# Restrictions de sécurité
restrict default kod notrap nomodify nopeer noquery limited
restrict -6 default kod notrap nomodify nopeer noquery limited
restrict 127.0.0.1
restrict -6 ::1
restrict source notrap nomodify noquery

# Permettre les requêtes locales pour le monitoring
restrict 127.0.0.1 nomodify
restrict 192.168.0.0 mask 255.255.0.0 nomodify
restrict 10.0.0.0 mask 255.0.0.0 nomodify
```

## 🔄 **Gestion des Services**

### **Commandes ntpsec**

```bash
# Gestion du service
sudo systemctl status ntpsec
sudo systemctl start ntpsec
sudo systemctl stop ntpsec
sudo systemctl restart ntpsec
sudo systemctl enable ntpsec

# Monitoring en temps réel
sudo journalctl -u ntpsec -f

# Vérification synchronisation
ntpq -c peers
ntpq -c associations
ntpq -c sysinfo
```

### **Commandes de Diagnostic**

```bash
# État des services de temps
systemctl is-active ntpsec
systemctl is-active chronyd
systemctl is-active systemd-timesyncd

# Vérifier conflits
sudo ss -tulnp | grep :123

# Logs détaillés
tail -f /var/log/ntpsec/ntp.log
```

## 🧪 **Tests et Validation**

### **Test Fonctionnement ntpsec**

```bash
# Test basique
ntpq -c peers

# Sortie attendue (exemple):
#      remote           refid      st t when poll reach   delay   offset  jitter
# ==============================================================================
# *ntp.ubuntu.com  .GPS.            1 u   64   64  377    1.234   -0.123   0.456
# +time.google.com .GPS.            1 u   32   64  377    5.678    0.234   0.123
```

### **Test Application**

```bash
# Vérifier configuration application
grep -E "NTP_.*=" /home/ntp-monitor/ntp-monitor-enterprise/.env

# Sortie attendue:
# NTP_MONITORING_METHOD=ntpsec
# NTP_COMMAND=ntpq
# NTP_SERVICE=ntpsec
```

### **Test Interface Web**

1. Accédez à http://192.168.10.45
2. Connectez-vous (admin/admin123)
3. Vérifiez l'onglet "Monitoring NTP"
4. Confirmez que les données ntpsec s'affichent

## 📊 **Configuration Application**

### **Variables d'Environnement (.env)**

```bash
# Monitoring NTP avec ntpsec
NTP_MONITORING_METHOD=ntpsec
NTP_COMMAND=ntpq
NTP_SERVICE=ntpsec

# Serveurs surveillés
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.10,10.0.0.50
```

### **Monitoring Automatique**

L'application surveille automatiquement :
- État du service ntpsec
- Synchronisation des serveurs NTP
- Offset et jitter des connexions
- Alertes en cas de problème

## ⚠️ **Dépannage**

### **Problème : ntpsec ne démarre pas**

```bash
# Vérifier les conflits
sudo systemctl status ntpsec
sudo journalctl -u ntpsec -n 50

# Solutions courantes
sudo systemctl stop chronyd systemd-timesyncd
sudo systemctl disable chronyd systemd-timesyncd
sudo systemctl restart ntpsec
```

### **Problème : Pas de synchronisation**

```bash
# Vérifier configuration
sudo ntpq -c peers
sudo ntpq -c associations

# Vérifier firewall
sudo ufw status | grep 123
sudo ufw allow 123/udp

# Vérifier serveurs NTP
ping pool.ntp.org
ping time.google.com
```

### **Problème : Application ne voit pas ntpsec**

```bash
# Vérifier variables d'environnement
cd /home/ntp-monitor/ntp-monitor-enterprise
grep NTP_ .env

# Corriger si nécessaire
echo "NTP_MONITORING_METHOD=ntpsec" >> .env
echo "NTP_COMMAND=ntpq" >> .env
echo "NTP_SERVICE=ntpsec" >> .env

# Redémarrer application
sudo systemctl restart ntp-monitor-enterprise
```

## 🔒 **Sécurité ntpsec**

### **Restrictions Recommandées**

```bash
# Dans /etc/ntpsec/ntp.conf
# Bloquer accès externe non autorisé
restrict default kod notrap nomodify nopeer noquery limited

# Autoriser surveillance locale uniquement
restrict 127.0.0.1 nomodify
restrict 192.168.0.0 mask 255.255.0.0 nomodify
```

### **Firewall**

```bash
# Autoriser NTP uniquement sur réseaux internes
sudo ufw allow from 192.168.0.0/16 to any port 123
sudo ufw allow from 10.0.0.0/8 to any port 123
sudo ufw allow from 127.0.0.1 to any port 123
```

## 📈 **Monitoring et Logs**

### **Logs Importants**

```bash
# Logs système ntpsec
sudo journalctl -u ntpsec -f

# Logs ntpsec détaillés
tail -f /var/log/ntpsec/ntp.log

# Logs statistiques
tail -f /var/log/ntpsec/loopstats
tail -f /var/log/ntpsec/peerstats
```

### **Métriques à Surveiller**

- **Offset** : Différence de temps (doit être < 100ms)
- **Jitter** : Variation (doit être < 50ms)
- **Reach** : Accessibilité serveur (doit être 377)
- **Delay** : Latence réseau

## 🎉 **Avantages ntpsec vs chrony**

| Aspect | ntpsec | chrony |
|--------|--------|--------|
| **Sécurité** | ✅ Conçu pour la sécurité | ⚠️ Standard |
| **Compatibilité** | ✅ Compatible NTP classique | ⚠️ Syntaxe différente |
| **Monitoring** | ✅ ntpq standard | ⚠️ chronyc différent |
| **Enterprise** | ✅ Recommandé | ❌ Desktop |
| **Configuration** | ✅ Syntaxe connue | ⚠️ Nouvelle syntaxe |

## 📋 **Checklist Post-Installation**

- [ ] ntpsec actif : `systemctl is-active ntpsec`
- [ ] chrony inactif : `systemctl is-active chronyd` → inactif
- [ ] systemd-timesyncd inactif : `systemctl is-active systemd-timesyncd` → inactif
- [ ] ntpq fonctionne : `ntpq -c peers`
- [ ] Application configurée : `grep NTP_ /home/ntp-monitor/ntp-monitor-enterprise/.env`
- [ ] Interface web accessible : http://192.168.10.45
- [ ] Monitoring NTP visible dans l'interface

## 🚀 **Déploiement Rapide**

```bash
# Restauration ntpsec (si chrony active)
sudo ./restore_ntpsec_config.sh

# OU déploiement complet avec ntpsec
sudo ./deploy_ubuntu24_ntpsec.sh

# Vérification finale
ntpq -c peers
systemctl status ntpsec
curl http://192.168.10.45
```

## 📞 **Support**

En cas de problème :
1. Vérifiez les logs : `journalctl -u ntpsec -f`
2. Testez la configuration : `ntpq -c peers`
3. Redémarrez les services : `systemctl restart ntpsec ntp-monitor-enterprise`
4. Vérifiez l'interface web pour les données NTP

**Votre configuration ntpsec est maintenant préservée et optimisée !** 🎯 