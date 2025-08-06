/**
 * NTP Monitor Enterprise - Application JavaScript principale
 */

// Configuration globale
const AppConfig = {
    refreshInterval: 30000, // 30 secondes
    apiBaseUrl: '/api',
    wsNamespace: '/ws'
};

// État global de l'application
const AppState = {
    isConnected: false,
    currentUser: null,
    lastUpdate: null,
    ntpServers: [],
    alerts: []
};

/**
 * Initialiser l'application
 */
function initApp() {
    console.log('Initialisation de NTP Monitor Enterprise...');
    
    // Charger les données utilisateur
    loadUserData();
    
    // Initialiser les composants
    initializeComponents();
    
    // Démarrer les mises à jour automatiques
    startAutoRefresh();
    
    console.log('Application initialisée avec succès');
}

/**
 * Charger les données utilisateur
 */
function loadUserData() {
    fetch('/api/session/check')
        .then(response => response.json())
        .then(data => {
            if (data.authenticated && data.user) {
                updateUserInterface(data.user);
            }
        })
        .catch(error => {
            console.warn('Données utilisateur non disponibles:', error);
        });
}

/**
 * Initialiser les composants de l'interface
 */
function initializeComponents() {
    // Initialiser les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialiser les popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Mettre à jour l'interface utilisateur
 */
function updateUserInterface(user) {
    if (user) {
        // Mettre à jour les éléments de l'interface avec les données utilisateur
        const userElements = document.querySelectorAll('.user-info');
        userElements.forEach(element => {
            element.textContent = user.username;
        });
        AppState.currentUser = user;
    }
}

/**
 * Démarrer les mises à jour automatiques
 */
function startAutoRefresh() {
    setInterval(() => {
        if (typeof refreshDashboard === 'function') {
            refreshDashboard();
        }
        AppState.lastUpdate = new Date();
    }, AppConfig.refreshInterval);
}

/**
 * Afficher une notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    const alertsContainer = document.getElementById('system-alerts');
    if (!alertsContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getIconForType(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertsContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss après la durée spécifiée
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = bootstrap.Alert.getInstance(alert);
                if (bsAlert) bsAlert.close();
            }
        }, duration);
    }
}

/**
 * Obtenir l'icône pour un type d'alerte
 */
function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'primary': 'info-circle',
        'secondary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Utilitaires de formatage
 */
const Utils = {
    formatDate: function(date) {
        return moment(date).format('DD/MM/YYYY HH:mm:ss');
    },
    
    formatDuration: function(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    },
    
    formatBytes: function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// Exporter les fonctions pour usage global
window.AppConfig = AppConfig;
window.AppState = AppState;
window.initApp = initApp;
window.showNotification = showNotification;
window.Utils = Utils;

// ================== FONCTIONS GLOBALES POUR LA CONFIGURATION ==================

/**
 * Ouvre le module Configuration directement sur la catégorie Alertes
 */
function openConfigurationAlertes() {
    console.log('🛠️ Ouverture de la configuration des alertes');
    
    // Fermer le modal des alertes s'il est ouvert
    const alertsModal = bootstrap.Modal.getInstance(document.getElementById('alertsModal'));
    if (alertsModal) {
        alertsModal.hide();
    }
    
    // Ouvrir le modal de configuration
    const configModal = new bootstrap.Modal(document.getElementById('configModal'));
    configModal.show();
    
    // Charger directement la catégorie alertes après un délai
    setTimeout(() => {
        if (window.configManager) {
            window.configManager.loadCategory('alerts');
        } else {
            console.error('ConfigManager non disponible');
        }
    }, 500);
}

/**
 * Ouvre le module Configuration sur une catégorie spécifique
 */
function openConfiguration(category = null) {
    console.log(`🛠️ Ouverture de la configuration${category ? ' - ' + category : ''}`);
    
    const configModal = new bootstrap.Modal(document.getElementById('configModal'));
    configModal.show();
    
    if (category && window.configManager) {
        setTimeout(() => {
            window.configManager.loadCategory(category);
        }, 500);
    }
}

/**
 * Ouvre le modal de configuration depuis la navigation
 */
function openConfigModal() {
    console.log('🛠️ Ouverture du modal de configuration');
    
    const configModal = new bootstrap.Modal(document.getElementById('configModal'));
    configModal.show();
    
    // Le ConfigManager sera initialisé automatiquement via l'événement shown.bs.modal
} 