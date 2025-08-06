/**
 * Module Client Monitor - Monitoring des clients NTP
 */
class ClientMonitor {
    constructor() {
        this.updateInterval = null;
        this.isActive = false;
        this.config = { updateInterval: 30000 };
        this.initEventListeners();
    }
    
    initEventListeners() {
        document.addEventListener('DOMContentLoaded', () => this.start());
    }
    
    async start() {
        if (this.isActive) return;
        
        // Vérifier l'authentification avant de démarrer
        if (!this.isUserAuthenticated()) {
            console.log('🔒 Monitoring non démarré - utilisateur non authentifié');
            return;
        }
        
        this.isActive = true;
        console.log('🚀 Démarrage du monitoring des clients NTP');
        
        await this.updateAll();
        this.updateInterval = setInterval(() => this.updateAll(), this.config.updateInterval);
        this.connectWebSocket();
    }
    
    stop() {
        this.isActive = false;
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async forceUpdate() {
        await this.updateAll();
    }
    
    async updateAll() {
        try {
            // Vérifier si l'utilisateur est authentifié
            if (!this.isUserAuthenticated()) {
                console.log('🔒 Utilisateur non authentifié - arrêt du monitoring');
                this.stop();
                return;
            }
            
            const [serviceStatus, connections, stats] = await Promise.all([
                this.fetchServiceStatus(),
                this.fetchActiveConnections(), 
                this.fetchClientStatistics()
            ]);
            
            this.updateServiceStatusDisplay(serviceStatus);
            this.updateActiveConnectionsDisplay(connections);
            this.updateStatisticsDisplay(stats);
            
        } catch (error) {
            console.error('Erreur monitoring:', error);
            this.showError(error);
        }
    }
    
    async fetchServiceStatus() {
        try {
            const response = await fetch('/api/ntp/service/status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            // Vérifier si la réponse est du JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.warn('⚠️ Réponse non-JSON reçue pour service status - probablement redirection de connexion');
                return { service_status: 'error', port_listening: false, port: 123 };
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur fetchServiceStatus:', error);
            return { service_status: 'error', port_listening: false, port: 123 };
        }
    }
    
    async fetchActiveConnections() {
        try {
            const response = await fetch('/api/ntp/clients/connections');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            // Vérifier si la réponse est du JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.warn('⚠️ Réponse non-JSON reçue pour connexions actives - probablement redirection de connexion');
                return [];
            }
            
            const data = await response.json();
            
            // CORRECTION EmaraudeNTP VIZ: L'API retourne un objet avec propriété 'connections'
            if (data && typeof data === 'object') {
                if (Array.isArray(data.connections)) {
                    console.log(`📡 ${data.connections.length} connexions actives, ${data.active_connections || 0} clients uniques`);
                    return data.connections;
                } else if (Array.isArray(data)) {
                    // Fallback: si c'est directement un array
                    console.log(`📡 ${data.length} connexions actives (format direct)`);
                    return data;
                } else {
                    console.warn('⚠️ Structure API inattendue:', data);
                    return [];
                }
            }
            
            console.warn('⚠️ Données API invalides:', data);
            return [];
        } catch (error) {
            console.error('❌ Erreur fetchActiveConnections:', error);
            return [];
        }
    }
    
    async fetchClientStatistics() {
        try {
            const response = await fetch('/api/ntp/clients/statistics?hours=24');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            // Vérifier si la réponse est du JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.warn('⚠️ Réponse non-JSON reçue pour statistiques clients - probablement redirection de connexion');
                return { total_connections: 0, unique_clients: 0, top_clients: [] };
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur fetchClientStatistics:', error);
            return { total_connections: 0, unique_clients: 0, top_clients: [] };
        }
    }
    
    updateServiceStatusDisplay(serviceStatus) {
        // Mettre à jour le statut du service dans la section monitoring
        const serviceStatusEl = document.getElementById('service-status');
        const servicePortEl = document.getElementById('service-port');
        
        if (serviceStatusEl) {
            if (serviceStatus.service_status === 'active' && serviceStatus.port_listening) {
                serviceStatusEl.textContent = 'Actif';
                serviceStatusEl.className = 'badge bg-success';
            } else if (serviceStatus.service_status === 'active') {
                serviceStatusEl.textContent = 'Actif (port fermé)';
                serviceStatusEl.className = 'badge bg-warning';
            } else {
                serviceStatusEl.textContent = 'Inactif';
                serviceStatusEl.className = 'badge bg-danger';
            }
        }
        
        if (servicePortEl) {
            servicePortEl.textContent = serviceStatus.port || 123;
        }
    }
    
    updateActiveConnectionsDisplay(connections) {
        // Mettre à jour le nombre de connexions actives
        const activeConnectionsEl = document.getElementById('active-connections');
        if (activeConnectionsEl) {
            activeConnectionsEl.textContent = Array.isArray(connections) ? connections.length : 0;
        }
        
        console.log(`📡 ${Array.isArray(connections) ? connections.length : 0} connexions actives mises à jour`);
    }
    
    updateStatisticsDisplay(statistics) {
        // Mettre à jour les clients uniques
        const uniqueClientsEl = document.getElementById('unique-clients');
        if (uniqueClientsEl) {
            uniqueClientsEl.textContent = statistics.unique_clients || 0;
        }
        
        // Mettre à jour le total 24h
        const total24hEl = document.getElementById('total-connections-24h');
        if (total24hEl) {
            total24hEl.textContent = statistics.total_connections || 0;
        }
        
        // Mettre à jour le top clients
        const topClientsEl = document.getElementById('top-clients');
        if (topClientsEl && statistics.top_clients) {
            let html = '';
            
            if (statistics.top_clients.length === 0) {
                html = `
                    <div class="col-12 text-center text-muted">
                        <i class="fas fa-users-slash fa-2x mb-2"></i>
                        <p class="mb-0">Aucun client actif</p>
                    </div>
                `;
            } else {
                statistics.top_clients.slice(0, 6).forEach((client, index) => {
                    html += `
                        <div class="col-md-4 mb-2">
                            <div class="d-flex justify-content-between align-items-center p-2 border rounded">
                                <span class="text-truncate" title="${client.ip}">
                                    <i class="fas fa-desktop me-1"></i>
                                    ${client.ip}
                                </span>
                                <span class="badge bg-primary">${client.connections}</span>
                            </div>
                        </div>
                    `;
                });
            }
            
            topClientsEl.innerHTML = html;
        }
    }
    
    connectWebSocket() {
        if (typeof io === 'undefined') return;
        
        const socket = io();
        socket.on('client_monitoring_update', (data) => {
            if (data.connections) this.updateActiveConnectionsDisplay(data.connections);
            if (data.client_stats) this.updateStatisticsDisplay(data.client_stats);
            if (data.service_status) this.updateServiceStatusDisplay(data.service_status);
        });
        
        socket.emit('subscribe', { type: 'client_monitoring', interval: 30 });
    }
    
    showError(error) {
        const element = document.getElementById('ntp-service-status');
        if (element) {
            element.innerHTML = `
                <span class="badge bg-danger">
                    <i class="fas fa-exclamation-triangle me-1"></i>Erreur
                </span>
                <small class="d-block text-danger mt-1">${error.message}</small>
            `;
        }
    }
    
    // Méthodes publiques
    getCurrentData() {
        return this.cache || {};
    }
    
    isMonitoringActive() {
        return this.isActive;
    }
    
    isUserAuthenticated() {
        // Vérifier si l'utilisateur est connecté en cherchant des éléments d'authentification
        const loginForm = document.querySelector('form[action*="login"]');
        const logoutButton = document.querySelector('a[href*="logout"]');
        const userMenu = document.querySelector('.user-menu, .navbar-nav .dropdown');
        
        // Si on trouve un formulaire de connexion, l'utilisateur n'est pas connecté
        if (loginForm) {
            return false;
        }
        
        // Si on trouve un bouton de déconnexion ou un menu utilisateur, l'utilisateur est connecté
        if (logoutButton || userMenu) {
            return true;
        }
        
        // Vérification par défaut - si on est sur une page qui nécessite une authentification
        const currentPath = window.location.pathname;
        if (currentPath === '/login' || currentPath === '/auth/login') {
            return false;
        }
        
        // Si on est sur le dashboard ou une page protégée, on suppose que l'utilisateur est connecté
        return true;
    }
}

// Instance globale
window.clientMonitor = new ClientMonitor();

// Export pour les modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClientMonitor;
} 