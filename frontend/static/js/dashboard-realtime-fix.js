/**
 * Dashboard Realtime Fix - NTP Monitor Enterprise
 * Corrige les problèmes de mise à jour temps réel des "Dernière sync"
 */

// Variables globales pour le système de mise à jour temps réel
let dashboardRealtimeTimer = null;
let lastSyncUpdateTimer = null;

// Fonction principale pour corriger la mise à jour temps réel
function fixDashboardRealtime() {
    console.log('🔧 Correction système temps réel dashboard');
    
    // Arrêter les anciens timers s'ils existent
    if (dashboardRealtimeTimer) {
        clearInterval(dashboardRealtimeTimer);
    }
    if (lastSyncUpdateTimer) {
        clearInterval(lastSyncUpdateTimer);
    }
    
    // Démarrer les nouveaux timers avec correction
    startFixedRealtimeUpdates();
}

// Démarrer les mises à jour temps réel corrigées
function startFixedRealtimeUpdates() {
    console.log('⏰ Démarrage mises à jour temps réel corrigées');
    
    // 1. Mise à jour des heures des serveurs toutes les secondes
    dashboardRealtimeTimer = setInterval(() => {
        updateAllServerTimes();
    }, 1000);
    
    // 2. Mise à jour des "Dernière sync" toutes les 10 secondes
    lastSyncUpdateTimer = setInterval(() => {
        updateAllLastSyncTimes();
    }, 10000);
    
    // 3. Mise à jour immédiate
    updateAllServerTimes();
    updateAllLastSyncTimes();
}

// Mettre à jour toutes les heures des serveurs
function updateAllServerTimes() {
    try {
        const servers = window.lastServersData || [];
        
        servers.forEach(server => {
            const timeElement = document.getElementById(`server-time-${server.id}`);
            if (timeElement) {
                const now = new Date();
                const serverTime = server.last_offset !== null ? 
                    new Date(now.getTime() + (server.last_offset || 0) * 1000) : 
                    new Date();
                
                const isServerOnline = server.status === 'online' || server.status === 'ok';
                const currentTimeFormatted = isServerOnline ? 
                    serverTime.toLocaleTimeString('fr-FR', { 
                        hour: '2-digit', 
                        minute: '2-digit',
                        second: '2-digit'
                    }) : '--:--:--';
                
                timeElement.textContent = currentTimeFormatted;
            }
        });
    } catch (error) {
        console.error('❌ Erreur mise à jour heures serveurs:', error);
    }
}

// Mettre à jour tous les textes "Dernière sync"
function updateAllLastSyncTimes() {
    try {
        const servers = window.lastServersData || [];
        
        servers.forEach(server => {
            // Trouver les éléments contenant "Dernière sync" pour ce serveur
            const syncElements = document.querySelectorAll('small.text-muted');
            
            syncElements.forEach(element => {
                const text = element.textContent;
                if (text && text.includes('Dernière sync:')) {
                    // Vérifier si cet élément appartient à ce serveur
                    const card = element.closest('.card');
                    if (card) {
                        const timeElement = card.querySelector(`#server-time-${server.id}`);
                        if (timeElement && server.last_sync) {
                            const lastSyncDate = new Date(server.last_sync);
                            const lastSyncFormatted = lastSyncDate.toLocaleTimeString('fr-FR', { 
                                hour: '2-digit', 
                                minute: '2-digit',
                                second: '2-digit'
                            });
                            const timeAgo = getTimeAgo(lastSyncDate);
                            
                            element.innerHTML = `
                                <i class="fas fa-sync me-1"></i>
                                Dernière sync: ${lastSyncFormatted}${timeAgo ? ' (' + timeAgo + ')' : ''}
                            `;
                        }
                    }
                }
            });
        });
    } catch (error) {
        console.error('❌ Erreur mise à jour dernière sync:', error);
    }
}

// Fonction utilitaire pour calculer le temps écoulé (compatible avec dashboard.js)
function getTimeAgo(date) {
    if (!date) return '';
    
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
        return `${diffDays}j`;
    } else if (diffHours > 0) {
        return `${diffHours}h`;
    } else if (diffMinutes > 0) {
        return `${diffMinutes}min`;
    } else {
        return 'maintenant';
    }
}

// Améliorer le système d'auto-refresh avec informations de débogage
function enhanceAutoRefresh() {
    console.log('🔧 Amélioration système auto-refresh');
    
    // Créer un indicateur visuel de mise à jour
    createUpdateIndicator();
    
    // Surcharger la fonction loadDashboardData pour afficher les mises à jour
    if (typeof loadDashboardData === 'function') {
        const originalLoadDashboardData = loadDashboardData;
        
        window.loadDashboardData = function() {
            console.log('📊 Chargement données dashboard:', new Date().toLocaleTimeString());
            showUpdateIndicator();
            
            return originalLoadDashboardData.apply(this, arguments);
        };
    }
}

// Créer un indicateur visuel de mise à jour
function createUpdateIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'update-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 123, 255, 0.9);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        z-index: 1000;
        display: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin me-1"></i>Mise à jour...';
    document.body.appendChild(indicator);
}

// Afficher l'indicateur de mise à jour
function showUpdateIndicator() {
    const indicator = document.getElementById('update-indicator');
    if (indicator) {
        indicator.style.display = 'block';
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }
}

// Fonction d'initialisation automatique
function initDashboardRealtimeFix() {
    console.log('🚀 Initialisation correction temps réel dashboard');
    
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(fixDashboardRealtime, 1000);
            setTimeout(enhanceAutoRefresh, 1500);
        });
    } else {
        setTimeout(fixDashboardRealtime, 1000);
        setTimeout(enhanceAutoRefresh, 1500);
    }
}

// Arrêter les mises à jour (pour debugging)
function stopRealtimeUpdates() {
    if (dashboardRealtimeTimer) {
        clearInterval(dashboardRealtimeTimer);
        dashboardRealtimeTimer = null;
    }
    if (lastSyncUpdateTimer) {
        clearInterval(lastSyncUpdateTimer);
        lastSyncUpdateTimer = null;
    }
    console.log('🛑 Mises à jour temps réel arrêtées');
}

// Démarrer automatiquement
initDashboardRealtimeFix();

// Exposer les fonctions pour debugging
window.dashboardRealtimeFix = {
    fix: fixDashboardRealtime,
    start: startFixedRealtimeUpdates,
    stop: stopRealtimeUpdates,
    updateTimes: updateAllServerTimes,
    updateSyncs: updateAllLastSyncTimes
}; 