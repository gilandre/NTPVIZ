/**
 * NTP Monitor Enterprise - Alertes Temps Réel
 * Module d'extension pour les alertes temps réel via WebSocket
 */

/**
 * Gestionnaire de nouvelle alerte temps réel
 */
function handleNewAlert(data) {
    console.log('🚨 Nouvelle alerte reçue:', data);
    
    const alert = data.alert;
    
    // Notification visuelle immédiate
    if (typeof showNotification === 'function') {
        const alertType = alert.severity === 'critical' ? 'danger' : 
                         alert.severity === 'warning' ? 'warning' : 'info';
        showNotification(`🚨 ${alert.title}`, alertType, 8000);
    }
    
    // Mettre à jour immédiatement tous les compteurs
    refreshAllAlertsCounters();
    
    // Déclencher une mise à jour de l'interface
    if (typeof updateAlertsWidget === 'function') {
        loadAlertsData().then(alertData => {
            if (alertData) {
                updateAlertsWidget(alertData);
            }
        });
    }
}

/**
 * Gestionnaire de mise à jour des alertes
 */
function handleAlertsUpdate(data) {
    console.log('📊 Mise à jour alertes reçue:', data);
    
    if (typeof updateAlertsWidget === 'function') {
        updateAlertsWidget(data);
    }
    
    // Synchroniser le gestionnaire d'alertes
    if (window.alertManager) {
        window.alertManager.refreshAlerts();
    }
}

/**
 * Gestionnaire d'acquittement d'alerte
 */
function handleAlertAcknowledged(data) {
    console.log('✅ Alerte acquittée:', data);
    
    // Actualiser les compteurs
    refreshAllAlertsCounters();
    
    // Notification
    if (typeof showNotification === 'function') {
        showNotification('Alerte acquittée', 'success', 3000);
    }
}

/**
 * Gestionnaire de résolution d'alerte
 */
function handleAlertResolved(data) {
    console.log('✅ Alerte résolue:', data);
    
    // Actualiser les compteurs
    refreshAllAlertsCounters();
    
    // Notification
    if (typeof showNotification === 'function') {
        showNotification('Alerte résolue automatiquement', 'success', 3000);
    }
}

/**
 * Gestionnaire de mise à jour générale du dashboard
 */
function handleDashboardUpdate(data) {
    console.log('📊 Mise à jour dashboard reçue:', data);
    
    // Mettre à jour les alertes récentes si présentes
    if (data.recent_alerts && typeof updateAlertsWidget === 'function') {
        const alertData = {
            total_active: data.recent_alerts.filter(a => a.status === 'active').length,
            critical: data.recent_alerts.filter(a => a.severity === 'critical' && a.status === 'active').length,
            warning: data.recent_alerts.filter(a => a.severity === 'warning' && a.status === 'active').length,
            recent: data.recent_alerts
        };
        updateAlertsWidget(alertData);
    }
}

/**
 * 🔧 FONCTION PRINCIPALE: Actualiser tous les compteurs d'alertes simultanément
 */
function refreshAllAlertsCounters() {
    console.log('🔄 Actualisation des compteurs d\'alertes...');
    
    loadAlertsData().then(alertData => {
        if (alertData) {
            const alertsCount = alertData.total_active || 0;
            
            // Liste de tous les compteurs à synchroniser
            const counters = [
                { selector: '#alerts-count', value: alertsCount },
                { selector: '#active-alerts-count', value: alertsCount },
                { selector: '.alerts-count-badge', value: alertsCount }
            ];
            
            // Mettre à jour tous les compteurs simultanément
            counters.forEach(counter => {
                const elements = document.querySelectorAll(counter.selector);
                elements.forEach(element => {
                    if (element) {
                        element.textContent = counter.value;
                        
                        // Appliquer le style approprié pour les badges
                        if (element.classList.contains('badge')) {
                            // Retirer les anciens styles
                            element.classList.remove('bg-danger', 'bg-secondary');
                            // Ajouter le nouveau style
                            element.classList.add(counter.value > 0 ? 'bg-danger' : 'bg-secondary');
                        }
                    }
                });
            });
            
            console.log('✅ Compteurs d\'alertes actualisés:', {
                total: alertsCount,
                critical: alertData.critical || 0,
                warning: alertData.warning || 0
            });
        }
    }).catch(error => {
        console.error('❌ Erreur actualisation compteurs:', error);
    });
}

/**
 * Fonction utilitaire pour charger les données d'alertes depuis l'API
 */
async function loadAlertsData() {
    try {
        const response = await fetch('/api/alerts/summary');
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error('Erreur chargement données alertes:', error);
    }
    return null;
}

/**
 * Initialiser le système d'alertes temps réel
 */
function initAlertsRealtime() {
    console.log('🚀 Initialisation des alertes temps réel...');
    
    // Vérifier si WebSocket est disponible
    if (typeof subscribeToEvent === 'function') {
        // S'abonner aux événements d'alertes
        subscribeToEvent('new_alert', handleNewAlert);
        subscribeToEvent('alerts_update', handleAlertsUpdate);
        subscribeToEvent('alert_acknowledged', handleAlertAcknowledged);
        subscribeToEvent('alert_resolved', handleAlertResolved);
        subscribeToEvent('dashboard_update', handleDashboardUpdate);
        
        console.log('✅ Abonnements aux événements d\'alertes configurés');
    } else {
        console.warn('⚠️ WebSocket non disponible - Mode dégradé');
        
        // Mode dégradé : actualisation périodique
        setInterval(refreshAllAlertsCounters, 10000); // Toutes les 10 secondes
    }
    
    // Actualisation initiale
    refreshAllAlertsCounters();
}

/**
 * Fonction pour tester le système d'alertes
 */
function testAlertSystem() {
    console.log('🧪 Test du système d\'alertes...');
    
    // Simuler une nouvelle alerte
    const testAlert = {
        alert: {
            id: Date.now(),
            title: 'Test d\'alerte',
            message: 'Ceci est un test du système d\'alertes temps réel',
            severity: 'warning',
            status: 'active',
            created_at: new Date().toISOString()
        }
    };
    
    handleNewAlert(testAlert);
}

// Exporter les fonctions pour usage global
window.handleNewAlert = handleNewAlert;
window.handleAlertsUpdate = handleAlertsUpdate;
window.handleAlertAcknowledged = handleAlertAcknowledged;
window.handleAlertResolved = handleAlertResolved;
window.handleDashboardUpdate = handleDashboardUpdate;
window.refreshAllAlertsCounters = refreshAllAlertsCounters;
window.initAlertsRealtime = initAlertsRealtime;
window.testAlertSystem = testAlertSystem;

// Auto-initialisation si le DOM est prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAlertsRealtime);
} else {
    initAlertsRealtime();
} 