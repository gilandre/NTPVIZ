# 📡 Guide du Monitoring des Clients NTP

## 🎯 Vue d'ensemble

Le système de monitoring des clients NTP permet de surveiller en temps réel les clients qui se connectent aux serveurs NTP locaux. Cette fonctionnalité est essentielle pour :

- **Surveiller l'utilisation** des serveurs NTP locaux 
- **Identifier les clients problématiques** ou les connexions suspectes
- **Analyser les patterns d'utilisation** sur 24h
- **Détecter les anomalies** de connexion
- **Optimiser la performance** des serveurs

## 🏗️ Architecture Technique

### Backend (Services & APIs)

#### Service Principal : `ClientMonitorService`
```python
# Localisation: backend/services/client_monitor_service.py

Méthodes principales:
├── get_active_connections()      # Connexions UDP actives sur port 123
├── get_ntp_statistics()         # Stats du service NTP via ntpq
├── get_client_statistics()      # Historique clients (24h)
├── get_connection_stats()       # Stats pour dashboard
├── get_service_status()         # Status service NTP
└── get_ntpq_peers()            # Peers NTP via ntpq -p
```

#### APIs REST Disponibles
```bash
# Status du service NTP local
GET /api/ntp/service/status
Response: {
    "service_status": "active|inactive|error",
    "port_listening": true|false,
    "port": 123,
    "timestamp": "2025-01-XX..."
}

# Connexions actives
GET /api/ntp/clients/connections  
Response: [
    {
        "client_ip": "192.168.1.100",
        "client_port": 45123,
        "server_ip": "192.168.10.28", 
        "server_port": 123,
        "status": "ESTABLISHED",
        "timestamp": "2025-01-XX..."
    }
]

# Statistiques des clients
GET /api/ntp/clients/statistics?hours=24
Response: {
    "total_connections": 150,
    "unique_clients": 12,
    "average_connections_per_client": 12.5,
    "top_clients": [
        {"ip": "192.168.1.100", "connections": 45}
    ],
    "hourly_connections": {...}
}
```

### Frontend (Interface & JavaScript)

#### Module JavaScript : `ClientMonitor`
```javascript
// Localisation: frontend/static/js/modules/client-monitor.js

Fonctionnalités:
├── Monitoring temps réel (30s intervals)
├── WebSocket pour mises à jour instantanées
├── Cache des données pour performance
├── Gestion d'erreurs robuste
└── API simple pour interaction
```

#### Interface Dashboard
```html
<!-- Section dans dashboard.html -->
Éléments d'interface:
├── Status du service NTP local
├── Connexions actives (nombre + détails)
├── Statistiques 24h (totales, uniques, moyenne)
├── Top clients les plus actifs
├── Boutons d'action (Détails, Pause, Export)
└── Modal de détails complet
```

## 🚀 Utilisation Pratique

### Démarrage Automatique

Le monitoring démarre automatiquement au chargement de la page :

```javascript
// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.clientMonitor.start();
});
```

### Contrôles Manuels

```javascript
// Forcer une mise à jour
window.clientMonitor.forceUpdate();

// Arrêter/Reprendre le monitoring
window.clientMonitor.stop();
window.clientMonitor.start();

// Vérifier l'état
window.clientMonitor.isMonitoringActive();

// Accéder aux données
window.clientMonitor.getCurrentData();
```

### Interface Utilisateur

#### Dashboard Principal
1. **Section "Monitoring Clients NTP"** - Vue d'ensemble temps réel
2. **Status Service** - État du service NTP local (actif/inactif)
3. **Connexions Actives** - Nombre et liste des clients connectés
4. **Statistiques 24h** - Métriques d'utilisation historiques

#### Modal de Détails
- **Bouton "Détails"** → Ouvre un modal complet avec :
  - Status détaillé du service
  - Table des connexions actives
  - Statistiques avancées
  - Top 10 des clients
  - Métriques de performance

#### Contrôles
- **Bouton Actualiser** ⟲ - Mise à jour manuelle immédiate
- **Bouton Pause** ⏸️ - Suspendre/reprendre le monitoring
- **Bouton Détails** ℹ️ - Affichage modal détaillé

## 📊 Données Monitorées

### Connexions UDP Actives
```python
# Via psutil.net_connections(kind='udp')
{
    'client_ip': '192.168.1.100',      # IP du client
    'client_port': 45123,              # Port source client
    'server_ip': '192.168.10.28',      # IP serveur local
    'server_port': 123,                # Port NTP (123)
    'status': 'ESTABLISHED',           # État connexion
    'pid': 1234,                       # Process ID
    'timestamp': '2025-01-XX...'       # Horodatage
}
```

### Service NTP Local
```python
# Via systemctl et ntpq
{
    'service_status': 'active',        # État systemctl
    'port_listening': true,            # Port 123 ouvert
    'stratum': 2,                      # Niveau NTP
    'precision': -20,                  # Précision
    'rootdelay': 0.050,               # Délai racine
    'peer': '1.pool.ntp.org',         # Serveur référence
    'uptime': 86400                    # Temps de fonctionnement
}
```

