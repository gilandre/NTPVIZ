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
        this.isActive = true;
        
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
            
            const data = await response.json();
            
            // Vérifier que data est bien un array, sinon retourner array vide
            if (!Array.isArray(data)) {
                console.warn('API connexions retourne non-array:', data);
                return [];
            }
            
            return data;
        } catch (error) {
            console.error('Erreur fetchActiveConnections:', error);
            return [];
        }
    }
    
    async fetchClientStatistics() {
        try {
            const response = await fetch('/api/ntp/clients/statistics?hours=24');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erreur fetchClientStatistics:', error);
            return { total_connections: 0, unique_clients: 0, top_clients: [] };
        }
    }
    
    updateServiceStatusDisplay(serviceStatus) {
        const element = document.getElementById('ntp-service-status');
        if (!element) return;
        
        let statusClass = 'bg-secondary', statusIcon = 'fas fa-question', statusText = 'Inconnu';
        
        if (serviceStatus.service_status === 'active' && serviceStatus.port_listening) {
            statusClass = 'bg-success';
            statusIcon = 'fas fa-check-circle';
            statusText = 'Service actif';
        } else if (serviceStatus.service_status === 'active') {
            statusClass = 'bg-warning';
            statusIcon = 'fas fa-exclamation-triangle';
            statusText = 'Service actif (port fermé)';
        } else {
            statusClass = 'bg-danger';
            statusIcon = 'fas fa-times-circle';
            statusText = 'Service inactif';
        }
        
        element.innerHTML = `
            <span class="badge ${statusClass}">
                <i class="${statusIcon} me-1"></i>${statusText}
            </span>
            <small class="d-block text-muted mt-1">Port ${serviceStatus.port}</small>
        `;
    }
    
    updateActiveConnectionsDisplay(connections) {
        const element = document.getElementById('active-connections');
        if (!element) return;
        
        // Vérifier que connections est un array valide
        if (!Array.isArray(connections) || connections.length === 0) {
            element.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-wifi-slash fa-2x mb-2"></i>
                    <p class="mb-0">Aucune connexion active</p>
                    ${!Array.isArray(connections) ? '<small class="text-warning">Données invalides</small>' : ''}
                </div>
            `;
            return;
        }
        
        const clientGroups = {};
        if (Array.isArray(connections)) connections.forEach(conn => {
            if (conn && conn.client_ip) {
                if (!clientGroups[conn.client_ip]) clientGroups[conn.client_ip] = [];
                clientGroups[conn.client_ip].push(conn);
            }
        });
        
        const uniqueClients = Object.keys(clientGroups).length;
        
        let html = `
            <div class="d-flex justify-content-between mb-2">
                <span class="fw-bold text-primary">${connections.length}</span>
                <small class="text-muted">${uniqueClients} client(s)</small>
            </div>
        `;
        
        const sortedClients = Object.entries(clientGroups)
            .sort((a, b) => b[1].length - a[1].length)
            .slice(0, 5);
        
        if (sortedClients.length > 0) {
            html += '<div class="client-list">';
            sortedClients.forEach(([ip, conns]) => {
                html += `
                    <div class="d-flex justify-content-between py-1">
                        <small class="text-truncate" title="${ip}">${ip}</small>
                        <span class="badge bg-light text-dark">${conns.length}</span>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        element.innerHTML = html;
    }
    
    updateStatisticsDisplay(statistics) {
        const element = document.getElementById('client-stats');
        if (!element) return;
        
        if (!statistics || statistics.error) {
            element.innerHTML = '<div class="text-muted">Données non disponibles</div>';
            return;
        }
        
        let html = `
            <div class="row text-center">
                <div class="col-6">
                    <div class="border-end">
                        <h6 class="text-primary mb-1">${statistics.total_connections || 0}</h6>
                        <small class="text-muted">Connexions totales</small>
                    </div>
                </div>
                <div class="col-6">
                    <h6 class="text-success mb-1">${statistics.unique_clients || 0}</h6>
                    <small class="text-muted">Clients uniques</small>
                </div>
            </div>
        `;
        
        if (statistics.top_clients && Array.isArray(statistics.top_clients) && statistics.top_clients.length > 0) {
            html += '<hr><h6 class="mb-2">Top clients (24h)</h6><div class="top-clients">';
            statistics.top_clients.slice(0, 5).forEach(client => {
                html += `
                    <div class="d-flex justify-content-between py-1">
                        <small title="${client.ip}">${client.ip}</small>
                        <span class="badge bg-info">${client.connections}</span>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        element.innerHTML = html;
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
}

// Instance globale
window.clientMonitor = new ClientMonitor();

// Export pour les modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClientMonitor;
} 