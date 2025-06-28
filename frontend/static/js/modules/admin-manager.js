/**
 * Administration Manager - Gestion avancée de l'administration système
 * NTP Monitor Enterprise
 */

class AdminManager {
    constructor() {
        this.currentView = 'overview';
        this.users = [];
        this.servers = [];
        this.stats = {};
        this.selectedItems = new Set();
        
        this.init();
    }
    
    async init() {
        await this.loadOverview();
        this.setupEventListeners();
        this.setupDataTables();
        this.setupAutoRefresh();
    }
    
    // ================== CHARGEMENT DES DONNÉES ==================
    
    async loadOverview() {
        try {
            const response = await fetch('/api/admin/stats/overview');
            if (!response.ok) throw new Error('Erreur chargement vue d\'ensemble');
            
            this.stats = await response.json();
            this.renderOverview();
            
        } catch (error) {
            console.error('Erreur lors du chargement de la vue d\'ensemble:', error);
            this.showNotification('Erreur de chargement de la vue d\'ensemble', 'error');
        }
    }
    
    async loadDetailedStats(days = 7) {
        try {
            const response = await fetch(`/api/admin/stats/detailed?days=${days}`);
            if (!response.ok) throw new Error('Erreur chargement statistiques détaillées');
            
            const detailedStats = await response.json();
            this.renderDetailedStats(detailedStats);
            
        } catch (error) {
            console.error('Erreur lors du chargement des statistiques détaillées:', error);
            this.showNotification('Erreur de chargement des statistiques', 'error');
        }
    }
    
    async loadUsers() {
        try {
            const response = await fetch('/api/admin/users');
            if (!response.ok) throw new Error('Erreur chargement utilisateurs');
            
            this.users = await response.json();
            this.renderUsersTable();
            
        } catch (error) {
            console.error('Erreur lors du chargement des utilisateurs:', error);
            this.showNotification('Erreur de chargement des utilisateurs', 'error');
        }
    }
    
    async loadServers() {
        try {
            const response = await fetch('/api/admin/servers');
            if (!response.ok) throw new Error('Erreur chargement serveurs');
            
            this.servers = await response.json();
            this.renderServersTable();
            
        } catch (error) {
            console.error('Erreur lors du chargement des serveurs:', error);
            this.showNotification('Erreur de chargement des serveurs', 'error');
        }
    }
    
    async loadAuditLogs(page = 1, filters = {}) {
        try {
            const params = new URLSearchParams({
                page,
                per_page: 50,
                ...filters
            });
            
            const response = await fetch(`/api/admin/audit/logs?${params}`);
            if (!response.ok) throw new Error('Erreur chargement logs audit');
            
            const auditData = await response.json();
            this.renderAuditLogs(auditData);
            
        } catch (error) {
            console.error('Erreur lors du chargement des logs audit:', error);
            this.showNotification('Erreur de chargement des logs audit', 'error');
        }
    }
    
    // ================== RENDU DES INTERFACES ==================
    
