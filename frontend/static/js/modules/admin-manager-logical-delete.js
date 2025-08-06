class AdminManager {
    constructor() {
        this.servers = [];
        this.users = [];
        this.currentView = 'servers';
        this.showDeletedServers = false; // Nouveau: affichage des serveurs supprimés
        
        this.init();
    }
    
    init() {
        this.loadServers();
        this.loadUsers();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Toggle pour afficher/masquer les serveurs supprimés
        const toggleDeletedBtn = document.getElementById('toggle-deleted-servers');
        if (toggleDeletedBtn) {
            toggleDeletedBtn.addEventListener('click', () => {
                this.showDeletedServers = !this.showDeletedServers;
                this.loadServers();
                this.updateToggleButton();
            });
        }
    }
    
    updateToggleButton() {
        const toggleDeletedBtn = document.getElementById('toggle-deleted-servers');
        if (toggleDeletedBtn) {
            const icon = this.showDeletedServers ? 'fa-eye-slash' : 'fa-eye';
            const text = this.showDeletedServers ? 'Masquer supprimés' : 'Afficher supprimés';
            toggleDeletedBtn.innerHTML = `<i class="fas ${icon}"></i> ${text}`;
        }
    }
    
    async loadServers() {
        try {
            const response = await fetch('/api/admin/servers');
            if (!response.ok) throw new Error('Erreur chargement serveurs');
            
            this.servers = await response.json();
            
            // Filtrer selon l'option d'affichage
            if (!this.showDeletedServers) {
                this.servers = this.servers.filter(server => !server.is_deleted);
            }
            
            this.renderServersTable();
            this.updateToggleButton();
            
        } catch (error) {
            console.error('Erreur lors du chargement des serveurs:', error);
            this.showNotification('Erreur de chargement des serveurs', 'error');
        }
    }
    
    renderServersTable() {
        const tbody = document.querySelector('#servers-table tbody');
        if (!tbody) return;
        
        if (this.servers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Aucun serveur trouvé</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.servers.map(server => this.renderServerRow(server)).join('');
    }
    
    renderServerRow(server) {
        const statusBadge = this.getServerStatusBadge(server.status);
        const lastSync = server.last_sync ? 
            new Date(server.last_sync).toLocaleString() : 
            '<span class="text-muted">Jamais</span>';
        
        const offset = server.last_offset !== null ? 
            `${server.last_offset.toFixed(3)}s` : 
            '<span class="text-muted">-</span>';
        
        // Indicateur de suppression logique
        const deletedIndicator = server.is_deleted ? 
            '<span class="badge bg-danger ms-2">Supprimé</span>' : '';
        
        const inactiveIndicator = !server.is_active && !server.is_deleted ? 
            '<span class="badge bg-secondary ms-2">Inactif</span>' : '';
        
        const actionButtons = this.getServerActionButtons(server);
        
        return `
            <tr data-server-id="${server.id}" class="${server.is_deleted ? 'table-danger' : ''}">
                <td>
                    <strong>${server.name}</strong>
                    ${deletedIndicator}
                    ${inactiveIndicator}
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
                        ${actionButtons}
                    </div>
                </td>
            </tr>
        `;
    }
    
    getServerActionButtons(server) {
        if (server.is_deleted) {
            // Serveur supprimé: bouton de restauration
            return `
                <button class="btn btn-outline-success" onclick="adminManager.restoreServer(${server.id})" 
                        title="Restaurer">
                    <i class="fas fa-undo"></i>
                </button>
                <button class="btn btn-outline-info" onclick="adminManager.viewServerHistory(${server.id})" 
                        title="Historique">
                    <i class="fas fa-history"></i>
                </button>
            `;
        } else {
            // Serveur actif: boutons normaux
            return `
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
            `;
        }
    }
    
    async deleteServer(serverId) {
        if (!await this.confirmAction('Êtes-vous sûr de vouloir supprimer ce serveur ? Cette action est réversible.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/servers/${serverId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Serveur supprimé avec succès', 'success');
                await this.loadServers();
            } else {
                throw new Error(result.message || 'Erreur lors de la suppression');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de suppression: ${error.message}`, 'error');
        }
    }
    
    async restoreServer(serverId) {
        if (!await this.confirmAction('Êtes-vous sûr de vouloir restaurer ce serveur ?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/servers/${serverId}/restore`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Serveur restauré avec succès', 'success');
                await this.loadServers();
            } else {
                throw new Error(result.message || 'Erreur lors de la restauration');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de restauration: ${error.message}`, 'error');
        }
    }
    
    async viewServerHistory(serverId) {
        try {
            const server = this.servers.find(s => s.id === serverId);
            if (!server) return;
            
            // Afficher les détails du serveur supprimé
            const modal = document.getElementById('serverHistoryModal');
            if (modal) {
                const modalBody = modal.querySelector('.modal-body');
                modalBody.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Informations du serveur</h6>
                            <p><strong>Nom:</strong> ${server.name}</p>
                            <p><strong>Adresse:</strong> ${server.address}:${server.port}</p>
                            <p><strong>Type:</strong> ${server.server_type}</p>
                            <p><strong>Supprimé le:</strong> ${new Date(server.deleted_at).toLocaleString()}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Statistiques</h6>
                            <p><strong>Dernière synchronisation:</strong> ${server.last_sync ? new Date(server.last_sync).toLocaleString() : 'Jamais'}</p>
                            <p><strong>Dernier offset:</strong> ${server.last_offset ? server.last_offset.toFixed(3) + 's' : 'N/A'}</p>
                            <p><strong>Status:</strong> ${server.status}</p>
                        </div>
                    </div>
                    <div class="mt-3">
                        <h6>Actions</h6>
                        <button class="btn btn-success btn-sm" onclick="adminManager.restoreServer(${server.id})">
                            <i class="fas fa-undo"></i> Restaurer le serveur
                        </button>
                    </div>
                `;
                
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
            }
            
        } catch (error) {
            this.showNotification(`Erreur lors de l'affichage de l'historique: ${error.message}`, 'error');
        }
    }
    
    // ... autres méthodes existantes ...
    
    showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alert, container.firstChild);
            
            // Auto-dismiss après 5 secondes
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }
    
    async confirmAction(message) {
        return new Promise((resolve) => {
            if (confirm(message)) {
                resolve(true);
            } else {
                resolve(false);
            }
        });
    }
}

// Initialisation globale
let adminManager;
document.addEventListener('DOMContentLoaded', () => {
    adminManager = new AdminManager();
});
