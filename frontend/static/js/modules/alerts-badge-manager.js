/**
 * Gestionnaire des badges d'alertes
 * Gère l'affichage et la mise à jour des badges d'alertes dans la navigation
 */

class AlertsBadgeManager {
    constructor() {
        this.badges = [];
        this.isInitialized = false;
        this.updateInterval = null;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    /**
     * Initialiser le gestionnaire
     */
    init() {
        if (this.isInitialized) return;
        
        console.log('🏷️ Initialisation du gestionnaire de badges...');
        
        // Sélectionner tous les badges d'alertes
        this.badges = document.querySelectorAll('.alerts-count-badge');
        
        if (this.badges.length === 0) {
            console.warn('⚠️ Aucun badge d\'alerte trouvé');
            return;
        }
        
        console.log(`✅ ${this.badges.length} badge(s) trouvé(s)`);
        
        // Première mise à jour
        this.updateAllBadges();
        
        // Mise à jour périodique toutes les 30 secondes
        this.updateInterval = setInterval(() => {
            this.updateAllBadges();
        }, 30000);
        
        this.isInitialized = true;
    }

    /**
     * Mettre à jour tous les badges d'alertes (VERSION CORRIGÉE)
     */
    async updateAllBadges() {
        try {
            const alertsData = await this.fetchAlertsData();
            
            if (alertsData && typeof alertsData === 'object') {
                // Gestion robuste des différentes structures possibles
                let alertsCount = 0;
                
                if (typeof alertsData.total_active === 'number') {
                    alertsCount = alertsData.total_active;
                } else if (alertsData.summary && typeof alertsData.summary.active_alerts === 'number') {
                    alertsCount = alertsData.summary.active_alerts;
                } else if (typeof alertsData.active_alerts === 'number') {
                    alertsCount = alertsData.active_alerts;
                } else {
                    console.warn('⚠️ Structure de données inconnue:', alertsData);
                    alertsCount = 0;
                }
                
                this.setBadgeCount(alertsCount);
                console.log(`🏷️ Badges mis à jour: ${alertsCount} alertes actives`);
                
                // Reset retry count on success
                this.retryCount = 0;
            } else {
                console.warn('⚠️ Données invalides reçues:', alertsData);
                this.handleError('Données invalides');
            }
        } catch (error) {
            console.error('❌ Erreur mise à jour badges:', error);
            this.handleError(error);
        }
    }

    /**
     * Gestion des erreurs avec retry
     */
    handleError(error) {
        this.retryCount++;
        
        if (this.retryCount <= this.maxRetries) {
            console.log(`🔄 Tentative ${this.retryCount}/${this.maxRetries} dans 5 secondes...`);
            setTimeout(() => this.updateAllBadges(), 5000);
        } else {
            console.error('❌ Échec après', this.maxRetries, 'tentatives');
            // Afficher 0 mais garder les badges visibles
            this.setBadgeCount(0);
        }
    }

    /**
     * Définir le nombre d'alertes sur tous les badges
     */
    setBadgeCount(count) {
        const validCount = Math.max(0, parseInt(count) || 0);
        
        this.badges.forEach(badge => {
            badge.textContent = validCount;
            this.updateBadgeStyle(badge, validCount);
        });
    }

    /**
     * Mettre à jour le style du badge selon le nombre d'alertes
     */
    updateBadgeStyle(element, count) {
        // Supprimer les classes existantes
        element.classList.remove('bg-danger', 'bg-warning', 'bg-secondary', 'bg-success');
        
        // Ajouter la classe appropriée
        if (count === 0) {
            element.classList.add('bg-secondary');
            element.style.display = 'none'; // Masquer si aucune alerte
        } else if (count <= 3) {
            element.classList.add('bg-warning');
            element.style.display = 'inline';
        } else {
            element.classList.add('bg-danger');
            element.style.display = 'inline';
        }
    }

    /**
     * Récupérer les données d'alertes depuis l'API
     */
    async fetchAlertsData() {
        try {
            const response = await fetch('/api/alerts/summary', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data && data.success && data.summary) {
                return {
                    total_active: data.summary.active_alerts || 0,
                    critical: data.summary.by_severity?.critical?.active || 0,
                    warning: data.summary.by_severity?.warning?.active || 0,
                    info: data.summary.by_severity?.info?.active || 0
                };
            }
            
            return null;
        } catch (error) {
            console.error('❌ Erreur récupération données alertes:', error);
            return null;
        }
    }

    /**
     * Forcer une mise à jour immédiate
     */
    forceUpdate() {
        console.log('🔄 Mise à jour forcée des badges...');
        this.retryCount = 0; // Reset retry count
        this.updateAllBadges();
    }

    /**
     * Obtenir le nombre actuel d'alertes affiché
     */
    getCurrentCount() {
        return this.badges.length > 0 ? parseInt(this.badges[0].textContent) || 0 : 0;
    }

    /**
     * Arrêter le gestionnaire
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        this.isInitialized = false;
        console.log('🛑 Gestionnaire de badges arrêté');
    }
}

// Créer une instance globale
window.alertsBadgeManager = new AlertsBadgeManager(); 