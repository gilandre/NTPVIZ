/**
 * Gestionnaire d'alertes optimisé pour NTPVIZ
 * Gère l'affichage cohérent des alertes dans l'interface
 */

class OptimizedAlertManager {
    constructor() {
        this.cache = {
            summary: null,
            active: null,
            lastUpdate: 0,
            cacheDuration: 5000 // 5 secondes
        };
        
        this.updateInterval = null;
        this.isInitialized = false;
        
        console.log('🚀 Gestionnaire d\'alertes optimisé initialisé');
    }
    
    // Initialiser le gestionnaire
    init() {
        if (this.isInitialized) {
            console.log('⚠️ Gestionnaire déjà initialisé');
            return;
        }
        
        this.isInitialized = true;
        
        // Premier chargement immédiat
        this.updateAllAlerts();
        
        // Mise à jour périodique
        this.updateInterval = setInterval(() => {
            this.updateAllAlerts();
        }, 15000); // 15 secondes
        
        console.log('✅ Gestionnaire d\'alertes optimisé démarré');
    }
    
    // Vérifier si le cache est valide
    isCacheValid() {
        return (Date.now() - this.cache.lastUpdate) < this.cache.cacheDuration;
    }
    
    // Récupérer les données d'alertes avec cache
    async fetchAlertsData() {
        if (this.isCacheValid() && this.cache.summary && this.cache.active) {
            console.log('📦 Utilisation du cache');
            return {
                summary: this.cache.summary,
                active: this.cache.active
            };
        }
        
        try {
            const [summaryResponse, activeResponse] = await Promise.all([
                fetch('/api/alerts/summary'),
                fetch('/api/alerts/active')
            ]);
            
            if (!summaryResponse.ok || !activeResponse.ok) {
                throw new Error('Erreur lors de la récupération des alertes');
            }
            
            const summaryData = await summaryResponse.json();
            const activeData = await activeResponse.json();
            
            // Mise à jour du cache
            this.cache.summary = summaryData;
            this.cache.active = activeData;
            this.cache.lastUpdate = Date.now();
            
            console.log('🔄 Cache mis à jour:', {
                total: summaryData.summary?.active_alerts || 0,
                critiques: summaryData.summary?.by_severity?.critical?.active || 0,
                warnings: summaryData.summary?.by_severity?.warning?.active || 0
            });
            
            return {
                summary: summaryData,
                active: activeData
            };
            
        } catch (error) {
            console.error('❌ Erreur lors de la récupération des alertes:', error);
            return null;
        }
    }
    
    // Mettre à jour tous les éléments d'alertes
    async updateAllAlerts() {
        const data = await this.fetchAlertsData();
        if (!data) return;
        
        const { summary, active } = data;
        
        // Mettre à jour les compteurs
        this.updateAlertCounters(summary.summary);
        
        // Mettre à jour les badges
        this.updateAlertBadges(summary.summary);
        
        // Mettre à jour les indicateurs de santé
        this.updateHealthIndicators(summary.summary);
        
        // Mettre à jour la liste des alertes si le modal est ouvert
        if (this.isAlertsModalOpen()) {
            this.updateAlertsModal(active.alerts);
        }
    }
    
    // Mettre à jour les compteurs d'alertes
    updateAlertCounters(summary) {
        if (!summary) return;
        
        // Compteur principal
        const alertsCount = document.getElementById('alerts-count');
        if (alertsCount) {
            alertsCount.textContent = summary.active_alerts || 0;
        }
        
        // Badge dans la navbar
        const alertsBadge = document.querySelector('.alerts-count-badge');
        if (alertsBadge) {
            alertsBadge.textContent = summary.active_alerts || 0;
            alertsBadge.style.display = (summary.active_alerts > 0) ? 'inline-block' : 'none';
        }
        
        // Compteurs par sévérité
        const criticalCount = document.getElementById('critical-alerts-count');
        const warningCount = document.getElementById('warning-alerts-count');
        
        if (criticalCount) {
            criticalCount.textContent = summary.by_severity?.critical?.active || 0;
        }
        
        if (warningCount) {
            warningCount.textContent = summary.by_severity?.warning?.active || 0;
        }
        
        console.log('📊 Compteurs mis à jour:', {
            total: summary.active_alerts,
            critiques: summary.by_severity?.critical?.active || 0,
            warnings: summary.by_severity?.warning?.active || 0
        });
    }
    
