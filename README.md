# 🚀 NTP Monitor Enterprise

Application web complète pour le monitoring en temps réel des serveurs NTP.

## ✅ Fonctionnalités

- **Modal d'administration complet** : Gestion utilisateurs, serveurs, statistiques
- **Monitoring NTP temps réel** : Offset, latence, stratum, disponibilité
- **Alertes intelligentes** : Seuils configurables par type de serveur
- **Interface responsive** : Compatible desktop et mobile
- **Système de rôles** : Admin, Operator, Viewer

## 🛠️ Installation

```bash
# Cloner le projet
git clone https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp env.example .env

# Initialiser la base de données
python initialiser_database.py

# Démarrer l'application
python app.py
```

## 👥 Utilisateurs par défaut

- **Administrateur** : `admin` / `admin123`
- **Opérateur** : `operator` / `operator123`
- **Lecteur** : `viewer` / `viewer123`

⚠️ **Important** : Changez les mots de passe après la première connexion !

## 🌐 Accès

- **URL** : http://localhost:5001
- **Interface d'administration** : http://localhost:5001 (admin/admin123)

## 📚 Documentation

- [Guide de déploiement](DEPLOY.md)
- [Installation rapide](INSTALLATION_RAPIDE.md)
- [Dépannage](TROUBLESHOOTING.md)

## 🏆 État du projet

✅ **Application fonctionnelle** : Démarrage stable
✅ **Modal d'administration** : Complètement opérationnel
✅ **Monitoring NTP** : Temps réel actif
✅ **Prêt pour la production** : Ubuntu 24.04 compatible

---

**NTP Monitor Enterprise** - Monitoring NTP professionnel en temps réel 🚀 