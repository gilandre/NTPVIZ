# 🎨 PLAN DASHBOARD MULTI-PROFILS - NTP Monitor Enterprise

## 📋 VUE D'ENSEMBLE

**OBJECTIF :** Créer 3 interfaces dashboard adaptées aux rôles utilisateur
**INFRASTRUCTURE :** ✅ Système de rôles déjà fonctionnel
**APPROCHE :** Dashboards conditionnels basés sur les permissions

---

## 🎯 SPÉCIFICATIONS PAR PROFIL

### 👑 **ADMIN** (Dashboard actuel - Interface complète)
```
✅ Accès total : Configuration, gestion serveurs, alertes
✅ Contrôles avancés : Ajout/suppression serveurs, paramètres système  
✅ Monitoring complet : Tous graphiques, statistiques détaillées
✅ Administration : Gestion utilisateurs, export/import
✅ Interface : dashboard-admin.html (actuelle)
```

### 👀 **VIEWER** (Interface simplifiée - Lecture seule)
```
✅ INCLUS:
- Horloges serveurs NTP (sans boutons configuration)
- Graphique écarts synchronisation (lecture seule)
- Statut système local (informations uniquement)
- Alertes (visualisation seulement)
- Menu simplifié (pas d'administration)

❌ EXCLU:
- Boutons configuration/administration
- Gestion serveurs NTP
- Création/modification alertes
- Paramètres système
- Export de données
```

### ⚙️ **OPERATOR** (Interface intermédiaire - Opérations)
```
✅ INCLUS:
- Tout du VIEWER +
- Actions serveurs : Test connectivité, forcer synchronisation
- Gestion alertes : Acquittement, création basique
- Statistiques avancées : Logs détaillés, métriques
- Monitoring clients : Connexions actives, statistiques

❌ EXCLU:
- Ajout/suppression serveurs NTP
- Gestion utilisateurs
- Configuration système critique
- Paramètres de sécurité
```

---

## 🏗️ ARCHITECTURE TECHNIQUE

### **APPROCHE 1 : Templates Conditionnels (RECOMMANDÉE)**
```
Structure fichiers :
- frontend/templates/dashboard.html → Logique conditionnelle
- frontend/static/js/dashboard-common.js → Fonctions partagées
- frontend/static/js/role-permissions.js → Gestion permissions
- frontend/static/css/role-styles.css → Styles adaptés

Avantages :
✅ Maintenance simplifiée (1 seul template)
✅ Utilise l'infrastructure existante
✅ Déploiement rapide
✅ Cohérence visuelle garantie
```

### **APPROCHE 2 : Templates Séparés (Alternative)**
```
Structure fichiers :
- frontend/templates/dashboard-admin.html → Interface complète
- frontend/templates/dashboard-operator.html → Interface intermédiaire  
- frontend/templates/dashboard-viewer.html → Interface simplifiée

Avantages :
✅ Séparation claire des fonctionnalités
✅ Personnalisation complète par rôle
✅ Performance optimisée

Inconvénients :
❌ Maintenance complexe (3 templates)
❌ Risque de divergence des interfaces
❌ Plus de développement initial
```

---

## 🚀 PLAN D'IMPLÉMENTATION (Phase 1 - APPROCHE 1)

### **ÉTAPE 1 : Modification Template Principal**
```html
<!-- dashboard.html - Ajout logique conditionnelle -->
{% if current_user.is_admin %}
    <!-- Section administration complète -->
{% elif current_user.can_configure %}
    <!-- Section opérateur (actions limitees) -->
{% else %}
    <!-- Section viewer (lecture seule) -->
{% endif %}
```

### **ÉTAPE 2 : JavaScript Conditionnel**
```javascript
// dashboard.js - Ajout gestion permissions
async function initDashboard() {
    const permissions = await loadUserPermissions();
    
    if (permissions.is_admin) {
        initAdminFeatures();
    } else if (permissions.can_configure) {
        initOperatorFeatures();
    } else {
        initViewerFeatures();
    }
}
```

### **ÉTAPE 3 : Styles Adaptatifs**
```css
/* role-styles.css - Masquage conditionnel */
.admin-only { display: none; }
.operator-only { display: none; }
.viewer-only { display: block; }

[data-role="admin"] .admin-only { display: block; }
[data-role="operator"] .operator-only { display: block; }
```

### **ÉTAPE 4 : API Protection Renforcée**
```python
# Ajout vérifications rôles sur endpoints sensibles
@admin_required  # Serveurs, utilisateurs, config système
@config_required # Tests, alertes, statistiques
# Pas de restriction pour lecture seule
```

