/**
 * Script de correction automatique pour l'affichage des alertes NTPVIZ
 * Ce script force la mise à jour des badges d'alertes
 */

(function() {
    'use strict';
    
    console.log('🔧 Script de correction d\'affichage des alertes chargé');
    
    // Configuration
    const CONFIG = {
        updateInterval: 15000, // 15 secondes
        maxRetries: 3,
        debug: true
    };
    
    // Variables globales
    let updateTimer = null;
    let retryCount = 0;
    let lastUpdateTime = 0;
    
    // Fonction pour logger avec timestamp
    function log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const emoji = type === 'error' ? '❌' : type === 'success' ? '✅' : '🔧';
        console.log(`[${timestamp}] ${emoji} AlertDisplayFix: ${message}`);
    }
    
    // Fonction pour récupérer les données d'alertes
    async function fetchAlertData() {
        try {
            const response = await fetch('/api/alerts/summary');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (!data.success || !data.summary) {
                throw new Error('Données d\'alertes invalides');
            }
            
            return data.summary;
        } catch (error) {
            log(`Erreur lors de la récupération des alertes: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // Fonction pour mettre à jour les badges
    function updateAlertBadges(summary) {
        const activeCount = summary.active_alerts || 0;
        const criticalCount = summary.by_severity?.critical?.active || 0;
        const warningCount = summary.by_severity?.warning?.active || 0;
        const unreadCount = summary.unread_count || 0;
        
        let updatedElements = 0;
        
        // Mettre à jour les badges avec ID alerts-count
        const alertsCountElements = document.querySelectorAll('#alerts-count');
        alertsCountElements.forEach((element, index) => {
            if (element.textContent !== activeCount.toString()) {
                element.textContent = activeCount;
                updatedElements++;
                log(`Badge #alerts-count ${index + 1} mis à jour: ${activeCount}`);
            }
        });
        
        // Mettre à jour les badges avec classe alerts-count-badge
        const alertsBadgeElements = document.querySelectorAll('.alerts-count-badge');
        alertsBadgeElements.forEach((element, index) => {
            if (element.textContent !== activeCount.toString()) {
                element.textContent = activeCount;
                element.style.display = activeCount > 0 ? 'inline-block' : 'none';
                
                // Ajouter une classe pour indiquer l'état
                if (activeCount > 0) {
                    element.classList.remove('bg-secondary');
                    element.classList.add(criticalCount > 0 ? 'bg-danger' : 'bg-warning');
                } else {
                    element.classList.remove('bg-danger', 'bg-warning');
                    element.classList.add('bg-secondary');
                }
                
                updatedElements++;
                log(`Badge .alerts-count-badge ${index + 1} mis à jour: ${activeCount}`);
            }
        });
        
        // Mettre à jour les badges par sévérité
        const severityBadges = document.querySelectorAll('[data-severity-badge]');
        severityBadges.forEach((badge, index) => {
            const severity = badge.getAttribute('data-severity-badge');
            let count = 0;
            
            switch (severity) {
                case 'critical':
                    count = criticalCount;
                    break;
                case 'warning':
                    count = warningCount;
                    break;
                default:
                    count = 0;
            }
            
            if (badge.textContent !== count.toString()) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
                updatedElements++;
                log(`Badge sévérité ${severity} ${index + 1} mis à jour: ${count}`);
            }
        });
        
        // Mettre à jour les compteurs dans les cartes du dashboard
        const dashboardCounters = [
            { selector: '#alerts-count', value: activeCount },
            { selector: '#critical-alerts-count', value: criticalCount },
            { selector: '#warning-alerts-count', value: warningCount },
            { selector: '#unread-alerts-count', value: unreadCount }
        ];
        
        dashboardCounters.forEach(counter => {
            const elements = document.querySelectorAll(counter.selector);
            elements.forEach((element, index) => {
                if (element.textContent !== counter.value.toString()) {
                    element.textContent = counter.value;
                    updatedElements++;
                    log(`Compteur ${counter.selector} ${index + 1} mis à jour: ${counter.value}`);
                }
            });
        });
        
        return updatedElements;
    }
    
    // Fonction pour mettre à jour les indicateurs de santé
    function updateHealthIndicators(summary) {
        const activeCount = summary.active_alerts || 0;
        const criticalCount = summary.by_severity?.critical?.active || 0;
        const warningCount = summary.by_severity?.warning?.active || 0;
        
        // Mettre à jour les indicateurs de santé
        const healthIndicators = document.querySelectorAll('.health-indicator');
        healthIndicators.forEach(indicator => {
            indicator.classList.remove('health-good', 'health-warning', 'health-critical');
            
            if (criticalCount > 0) {
                indicator.classList.add('health-critical');
            } else if (warningCount > 0) {
                indicator.classList.add('health-warning');
            } else {
                indicator.classList.add('health-good');
            }
        });
        
        // Mettre à jour les textes de statut
        const statusTexts = document.querySelectorAll('.status-text');
        statusTexts.forEach(statusText => {
            if (activeCount === 0) {
                statusText.textContent = 'Système en bon état';
                statusText.className = 'status-text text-success';
            } else {
                statusText.textContent = `${activeCount} alerte${activeCount > 1 ? 's' : ''} active${activeCount > 1 ? 's' : ''}`;
                statusText.className = criticalCount > 0 ? 'status-text text-danger' : 'status-text text-warning';
            }
        });
    }
    
    // Fonction principale de mise à jour
    async function performUpdate() {
        try {
            log('Début de la mise à jour des alertes...');
            
            const summary = await fetchAlertData();
            const updatedElements = updateAlertBadges(summary);
            updateHealthIndicators(summary);
            
            lastUpdateTime = Date.now();
            retryCount = 0;
            
            log(`Mise à jour terminée: ${summary.active_alerts} alertes actives, ${updatedElements} éléments mis à jour`, 'success');
            
        } catch (error) {
            retryCount++;
            log(`Échec de la mise à jour (tentative ${retryCount}/${CONFIG.maxRetries}): ${error.message}`, 'error');
            
            if (retryCount >= CONFIG.maxRetries) {
                log('Nombre maximum de tentatives atteint, arrêt des mises à jour', 'error');
                stopAutoUpdate();
            }
        }
    }
    
    // Fonction pour démarrer les mises à jour automatiques
    function startAutoUpdate() {
        if (updateTimer) {
            clearInterval(updateTimer);
        }
        
        log(`Démarrage des mises à jour automatiques (intervalle: ${CONFIG.updateInterval}ms)`);
        
        // Première mise à jour immédiate
        performUpdate();
        
        // Mises à jour périodiques
        updateTimer = setInterval(performUpdate, CONFIG.updateInterval);
    }
    
    // Fonction pour arrêter les mises à jour automatiques
    function stopAutoUpdate() {
        if (updateTimer) {
            clearInterval(updateTimer);
            updateTimer = null;
            log('Mises à jour automatiques arrêtées');
        }
    }
    
    // Fonction de diagnostic
    function runDiagnostic() {
        log('=== DIAGNOSTIC DES ÉLÉMENTS D\'ALERTES ===');
        
        const selectors = [
            '#alerts-count',
            '.alerts-count-badge',
            '[data-severity-badge]',
            '.health-indicator',
            '.status-text'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            log(`${selector}: ${elements.length} élément(s) trouvé(s)`);
            
            elements.forEach((element, index) => {
                log(`  ${index + 1}. Contenu: "${element.textContent.trim()}" | Classes: ${element.className}`);
            });
        });
        
        log('=== FIN DU DIAGNOSTIC ===');
    }
    
    // Fonction d'initialisation
    function initialize() {
        log('Initialisation du correcteur d\'affichage des alertes');
        
        // Attendre que le DOM soit complètement chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(initialize, 1000);
            });
            return;
        }
        
        // Diagnostic initial
        if (CONFIG.debug) {
            runDiagnostic();
        }
        
        // Démarrer les mises à jour automatiques
        startAutoUpdate();
        
        // Exposer les fonctions pour usage manuel
        window.alertDisplayFix = {
            update: performUpdate,
            start: startAutoUpdate,
            stop: stopAutoUpdate,
            diagnostic: runDiagnostic,
            getLastUpdate: () => lastUpdateTime
        };
        
        log('Correcteur d\'affichage des alertes initialisé avec succès', 'success');
    }
    
    // Démarrer l'initialisation
    initialize();
    
    // Nettoyer lors du déchargement de la page
    window.addEventListener('beforeunload', function() {
        stopAutoUpdate();
    });
    
})(); 