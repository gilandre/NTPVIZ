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
async function loadUserData() {
    try {
        const response = await fetch('/api/user/profile');
        if (response.ok) {
            AppState.currentUser = await response.json();
            updateUserInterface();
        }
    } catch (error) {
        console.error('Erreur chargement données utilisateur:', error);
    }
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
function updateUserInterface() {
    if (AppState.currentUser) {
        // Mettre à jour les éléments de l'interface avec les données utilisateur
        const userElements = document.querySelectorAll('.user-info');
        userElements.forEach(element => {
            element.textContent = AppState.currentUser.username;
        });
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