---

## 📊 FONCTIONNALITÉS PAR INTERFACE

### **TABLEAU COMPARATIF**
| Fonctionnalité | Admin | Operator | Viewer |
|---|---|---|---|
| Horloges serveurs | ✅ Complet | ✅ Monitoring | ✅ Affichage |
| Graphique écarts | ✅ + Config | ✅ Monitoring | ✅ Affichage |  
| Gestion serveurs | ✅ CRUD | ❌ Lecture | ❌ Lecture |
| Gestion alertes | ✅ CRUD | ✅ Acquit | ✅ Lecture |
| Administration | ✅ Complet | ❌ Non | ❌ Non |
| Tests connectivité | ✅ Oui | ✅ Oui | ❌ Non |
| Export données | ✅ Oui | ✅ Logs | ❌ Non |
| Configuration | ✅ Système | ✅ Moniteur | ❌ Non |

---

## 🎨 WIREFRAMES INTERFACES

### **VIEWER Dashboard (Simplifié)**
```
┌─────────────────────────────────────┐
│ 🏠 NTP Monitor - [User] Viewer      │
├─────────────────────────────────────┤
│ 📊 Résumé: 6 Serveurs │ ⚡ 2 Alertes │
├─────────────────────────────────────┤
│ ⏲️  HORLOGES SERVEURS (lecture)      │  
│ [Pool 0] [Pool 1] [Pool 2] [Pool 3] │
│ [BDT-01] [BDT-02]                   │
├─────────────────────────────────────┤
│ 📈 GRAPHIQUE ÉCARTS (affichage)     │
│ [Graphique ligne 24h glissantes]    │
├─────────────────────────────────────┤
│ 🖥️  SYSTÈME LOCAL (infos)           │
│ Timezone | UTC | Heure locale       │
└─────────────────────────────────────┘
```

### **OPERATOR Dashboard (Intermédiaire)**
```
┌─────────────────────────────────────┐
│ 🏠 NTP Monitor - [User] Operator    │
├─────────────────────────────────────┤
│ 📊 Résumé + [🔄 Refresh] [📊 Stats] │
├─────────────────────────────────────┤
│ ⏲️  HORLOGES + [🧪 Test] [🔄 Sync]   │
├─────────────────────────────────────┤
│ 📈 GRAPHIQUE + [⚙️ Interval]        │
├─────────────────────────────────────┤
│ ⚠️  ALERTES + [✅ Acquit] [➕ New]   │
└─────────────────────────────────────┘
```

---

## ⏱️ PLANNING DE DÉVELOPPEMENT

### **PHASE 1 : Base (2-3 heures)**
- ✅ Ajout logique conditionnelle dashboard.html
- ✅ Modification dashboard.js pour permissions
- ✅ Création role-styles.css
- ✅ Test avec 3 comptes existants

### **PHASE 2 : Finitions (1-2 heures)**  
- ✅ Ajustements UX par rôle
- ✅ Messages d'information contextuels
- ✅ Documentation utilisateur
- ✅ Tests complets

### **PHASE 3 : Améliorations futures**
- Templates séparés si besoin
- Personnalisation avancée par rôle
- Dashboards mobiles adaptés

---

## 🧪 TESTS PRÉVUS

### **COMPTES DE TEST**
```
Admin: admin/admin123 → Interface complète
Operator: operator/operator123 → Interface intermédiaire  
Viewer: viewer/viewer123 → Interface simplifiée
```

### **SCÉNARIOS DE TEST**
1. **Navigation** : Accès aux bonnes sections par rôle
2. **Actions** : Boutons/formulaires selon permissions
3. **API** : Endpoints protégés correctement
4. **Affichage** : Éléments masqués/visibles appropriés

---

## 📝 NOTES D'IMPLÉMENTATION

### **POINTS D'ATTENTION**
- ✅ Utiliser `current_user.is_admin` et `current_user.can_configure`
- ✅ Protéger côté client ET serveur
- ✅ Messages utilisateur contextuel selon rôle
- ✅ Maintenir cohérence visuelle

### **ÉVOLUTIONS FUTURES**
- Dashboard mobile adaptatif
- Notifications push par rôle
- Rapports personnalisés
- Widgets configurables par utilisateur

---

**STATUS :** 📋 Plan prêt pour implémentation
**PROCHAINE ÉTAPE :** Démarrer Phase 1 - Modification template principal 