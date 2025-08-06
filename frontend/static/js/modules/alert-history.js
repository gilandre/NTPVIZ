/**
 * NTP Monitor Enterprise - Module d'Historique des Alertes
 * Gestion de l'historique des alertes résolues et inactives
 */

class AlertHistoryManager {
    constructor() {
        this.alerts = [];
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.totalPages = 1;
        this.totalItems = 0;
        this.filters = {
            status: 'all',
            severity: 'all',
            server_id: 'all',
            date_range: '7d'
        };
        this.isLoading = false;
    }

    init() {
        this.setupEventListeners();
        this.initializeFilters();
        this.loadAlertHistory();
    }

    setupEventListeners() {
        // Filtres
        $(document).on('change', '#history-status-filter', (e) => {
            this.filters.status = $(e.target).val();
            this.currentPage = 1;
            this.loadAlertHistory();
        });

        $(document).on('change', '#history-severity-filter', (e) => {
            this.filters.severity = $(e.target).val();
            this.currentPage = 1;
            this.loadAlertHistory();
        });

        $(document).on('change', '#history-server-filter', (e) => {
            this.filters.server_id = $(e.target).val();
            this.currentPage = 1;
            this.loadAlertHistory();
        });

        $(document).on('change', '#history-date-range', (e) => {
            this.filters.date_range = $(e.target).val();
            this.currentPage = 1;
            this.loadAlertHistory();
        });

        // Pagination
        $(document).on('click', '.history-pagination .page-link', (e) => {
            e.preventDefault();
            const page = parseInt($(e.target).data('page'));
            if (page && page !== this.currentPage) {
                this.currentPage = page;
                this.loadAlertHistory();
            }
        });

        // Actions sur les alertes
        $(document).on('click', '[data-action="view-alert-history"]', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            this.showAlertHistoryDetails(alertId);
        });