    renderOverview() {
        const overviewContainer = document.getElementById('admin-overview');
        if (!overviewContainer) return;
        
        const overviewHTML = `
            <div class="row">
                <!-- Statistiques générales -->
                <div class="col-md-3 mb-4">
                    <div class="card bg-primary text-white h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">Serveurs NTP</h6>
                                    <h2 class="mb-0">${this.stats.servers?.total || 0}</h2>
                                    <small>dont ${this.stats.servers?.active || 0} actifs</small>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-server fa-2x"></i>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer bg-primary-dark">
                            <span class="text-success">
                                <i class="fas fa-check-circle"></i>
                                ${this.stats.servers?.active || 0} en ligne
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card bg-success text-white h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">Utilisateurs</h6>
                                    <h2 class="mb-0">${this.stats.users?.total || 0}</h2>
                                    <small>dont ${this.stats.users?.active || 0} actifs</small>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-users fa-2x"></i>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer bg-success-dark">
                            <span class="text-light">
                                <i class="fas fa-user-shield"></i>
                                ${this.stats.users?.admins || 0} administrateurs
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card bg-warning text-white h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">Alertes</h6>
                                    <h2 class="mb-0">${this.stats.alerts?.active || 0}</h2>
                                    <small>${this.stats.alerts?.total || 0} au total</small>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer bg-warning-dark">
                            <span class="text-light">
                                <i class="fas fa-bell"></i>
                                ${this.stats.alerts?.unread || 0} non lues
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3 mb-4">
                    <div class="card bg-info text-white h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">Base de données</h6>
                                    <h2 class="mb-0">${this.formatFileSize(this.stats.database?.size_bytes || 0)}</h2>
                                    <small>Taille actuelle</small>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-database fa-2x"></i>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer bg-info-dark">
                            <span class="text-light">
                                <i class="fas fa-chart-line"></i>
                                Optimale
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Actions rapides -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-bolt me-2"></i>Actions Rapides</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Gestion des données</h6>
                                    <button class="btn btn-outline-primary btn-sm me-2" onclick="adminManager.showExportModal()">
                                        <i class="fas fa-download"></i> Exporter
                                    </button>
                                    <button class="btn btn-outline-secondary btn-sm me-2" onclick="adminManager.showImportModal()">
                                        <i class="fas fa-upload"></i> Importer
                                    </button>
                                    <button class="btn btn-outline-warning btn-sm" onclick="adminManager.showMaintenanceModal()">
                                        <i class="fas fa-tools"></i> Maintenance
                                    </button>
                                </div>
                                <div class="col-md-6">
                                    <h6>Monitoring</h6>
                                    <button class="btn btn-outline-info btn-sm me-2" onclick="adminManager.switchToView('stats')">
                                        <i class="fas fa-chart-bar"></i> Statistiques détaillées
                                    </button>
                                    <button class="btn btn-outline-dark btn-sm" onclick="adminManager.switchToView('audit')">
                                        <i class="fas fa-history"></i> Logs d'audit
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        overviewContainer.innerHTML = overviewHTML;
    }
    
    renderUsersTable() {
        const usersContainer = document.getElementById('admin-users');
        if (!usersContainer) return;
        
        const usersHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5><i class="fas fa-users me-2"></i>Gestion des Utilisateurs</h5>
                    <div>
                        <button class="btn btn-primary btn-sm" onclick="adminManager.showUserModal()">
                            <i class="fas fa-plus"></i> Nouvel utilisateur
                        </button>
                        <button class="btn btn-warning btn-sm" onclick="adminManager.bulkUserAction('deactivate')" 
                                disabled id="bulk-deactivate-btn">
                            <i class="fas fa-user-slash"></i> Désactiver sélection
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped" id="users-table">
                            <thead>
                                <tr>
                                    <th>
                                        <input type="checkbox" id="select-all-users" onchange="adminManager.toggleAllUsers(this)">
                                    </th>
                                    <th>Utilisateur</th>
                                    <th>Email</th>
                                    <th>Rôle</th>
                                    <th>Statut</th>
                                    <th>Dernière connexion</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.users.map(user => this.renderUserRow(user)).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        usersContainer.innerHTML = usersHTML;
        this.initializeDataTable('#users-table');
    }
    
    renderUserRow(user) {
        const statusBadge = user.is_active ? 
            '<span class="badge bg-success">Actif</span>' : 
            '<span class="badge bg-secondary">Inactif</span>';
        
        const roleBadge = this.getRoleBadge(user.role);
        
        const lastLogin = user.last_login ? 
            new Date(user.last_login).toLocaleString() : 
            '<span class="text-muted">Jamais</span>';
        
        return `
            <tr data-user-id="${user.id}">
                <td>
                    <input type="checkbox" class="user-checkbox" value="${user.id}" 
                           onchange="adminManager.updateBulkButtons()">
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="avatar me-2">
                            <div class="avatar-circle bg-primary text-white">
                                ${user.username.charAt(0).toUpperCase()}
                            </div>
                        </div>
                        <div>
                            <strong>${user.username}</strong>
                            ${user.first_name && user.last_name ? 
                                `<br><small class="text-muted">${user.first_name} ${user.last_name}</small>` : ''}
                        </div>
                    </div>
                </td>
                <td>${user.email}</td>
                <td>${roleBadge}</td>
                <td>${statusBadge}</td>
                <td>${lastLogin}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="adminManager.editUser(${user.id})" 
                                title="Modifier">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="adminManager.resetUserPassword(${user.id})" 
                                title="Réinitialiser mot de passe">
                            <i class="fas fa-key"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="adminManager.deleteUser(${user.id})" 
                                title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
    
    renderServersTable() {
        const serversContainer = document.getElementById('admin-servers');
        if (!serversContainer) return;
        
        const serversHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5><i class="fas fa-server me-2"></i>Gestion des Serveurs NTP</h5>
                    <div>
                        <button class="btn btn-primary btn-sm" onclick="adminManager.showServerModal()">
                            <i class="fas fa-plus"></i> Nouveau serveur
                        </button>
                        <button class="btn btn-success btn-sm" onclick="adminManager.testAllServers()">
                            <i class="fas fa-flask"></i> Tester tous
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped" id="servers-table">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Adresse</th>
                                    <th>Type</th>
                                    <th>Statut</th>
                                    <th>Dernière sync</th>
                                    <th>Offset</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.servers.map(server => this.renderServerRow(server)).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        serversContainer.innerHTML = serversHTML;
        this.initializeDataTable('#servers-table');
    }
    
    renderServerRow(server) {
        const statusBadge = this.getServerStatusBadge(server.status);
        const lastSync = server.last_sync ? 
            new Date(server.last_sync).toLocaleString() : 
            '<span class="text-muted">Jamais</span>';
        
        const offset = server.last_offset !== null ? 
            `${server.last_offset.toFixed(3)}s` : 
            '<span class="text-muted">-</span>';
        
        return `
            <tr data-server-id="${server.id}">
                <td>
                    <strong>${server.name}</strong>
                    ${!server.is_active ? '<span class="badge bg-secondary ms-2">Inactif</span>' : ''}
                </td>
                <td>
                    <code>${server.address}:${server.port}</code>
                </td>
                <td>
                    <span class="badge bg-info">${server.server_type}</span>
                </td>
                <td>${statusBadge}</td>
                <td>${lastSync}</td>
                <td>${offset}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-success" onclick="adminManager.testServer(${server.id})" 
                                title="Tester">
                            <i class="fas fa-flask"></i>
                        </button>
                        <button class="btn btn-outline-primary" onclick="adminManager.editServer(${server.id})" 
                                title="Modifier">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="adminManager.deleteServer(${server.id})" 
                                title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
    
    // ================== GESTION DES ÉVÉNEMENTS ==================
    
    setupEventListeners() {
        // Navigation entre les vues
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-admin-view]')) {
                const view = e.target.closest('[data-admin-view]').dataset.adminView;
                this.switchToView(view);
            }
        });
        
        // Recherche en temps réel
        document.addEventListener('input', (e) => {
            if (e.target.matches('.admin-search')) {
                this.handleSearch(e.target.value, e.target.dataset.searchTarget);
            }
        });
    }
    
    setupDataTables() {
        // Configuration DataTables pour les tableaux
        this.dataTableConfig = {
            pageLength: 25,
            responsive: true,
            language: {
                url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/fr-FR.json'
            },
            dom: '<"row"<"col-sm-6"l><"col-sm-6"f>>rtip'
        };
    }
    
    setupAutoRefresh() {
        // Actualisation automatique toutes les 30 secondes
        setInterval(() => {
            if (this.currentView === 'overview') {
                this.loadOverview();
            }
        }, 30000);
    }
    
    // ================== ACTIONS ADMINISTRATIVES ==================
    
    async switchToView(view) {
        this.currentView = view;
        this.updateNavigation(view);
        
        const contentContainer = document.getElementById('admin-content');
        if (!contentContainer) return;
        
        // Afficher le spinner de chargement
        this.showLoadingSpinner(true);
        
        try {
            switch (view) {
                case 'overview':
                    await this.loadOverview();
                    break;
                case 'users':
                    await this.loadUsers();
                    break;
                case 'servers':
                    await this.loadServers();
                    break;
                case 'stats':
                    await this.loadDetailedStats();
                    break;
                case 'audit':
                    await this.loadAuditLogs();
                    break;
                default:
                    console.warn('Vue inconnue:', view);
            }
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    async createUser(userData) {
        try {
            const response = await fetch('/api/admin/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Utilisateur créé avec succès', 'success');
                await this.loadUsers();
                return true;
            } else {
                throw new Error(result.message || 'Erreur lors de la création');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de création: ${error.message}`, 'error');
            return false;
        }
    }
    
    async updateUser(userId, userData) {
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Utilisateur mis à jour avec succès', 'success');
                await this.loadUsers();
                return true;
            } else {
                throw new Error(result.message || 'Erreur lors de la mise à jour');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de mise à jour: ${error.message}`, 'error');
            return false;
        }
    }
    
    async deleteUser(userId) {
        if (!await this.confirmAction('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Utilisateur supprimé avec succès', 'success');
                await this.loadUsers();
            } else {
                throw new Error(result.message || 'Erreur lors de la suppression');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de suppression: ${error.message}`, 'error');
        }
    }
    
    async testServer(serverId) {
        try {
            const response = await fetch(`/api/admin/servers/${serverId}/test`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.connectivity.reachable) {
                this.showNotification('Serveur accessible', 'success');
            } else {
                this.showNotification('Serveur inaccessible', 'warning');
            }
            
            // Afficher les détails dans une modal
            this.showServerTestResults(result);
            
        } catch (error) {
            this.showNotification(`Erreur de test: ${error.message}`, 'error');
        }
    }
    
    async performMaintenance(options) {
        try {
            const response = await fetch('/api/admin/maintenance/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ options })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Maintenance terminée avec succès', 'success');
                this.showMaintenanceResults(result.results);
            } else {
                throw new Error(result.message || 'Erreur lors de la maintenance');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de maintenance: ${error.message}`, 'error');
        }
    }
    
    async exportData(options) {
        try {
            const response = await fetch('/api/admin/backup/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ options })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.downloadJSON(result.data, 'ntp-monitor-export.json');
                this.showNotification('Export généré avec succès', 'success');
            } else {
                throw new Error(result.message || 'Erreur lors de l\'export');
            }
            
        } catch (error) {
            this.showNotification(`Erreur d'export: ${error.message}`, 'error');
        }
    }
    
    // ================== UTILITAIRES ==================
    
    initializeDataTable(selector) {
        if (typeof $ !== 'undefined' && $.fn.DataTable) {
            $(selector).DataTable(this.dataTableConfig);
        }
    }
    
    updateNavigation(activeView) {
        document.querySelectorAll('[data-admin-view]').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-admin-view="${activeView}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
    
    getRoleBadge(role) {
        const badges = {
            'admin': '<span class="badge bg-danger">Administrateur</span>',
            'operator': '<span class="badge bg-warning">Opérateur</span>',
            'viewer': '<span class="badge bg-info">Visualiseur</span>'
        };
        return badges[role] || `<span class="badge bg-secondary">${role}</span>`;
    }
    
    getServerStatusBadge(status) {
        const badges = {
            'ok': '<span class="badge bg-success">OK</span>',
            'warning': '<span class="badge bg-warning">Attention</span>',
            'critical': '<span class="badge bg-danger">Critique</span>',
            'offline': '<span class="badge bg-secondary">Hors ligne</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    async confirmAction(message) {
        return new Promise((resolve) => {
            if (window.confirm(message)) {
                resolve(true);
            } else {
                resolve(false);
            }
        });
    }
    
    showLoadingSpinner(show) {
        const spinner = document.getElementById('admin-loading-spinner');
        if (spinner) {
            spinner.style.display = show ? 'block' : 'none';
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        // Utiliser le système de notifications global
        if (window.showNotification) {
            window.showNotification(message, type, duration);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // Méthodes pour les modals (à implémenter)
    showUserModal(userId = null) {
        // TODO: Implémenter la modal de gestion des utilisateurs
        console.log('Modal utilisateur:', userId);
    }
    
    showServerModal(serverId = null) {
        // TODO: Implémenter la modal de gestion des serveurs
        console.log('Modal serveur:', serverId);
    }
    
    showExportModal() {
        // TODO: Implémenter la modal d'export
        console.log('Modal export');
    }
    
    showImportModal() {
        // TODO: Implémenter la modal d'import
        console.log('Modal import');
    }
    
    showMaintenanceModal() {
        // TODO: Implémenter la modal de maintenance
        console.log('Modal maintenance');
    }
}

// Initialisation globale
let adminManager;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('admin-overview')) {
        adminManager = new AdminManager();
    }
});

// Export pour utilisation externe
window.AdminManager = AdminManager; 