    // Mettre à jour les badges d'alertes
    updateAlertBadges(summary) {
        if (!summary) return;
        
        // Badge principal
        const mainBadge = document.querySelector('.badge.bg-secondary');
        if (mainBadge) {
            mainBadge.textContent = summary.active_alerts || 0;
            mainBadge.classList.toggle('bg-danger', summary.active_alerts > 0);
            mainBadge.classList.toggle('bg-secondary', summary.active_alerts === 0);
        }
        
        // Badges par sévérité
        const severityBadges = document.querySelectorAll('[data-severity-badge]');
        severityBadges.forEach(badge => {
            const severity = badge.getAttribute('data-severity-badge');
            const count = summary.by_severity?.[severity]?.active || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        });
    }
    
    // Mettre à jour les indicateurs de santé
    updateHealthIndicators(summary) {
        if (!summary) return;
        
        // Indicateur de santé général
        const healthIndicator = document.querySelector('.health-indicator');
        if (healthIndicator) {
            const criticalCount = summary.by_severity?.critical?.active || 0;
            const warningCount = summary.by_severity?.warning?.active || 0;
            
            healthIndicator.classList.remove('health-good', 'health-warning', 'health-critical');
            
            if (criticalCount > 0) {
                healthIndicator.classList.add('health-critical');
            } else if (warningCount > 0) {
                healthIndicator.classList.add('health-warning');
            } else {
                healthIndicator.classList.add('health-good');
            }
        }
        
        // Mettre à jour les textes d'état
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            const totalAlerts = summary.active_alerts || 0;
            if (totalAlerts === 0) {
                statusText.textContent = 'Système en bon état';
            } else {
                statusText.textContent = `${totalAlerts} alerte${totalAlerts > 1 ? 's' : ''} active${totalAlerts > 1 ? 's' : ''}`;
            }
        }
    }
    
    // Vérifier si le modal d'alertes est ouvert
    isAlertsModalOpen() {
        const modal = document.getElementById('alertsModal');
        return modal && modal.classList.contains('show');
    }
    
    // Mettre à jour le contenu du modal d'alertes
    updateAlertsModal(alerts) {
        if (!alerts) return;
        
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        if (alerts.length === 0) {
            alertsList.innerHTML = '<div class="text-center text-muted py-4">Aucune alerte active</div>';
            return;
        }
        
        alertsList.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity === 'critical' ? 'danger' : 'warning'} alert-dismissible fade show" 
                 data-alert-id="${alert.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="alert-heading mb-1">
                            <i class="fas fa-${alert.severity === 'critical' ? 'exclamation-triangle' : 'exclamation-circle'} me-2"></i>
                            ${alert.title}
                        </h6>
                        <p class="mb-1">${alert.message}</p>
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            ${new Date(alert.created_at).toLocaleString('fr-FR')}
                            ${alert.occurrence_count > 1 ? ` (${alert.occurrence_count} occurrences)` : ''}
                        </small>
                    </div>
                    <button type="button" class="btn-close" 
                            onclick="acknowledgeAlert(${alert.id})" 
                            aria-label="Acquitter"></button>
                </div>
            </div>
        `).join('');
        
        console.log('📋 Modal d\'alertes mis à jour:', alerts.length, 'alertes');
    }
    
    // Acquitter une alerte
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Invalider le cache et mettre à jour
                this.cache.lastUpdate = 0;
                this.updateAllAlerts();
                console.log('✅ Alerte acquittée:', alertId);
            } else {
                console.error('❌ Erreur lors de l\'acquittement de l\'alerte:', alertId);
            }
        } catch (error) {
            console.error('❌ Erreur lors de l\'acquittement:', error);
        }
    }
    
    // Arrêter le gestionnaire
    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        this.isInitialized = false;
        console.log('🛑 Gestionnaire d\'alertes optimisé arrêté');
    }
}

// Instance globale du gestionnaire
window.optimizedAlertManager = new OptimizedAlertManager();

// Fonction globale pour acquitter les alertes
window.acknowledgeAlert = function(alertId) {
    if (window.optimizedAlertManager) {
        window.optimizedAlertManager.acknowledgeAlert(alertId);
    }
};

// Initialiser automatiquement quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    if (window.optimizedAlertManager) {
        window.optimizedAlertManager.init();
    }
});

// Nettoyer lors du déchargement de la page
window.addEventListener('beforeunload', function() {
    if (window.optimizedAlertManager) {
        window.optimizedAlertManager.stop();
    }
});

console.log('📦 Module gestionnaire d\'alertes optimisé chargé');