        $(document).on('click', '[data-action="delete-alert-history"]', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            this.deleteAlertFromHistory(alertId);
        });

        // Recherche
        $(document).on('input', '#history-search', (e) => {
            const query = $(e.target).val();
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchAlertHistory(query);
            }, 300);
        });

        // Export
        $(document).on('click', '[data-action="export-history"]', () => {
            this.exportAlertHistory();
        });
    }

    initializeFilters() {
        // Charger la liste des serveurs pour le filtre
        this.loadServersList();
    }

    async loadServersList() {
        try {
            const response = await fetch('/api/ntp/servers');
            const data = await response.json();
            
            if (data.success && data.servers) {
                const serverFilter = $('#history-server-filter');
                serverFilter.empty();
                serverFilter.append('<option value="all">Tous les serveurs</option>');
                
                data.servers.forEach(server => {
                    serverFilter.append(`<option value="${server.id}">${server.name}</option>`);
                });
            }
        } catch (error) {
            console.error('Erreur chargement serveurs:', error);
        }
    }

    async loadAlertHistory() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.itemsPerPage,
                status: this.filters.status,
                severity: this.filters.severity,
                server_id: this.filters.server_id,
                date_range: this.filters.date_range
            });

            const response = await fetch(`/api/alerts/history?${params}`);
            const data = await response.json();

            if (data.success) {
                this.alerts = data.alerts || [];
                this.totalItems = data.pagination.total || 0;
                this.totalPages = data.pagination.pages || 1;
                this.currentPage = data.pagination.page || 1;

                this.updateHistoryDisplay();
                this.updatePagination();
                this.updateStatistics(data.stats);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement de l\'historique');
            }
        } catch (error) {
            console.error('Erreur chargement historique:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    updateHistoryDisplay() {
        const container = $('#alert-history-container');
        if (!container.length) return;

        if (this.alerts.length === 0) {
            container.html(`
                <div class="text-center py-5">
                    <i class="fas fa-history text-muted fa-3x mb-3"></i>
                    <h5>Aucun historique d'alerte</h5>
                    <p class="text-muted">Aucune alerte correspondant aux filtres sélectionnés</p>
                </div>
            `);
            return;
        }

        const alertsHtml = this.alerts.map(alert => this.createHistoryCard(alert)).join('');
        container.html(alertsHtml);
    }

    createHistoryCard(alert) {
        const severityClass = this.getSeverityClass(alert.severity);
        const severityIcon = this.getSeverityIcon(alert.severity);
        const severityLabel = this.getSeverityLabel(alert.severity);
        const statusClass = this.getStatusClass(alert.status);
        const statusIcon = this.getStatusIcon(alert.status);
        const statusLabel = this.getStatusLabel(alert.status);
        
        const createdAt = new Date(alert.created_at).toLocaleString('fr-FR');
        const resolvedAt = alert.resolved_at ? new Date(alert.resolved_at).toLocaleString('fr-FR') : null;
        const duration = this.calculateDuration(alert.created_at, alert.resolved_at);
        
        const serverName = alert.server_name || 'Système';
        const alertTitle = alert.title || 'Alerte';
        const alertMessage = alert.message || 'Aucun message';
        
        return `
            <div class="alert-history-card card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <span class="badge bg-${severityClass} text-dark me-2">
                                ${severityIcon} ${severityLabel}
                            </span>
                            <span class="badge bg-${statusClass} text-dark">
                                ${statusIcon} ${statusLabel}
                            </span>
                            ${alert.occurrence_count > 1 ? `
                                <span class="badge bg-info text-dark ms-1" title="Nombre d'occurrences">
                                    <i class="fas fa-redo me-1"></i>${alert.occurrence_count}
                                </span>
                            ` : ''}
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                    type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="#" 
                                       data-action="view-alert-history" data-alert-id="${alert.id}">
                                    <i class="fas fa-eye me-2"></i>Voir les détails
                                </a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="#" 
                                       data-action="delete-alert-history" data-alert-id="${alert.id}">
                                    <i class="fas fa-trash me-2"></i>Supprimer
                                </a></li>
                            </ul>
                        </div>
                    </div>
                    
                    <h6 class="card-title mb-2">${alertTitle}</h6>
                    <p class="card-text text-muted mb-3">${alertMessage}</p>
                    
                    <div class="row">
                        <div class="col-md-3">
                            <small class="text-muted">
                                <i class="fas fa-server me-1"></i>
                                <strong>Serveur:</strong> ${serverName}
                            </small>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">
                                <i class="fas fa-calendar-plus me-1"></i>
                                <strong>Créée:</strong> ${createdAt}
                            </small>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">
                                <i class="fas fa-calendar-check me-1"></i>
                                <strong>Résolue:</strong> ${resolvedAt || 'N/A'}
                            </small>
                        </div>
                        <div class="col-md-3">
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>
                                <strong>Durée:</strong> ${duration}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updatePagination() {
        const paginationContainer = $('#history-pagination');
        if (!paginationContainer.length) return;

        if (this.totalPages <= 1) {
            paginationContainer.hide();
            return;
        }

        paginationContainer.show();
        
        let paginationHtml = '<nav><ul class="pagination justify-content-center history-pagination">';
        
        // Bouton précédent
        if (this.currentPage > 1) {
            paginationHtml += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">Précédent</a>
            </li>`;
        }
        
        // Pages
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === this.currentPage ? 'active' : '';
            paginationHtml += `<li class="page-item ${isActive}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }
        
        // Bouton suivant
        if (this.currentPage < this.totalPages) {
            paginationHtml += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">Suivant</a>
            </li>`;
        }
        
        paginationHtml += '</ul></nav>';
        paginationContainer.html(paginationHtml);
    }

    updateStatistics(stats) {
        if (!stats) return;

        $('#history-total-count').text(stats.total || 0);
        $('#history-resolved-count').text(stats.resolved || 0);
        $('#history-acknowledged-count').text(stats.acknowledged || 0);
        $('#history-deleted-count').text(stats.deleted || 0);
    }

    calculateDuration(startDate, endDate) {
        if (!startDate || !endDate) return 'N/A';
        
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffMs = end - start;
        
        const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (days > 0) return `${days}j ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    }

    showLoadingState() {
        const container = $('#alert-history-container');
        container.html(`
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
                <p class="mt-2 text-muted">Chargement de l'historique...</p>
            </div>
        `);
    }

    hideLoadingState() {
        // Géré par updateHistoryDisplay
    }

    showErrorState(message) {
        const container = $('#alert-history-container');
        container.html(`
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-warning fa-3x mb-3"></i>
                <h5>Erreur de chargement</h5>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="window.alertHistoryManager.loadAlertHistory()">
                    <i class="fas fa-redo me-1"></i>Réessayer
                </button>
            </div>
        `);
    }

    // Méthodes utilitaires (similaires à AlertManager)
    getSeverityClass(severity) {
        switch (severity) {
            case 'critical': return 'danger';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'secondary';
        }
    }

    getSeverityIcon(severity) {
        switch (severity) {
            case 'critical': return '<i class="fas fa-exclamation-triangle"></i>';
            case 'warning': return '<i class="fas fa-exclamation-circle"></i>';
            case 'info': return '<i class="fas fa-info-circle"></i>';
            default: return '<i class="fas fa-bell"></i>';
        }
    }

    getSeverityLabel(severity) {
        switch (severity) {
            case 'critical': return 'Critique';
            case 'warning': return 'Avertissement';
            case 'info': return 'Information';
            default: return 'Inconnu';
        }
    }

    getStatusClass(status) {
        switch (status) {
            case 'resolved': return 'success';
            case 'acknowledged': return 'info';
            case 'deleted': return 'dark';
            default: return 'secondary';
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'resolved': return '<i class="fas fa-check-double"></i>';
            case 'acknowledged': return '<i class="fas fa-check"></i>';
            case 'deleted': return '<i class="fas fa-trash"></i>';
            default: return '<i class="fas fa-question"></i>';
        }
    }

    getStatusLabel(status) {
        switch (status) {
            case 'resolved': return 'Résolue';
            case 'acknowledged': return 'Acquittée';
            case 'deleted': return 'Supprimée';
            default: return 'Inconnu';
        }
    }

    async showAlertHistoryDetails(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}`);
            const data = await response.json();
            
            if (data.success) {
                this.openHistoryDetailModal(data.alert);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement des détails');
            }
        } catch (error) {
            console.error('Erreur détails historique:', error);
            alert('Erreur lors du chargement des détails: ' + error.message);
        }
    }

    openHistoryDetailModal(alertData) {
        // Réutiliser le modal existant ou en créer un nouveau
        let modal = $('#alertHistoryDetailModal');
        if (!modal.length) {
            modal = this.createHistoryDetailModal();
            $('body').append(modal);
        }

        this.populateHistoryDetailModal(modal, alertData);
        
        const bootstrapModal = new bootstrap.Modal(modal[0]);
        bootstrapModal.show();
    }

    createHistoryDetailModal() {
        return $(`
            <div class="modal fade" id="alertHistoryDetailModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Détails de l'alerte historique</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="alertHistoryDetailBody">
                            <!-- Contenu dynamique -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    populateHistoryDetailModal(modal, alertData) {
        const modalBody = modal.find('#alertHistoryDetailBody');
        
        // Utiliser la même logique que pour les alertes actives
        const severityClass = this.getSeverityClass(alertData.severity);
        const createdAt = new Date(alertData.created_at).toLocaleString('fr-FR');
        const resolvedAt = alertData.resolved_at ? new Date(alertData.resolved_at).toLocaleString('fr-FR') : null;
        const duration = this.calculateDuration(alertData.created_at, alertData.resolved_at);
        
        modalBody.html(`
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card border-${severityClass}">
                        <div class="card-header bg-${severityClass} text-white">
                            <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Informations générales</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Type :</strong> ${alertData.alert_type || 'N/A'}</p>
                            <p><strong>Sévérité :</strong> ${this.getSeverityLabel(alertData.severity)}</p>
                            <p><strong>Statut :</strong> ${this.getStatusLabel(alertData.status)}</p>
                            <p><strong>Créée le :</strong> ${createdAt}</p>
                            <p><strong>Résolue le :</strong> ${resolvedAt || 'N/A'}</p>
                            <p><strong>Durée :</strong> ${duration}</p>
                            ${alertData.occurrence_count > 1 ? `<p><strong>Occurrences :</strong> ${alertData.occurrence_count}</p>` : ''}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0"><i class="fas fa-server me-2"></i>Serveur associé</h6>
                        </div>
                        <div class="card-body">
                            ${alertData.server_name ? `
                                <p><strong>Nom :</strong> ${alertData.server_name}</p>
                                <p><strong>ID :</strong> ${alertData.server_id}</p>
                            ` : '<p class="text-muted">Aucun serveur associé</p>'}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0"><i class="fas fa-comment me-2"></i>Message</h6>
                        </div>
                        <div class="card-body">
                            <p>${alertData.message || 'Aucun message'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    async exportAlertHistory() {
        try {
            const params = new URLSearchParams(this.filters);
            const response = await fetch(`/api/alerts/history/export?${params}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `alert-history-${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                throw new Error('Erreur lors de l\'export');
            }
        } catch (error) {
            console.error('Erreur export:', error);
            alert('Erreur lors de l\'export: ' + error.message);
        }
    }
}

// Initialisation globale
window.alertHistoryManager = new AlertHistoryManager();

// Auto-initialisation
$(document).ready(() => {
    if ($('#alert-history-container').length) {
        window.alertHistoryManager.init();
    }
}); 