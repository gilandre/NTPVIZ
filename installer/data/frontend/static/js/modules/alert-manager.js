/**
 * Gestionnaire d'alertes - NTP Monitor Enterprise
 * Interface pour la gestion et l'affichage des alertes
 */
class AlertManager {
    constructor() {
        this.alerts = [];
        this.unreadCount = 0;
        this.autoRefresh = true;
        this.refreshInterval = 30000; // 30 secondes
        this.refreshTimer = null;
        
        this.init();
    }
    
    init() {
        console.log('🚨 Initialisation du gestionnaire d\'alertes');
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadAlerts();
    }
    
    setupEventListeners() {
        // Bouton d'actualisation
        $(document).on('click', '[data-action="refresh-alerts"]', () => {
            this.loadAlerts();
        });
        
        // Marquer tout comme lu
        $(document).on('click', '[data-action="mark-all-read"]', () => {
            this.markAllAsRead();
        });
        
        // Actions sur les alertes individuelles
        $(document).on('click', '[data-action="acknowledge-alert"]', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            this.acknowledgeAlert(alertId);
        });
        
        $(document).on('click', '[data-action="resolve-alert"]', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            this.resolveAlert(alertId);
        });
        
        $(document).on('click', '[data-action="mark-read"]', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            this.markAsRead(alertId);
        });
        
        // Filtre de sévérité
        $(document).on('change', '#alert-severity-filter', (e) => {
            this.filterBySeverity($(e.target).val());
        });
        
        // Configuration des alertes
        $(document).on('click', '[data-action="configure-alerts"]', () => {
            this.showConfigModal();
        });
        
        // Actions en lot
        $(document).on('click', '#bulk-action-btn', () => {
            this.performBulkAction();
        });
        
        // Sélection/désélection des alertes
        $(document).on('change', '.alert-checkbox', () => {
            this.updateBulkActions();
        });
        
        $(document).on('change', '#select-all-alerts', (e) => {
            $('.alert-checkbox').prop('checked', e.target.checked);
            this.updateBulkActions();
        });
    }
    
    async loadAlerts() {
        try {
            console.log('🔄 Chargement des alertes...');
            
            const response = await fetch('/api/alerts');
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('⚠️ Endpoint alertes non trouvé, initialisation avec des données vides');
                    this.alerts = [];
                    this.updateAlertsDisplay();
                    this.updateUnreadCount();
                    return;
                }
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.alerts = data.alerts || [];
                this.updateAlertsDisplay();
                this.updateUnreadCount();
                console.log(`✅ ${this.alerts.length} alertes chargées`);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement des alertes');
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement des alertes:', error);
            // Initialiser avec des données vides au lieu de montrer une erreur répétée
            this.alerts = [];
            this.updateAlertsDisplay();
            this.updateUnreadCount();
        }
    }
    
    async loadAlertsSummary() {
        try {
            const response = await fetch('/api/alerts/summary');
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.updateSummaryDisplay(data.summary);
                return data.summary;
            } else {
                throw new Error(data.error || 'Erreur lors du chargement du résumé');
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement du résumé:', error);
            return null;
        }
    }
    
    updateAlertsDisplay() {
        const container = $('#alerts-container');
        if (!container.length) return;
        
        if (this.alerts.length === 0) {
            container.html(`
                <div class="text-center py-5">
                    <i class="fas fa-check-circle text-success fa-3x mb-3"></i>
                    <h5>Aucune alerte active</h5>
                    <p class="text-muted">Tous les serveurs fonctionnent normalement</p>
                </div>
            `);
            return;
        }
        
        const alertsHtml = this.alerts.map(alert => this.createAlertCard(alert)).join('');
        container.html(alertsHtml);
        
        // Mettre à jour les compteurs
        $('#total-alerts-count').text(this.alerts.length);
        $('#critical-alerts-count').text(this.alerts.filter(a => a.severity === 'critical').length);
    }
    
    createAlertCard(alert) {
        const severityClass = this.getSeverityClass(alert.severity);
        const severityIcon = this.getSeverityIcon(alert.severity);
        const timeAgo = this.formatTimeAgo(alert.created_at);
        
        return `
            <div class="alert-card border-left border-${severityClass} ${alert.is_read ? '' : 'alert-unread'}" 
                 data-alert-id="${alert.id}">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="form-check">
                            <input class="form-check-input alert-checkbox" type="checkbox" 
                                   value="${alert.id}" id="alert-${alert.id}">
                            <label class="form-check-label" for="alert-${alert.id}">
                                <span class="badge badge-${severityClass} mr-2">
                                    ${severityIcon} ${alert.severity_label}
                                </span>
                            </label>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                    type="button" data-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-right">
                                ${!alert.acknowledged_at ? `
                                    <a class="dropdown-item" href="#" 
                                       data-action="acknowledge-alert" data-alert-id="${alert.id}">
                                        <i class="fas fa-check mr-2"></i>Acquitter
                                    </a>
                                ` : ''}
                                <a class="dropdown-item" href="#" 
                                   data-action="resolve-alert" data-alert-id="${alert.id}">
                                    <i class="fas fa-times mr-2"></i>Résoudre
                                </a>
                                ${!alert.is_read ? `
                                    <a class="dropdown-item" href="#" 
                                       data-action="mark-read" data-alert-id="${alert.id}">
                                        <i class="fas fa-eye mr-2"></i>Marquer comme lu
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                    
                    <h6 class="card-title mb-2">${alert.title}</h6>
                    <p class="card-text text-muted mb-2">${alert.message}</p>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">
                                <i class="fas fa-server mr-1"></i>
                                ${alert.server_name || 'Système'}
                            </small>
                        </div>
                        <div class="col-md-6 text-right">
                            <small class="text-muted">
                                <i class="fas fa-clock mr-1"></i>
                                ${timeAgo}
                            </small>
                        </div>
                    </div>
                    
                    ${alert.details ? `
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-info" type="button" 
                                    data-toggle="collapse" data-target="#details-${alert.id}">
                                <i class="fas fa-info-circle mr-1"></i>Détails
                            </button>
                            <div class="collapse mt-2" id="details-${alert.id}">
                                <div class="card card-body">
                                    <pre class="mb-0">${JSON.stringify(alert.details, null, 2)}</pre>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${alert.acknowledged_at ? `
                        <div class="mt-2">
                            <span class="badge badge-info">
                                <i class="fas fa-check mr-1"></i>
                                Acquittée le ${new Date(alert.acknowledged_at).toLocaleString()}
                            </span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    updateSummaryDisplay(summary) {
        // Mettre à jour les badges dans la navigation
        $('.alerts-count-badge').text(summary.total_active || 0);
        
        // Mettre à jour les widgets du dashboard
        $('#total-alerts').text(summary.total_active || 0);
        $('#critical-alerts').text(summary.by_severity.critical || 0);
        $('#warning-alerts').text(summary.by_severity.warning || 0);
        $('#unread-alerts').text(summary.unread_count || 0);
        
        // Mettre à jour l'indicateur de santé
        this.updateHealthIndicator(summary);
    }
    
    updateHealthIndicator(summary) {
        const healthIndicator = $('#system-health-indicator');
        if (!healthIndicator.length) return;
        
        let healthClass = 'success';
        let healthText = 'Système sain';
        let healthIcon = 'check-circle';
        
        if (summary.by_severity.critical > 0) {
            healthClass = 'danger';
            healthText = 'Alertes critiques';
            healthIcon = 'exclamation-triangle';
        } else if (summary.by_severity.error > 0) {
            healthClass = 'warning';
            healthText = 'Problèmes détectés';
            healthIcon = 'exclamation-circle';
        } else if (summary.by_severity.warning > 0) {
            healthClass = 'info';
            healthText = 'Avertissements';
            healthIcon = 'info-circle';
        }
        
        healthIndicator.html(`
            <span class="badge badge-${healthClass}">
                <i class="fas fa-${healthIcon} mr-1"></i>
                ${healthText}
            </span>
        `);
    }
    
    updateUnreadCount() {
        this.unreadCount = this.alerts.filter(alert => !alert.is_read).length;
        $('.unread-alerts-count').text(this.unreadCount);
        
        // Animer le badge si il y a des alertes non lues
        if (this.unreadCount > 0) {
            $('.alerts-count-badge').addClass('badge-pulse');
        } else {
            $('.alerts-count-badge').removeClass('badge-pulse');
        }
    }
    
    updateBulkActions() {
        const checkedAlerts = $('.alert-checkbox:checked').length;
        const bulkActions = $('#bulk-actions');
        
        if (checkedAlerts > 0) {
            bulkActions.show();
            $('#selected-count').text(checkedAlerts);
        } else {
            bulkActions.hide();
        }
    }
    
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            if (data.success) {
                if (window.notificationSystem) {
                    window.notificationSystem.show('Alerte acquittée', 'success');
                }
                this.loadAlerts(); // Recharger les alertes
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur lors de l\'acquittement:', error);
            if (window.notificationSystem) {
                window.notificationSystem.show('Erreur lors de l\'acquittement', 'error');
            }
        }
    }
    
    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            if (data.success) {
                if (window.notificationSystem) {
                    window.notificationSystem.show('Alerte résolue', 'success');
                }
                this.loadAlerts(); // Recharger les alertes
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur lors de la résolution:', error);
            if (window.notificationSystem) {
                window.notificationSystem.show('Erreur lors de la résolution', 'error');
            }
        }
    }
    
    async markAsRead(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/read`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            if (data.success) {
                this.loadAlerts(); // Recharger les alertes
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du marquage:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/alerts/mark-all-read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            if (data.success) {
                if (window.notificationSystem) {
                    window.notificationSystem.show('Toutes les alertes marquées comme lues', 'success');
                }
                this.loadAlerts(); // Recharger les alertes
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du marquage global:', error);
            if (window.notificationSystem) {
                window.notificationSystem.show('Erreur lors du marquage', 'error');
            }
        }
    }
    
    async performBulkAction() {
        const selectedAlerts = $('.alert-checkbox:checked').map(function() {
            return parseInt($(this).val());
        }).get();
        
        const action = $('#bulk-action-select').val();
        
        if (selectedAlerts.length === 0 || !action) {
            if (window.notificationSystem) {
                window.notificationSystem.show('Sélectionnez des alertes et une action', 'warning');
            }
            return;
        }
        
        try {
            const response = await fetch('/api/alerts/bulk-action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    alert_ids: selectedAlerts,
                    action: action
                })
            });
            
            const data = await response.json();
            if (data.success) {
                if (window.notificationSystem) {
                    window.notificationSystem.show(data.message, 'success');
                }
                this.loadAlerts(); // Recharger les alertes
                this.updateBulkActions(); // Masquer les actions en lot
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur lors de l\'action en lot:', error);
            if (window.notificationSystem) {
                window.notificationSystem.show('Erreur lors de l\'action en lot', 'error');
            }
        }
    }
    
    filterBySeverity(severity) {
        if (!severity || severity === 'all') {
            $('.alert-card').show();
            return;
        }
        
        $('.alert-card').each(function() {
            const alertSeverity = $(this).find('.badge').text().toLowerCase();
            if (alertSeverity.includes(severity)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }
    
    getSeverityClass(severity) {
        const classes = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'critical': 'danger'
        };
        return classes[severity] || 'secondary';
    }
    
    getSeverityIcon(severity) {
        const icons = {
            'info': '<i class="fas fa-info-circle"></i>',
            'warning': '<i class="fas fa-exclamation-triangle"></i>',
            'error': '<i class="fas fa-exclamation-circle"></i>',
            'critical': '<i class="fas fa-skull-crossbones"></i>'
        };
        return icons[severity] || '<i class="fas fa-bell"></i>';
    }
    
    formatTimeAgo(timestamp) {
        const now = new Date();
        const alertTime = new Date(timestamp);
        const diff = Math.floor((now - alertTime) / 1000);
        
        if (diff < 60) return 'Il y a moins d\'une minute';
        if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} minutes`;
        if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)} heures`;
        return `Il y a ${Math.floor(diff / 86400)} jours`;
    }
    
    startAutoRefresh() {
        if (this.autoRefresh && !this.refreshTimer) {
            this.refreshTimer = setInterval(() => {
                this.loadAlerts();
            }, this.refreshInterval);
            console.log(`🔄 Auto-actualisation des alertes activée (${this.refreshInterval/1000}s)`);
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('⏹️ Auto-actualisation des alertes arrêtée');
        }
    }
    
    showConfigModal() {
        // Cette méthode sera étendue pour afficher la modal de configuration
        console.log('🛠️ Configuration des alertes (à implémenter)');
        if (window.notificationSystem) {
            window.notificationSystem.show('Configuration des alertes en cours de développement', 'info');
        }
    }
    
    // Méthode pour l'intégration avec le dashboard
    async getDashboardData() {
        const summary = await this.loadAlertsSummary();
        return {
            total_active: summary?.total_active || 0,
            critical: summary?.by_severity?.critical || 0,
            warning: summary?.by_severity?.warning || 0,
            info: summary?.by_severity?.info || 0,
            unread: summary?.unread_count || 0,
            recent: summary?.recent_alerts || []
        };
    }
}

// Export pour utilisation globale
window.AlertManager = AlertManager;

// Instance globale automatique
document.addEventListener('DOMContentLoaded', function() {
    if (!window.alertManager) {
        window.alertManager = new AlertManager();
        console.log(' Instance globale alertManager cr��e');
    }
}); 