### Statistiques Historiques
```python
# Calculs sur période (défaut: 24h)
{
    'total_connections': 150,          # Total connexions
    'unique_clients': 12,              # Clients uniques
    'average_connections_per_client': 12.5,  # Moyenne
    'top_clients': [...],              # Top 10 clients
    'hourly_connections': {...}        # Répartition horaire
}
```

## 🔧 Configuration Avancée

### Ajustement des Intervalles
```javascript
// Modifier l'intervalle de mise à jour (défaut: 30s)
window.clientMonitor.config.updateInterval = 60000; // 1 minute

// Redémarrer avec nouveau paramètre
window.clientMonitor.stop();
window.clientMonitor.start();
```

### WebSocket Temps Réel
```python
# Activation côté serveur (websocket.py)
socket.emit('subscribe', {
    'type': 'client_monitoring',
    'interval': 30  # secondes
});

# Réception des mises à jour
socket.on('client_monitoring_update', (data) => {
    // data.connections - connexions actives
    // data.client_stats - statistiques
    // data.service_status - état service
});
```

### Personnalisation de l'Affichage
```javascript
// Modifier le nombre max de clients affichés
const maxClients = 10;
const sortedClients = Object.entries(clientGroups)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, maxClients);
```

## 🎯 Cas d'Usage Pratiques

### 1. Surveillance Réseau d'Entreprise
```bash
Objectif: Monitorer l'utilisation des serveurs NTP internes
- SRV-NTP-01 (192.168.10.28) - Site principal  
- SRV-NTP-02 (192.168.10.45) - Site secondaire

Métriques clés:
✓ Nombre de clients par serveur
✓ Répartition géographique (par IP)
✓ Pics d'utilisation horaires
✓ Clients les plus actifs
```

### 2. Détection d'Anomalies
```bash
Alertes automatiques sur:
⚠️ Pic anormal de connexions (> 100 simultanées)
⚠️ Nouveau client inconnu (IP hors réseau)
⚠️ Service NTP inactif ou port fermé
⚠️ Échec répétés de synchronisation
```

### 3. Optimisation Performance
```bash
Analyses disponibles:
📈 Courbe de charge sur 24h
📊 Répartition par client/serveur
🔍 Identification des clients gourmands
⚡ Temps de réponse par connexion
```

### 4. Audit et Conformité
```bash
Traçabilité complète:
📝 Logs horodatés de toutes les connexions
📋 Historique des accès par IP
📄 Export des données pour audit
🔒 Monitoring des accès non autorisés
```

## 🛠️ Dépannage

### Service NTP Non Actif
```bash
# Vérifier le service
systemctl status ntpsec
systemctl status ntp

# Redémarrer si nécessaire
sudo systemctl restart ntpsec

# Vérifier le port d'écoute
netstat -ulnp | grep :123
```

### Pas de Connexions Visibles
```bash
# Vérifier les permissions
sudo netstat -ulnp | grep :123

# Tester une connexion NTP
ntpdate -q 192.168.10.28

# Vérifier le firewall
sudo ufw status | grep 123
```

### Erreurs JavaScript
```bash
# Console développeur (F12)
1. Vérifier que client-monitor.js est chargé
2. Contrôler window.clientMonitor existe
3. Tester manuellement: window.clientMonitor.forceUpdate()
4. Vérifier les erreurs réseau dans l'onglet Network
```

### Performance Lente
```bash
# Réduire l'intervalle de polling
window.clientMonitor.config.updateInterval = 60000; // 1 min

# Limiter l'historique
GET /api/ntp/clients/statistics?hours=1  // 1h au lieu de 24h

# Désactiver WebSocket si problématique
// Commentaire dans connectWebSocket()
```

## 📈 Métriques de Performance

### Benchmarks Typiques
```bash
Environnement standard (50 clients):
├── Mise à jour dashboard: < 500ms
├── Chargement modal détails: < 1s  
├── Connexions simultanées: 20-30 actives
├── Mémoire JavaScript: ~2MB
└── Trafic réseau: ~10KB/mise à jour
```

### Limites Recommandées
```bash
Configuration recommandée:
├── Max clients simultanés: < 100
├── Interval monitoring: ≥ 30s
├── Historique: ≤ 24h
├── Top clients affichés: ≤ 10
└── Données WebSocket: < 1KB/update
```

---

## 🎉 Conclusion

Le système de monitoring des clients NTP offre une **visibilité complète** sur l'utilisation des serveurs NTP locaux. Avec son interface temps réel, ses métriques détaillées et sa robustesse technique, il constitue un outil professionnel indispensable pour la **surveillance de l'infrastructure NTP** d'entreprise.

**Intégration parfaite** avec NTP Monitor Enterprise pour une solution de monitoring complète ! 🌐 