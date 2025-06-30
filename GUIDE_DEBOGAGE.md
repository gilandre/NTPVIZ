# 🔧 GUIDE DE DÉBOGAGE - EmaraudeNTP VIZ

## 📋 PROBLÈMES IDENTIFIÉS ET SOLUTIONS

### 1. 🔒 BASE DE DONNÉES VERROUILLÉE

**Symptôme** : Erreur `database is locked` lors de la connexion

**Cause** : Fichier journal SQLite `instance/ntp_monitor_dev.db-journal`

**Solutions** :

#### Option 1 - Redémarrage propre (RECOMMANDÉ)
```bash
1. Arrêter l'application : Ctrl+C dans le terminal
2. Supprimer le journal : rm instance/ntp_monitor_dev.db-journal
3. Redémarrer : python app.py
```

#### Option 2 - Suppression directe (DANGER)
```bash
# ⚠️ ATTENTION : Uniquement si l'application est arrêtée
Remove-Item "instance/ntp_monitor_dev.db-journal" -Force
```

### 2. 🎯 CORRECTION DES PRIORITÉS NTP

**Problème** : Serveur INVESTECH-01 pas en priorité 1

**Solution** : Après avoir débloqué la BD
```bash
python fix_ntp_priorities_api.py
```

**Priorités correctes** :
- Priorité 1 👑 : SRV-NTP-BDT.INVESTECH-01 (192.168.10.45)
- Priorité 2 : SRV-NTP-BDT.INVESTECH-02 (192.168.10.28)
- Priorité 3-6 : Pools NTP

### 3. ✅ CORRECTIONS DÉJÀ APPLIQUÉES

- ✅ Erreur 404 `emeraude-enhancements.js` → CORRIGÉE
- ✅ Erreur WinError 2 service monitoring → CORRIGÉE
- ✅ Templates d'erreur créés (404, 500, 403) → CRÉÉS
- ✅ Branding "EmaraudeNTP VIZ" → CORRIGÉ
- ✅ Page login épurée → CORRIGÉE
- ✅ Gestionnaire d'alertes JavaScript → CORRIGÉ

### 4. 🔧 PROCÉDURE COMPLÈTE DE CORRECTION

```bash
# 1. Arrêter l'application
Ctrl+C

# 2. Débloquer la base de données
Remove-Item "instance/ntp_monitor_dev.db-journal" -Force

# 3. Corriger les priorités
python fix_ntp_priorities_api.py

# 4. Redémarrer l'application
python app.py

# 5. Tester la connexion
# Navigateur : http://127.0.0.1:5000
# Credentials : admin / admin123
```

### 5. 📊 VÉRIFICATIONS POST-CORRECTION

- [ ] Connexion admin/admin123 fonctionne
- [ ] Serveur INVESTECH-01 en priorité 1 👑
- [ ] Interface visuelle correcte
- [ ] Aucune erreur JavaScript console
- [ ] Branding "EmaraudeNTP VIZ" affiché

### 6. 🚨 EN CAS DE PROBLÈME

**Si la BD reste verrouillée** :
1. Vérifier qu'aucun processus python ne tourne
2. Redémarrer la machine si nécessaire
3. Restaurer depuis `ntp_monitor_prod.db` si corruption

**Si les priorités ne se corrigent pas** :
1. Vérifier que le script trouve la bonne BD
2. Exécuter avec l'application arrêtée
3. Vérifier les logs pour d'autres erreurs

---

## 📞 RÉSUMÉ ÉTAT ACTUEL

✅ **FONCTIONNEL** : Application sur port 5000  
❌ **BLOQUÉ** : Connexion (BD verrouillée)  
⏳ **À FAIRE** : Priorités NTP incorrectes  

**Action suivante** : Débloquer la BD → Corriger priorités → Redémarrer 