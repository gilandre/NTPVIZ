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
        
        // Filtres
        $(document).on('change', '#alert-severity-filter', (e) => {
            this.filterBySeverity($(e.target).val());
        });
        
        // 🔧 NOUVEAU: Recherche en temps réel
        $(document).on('input', '#alert-search', (e) => {
            const query = $(e.target).val();
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchAlerts(query);
            }, 300); // Délai de 300ms pour éviter trop de requêtes
        });
        
        // 🔧 NOUVEAU: Raccourcis clavier
        $(document).on('keydown', '#alert-search', (e) => {
            if (e.key === 'Escape') {
                $(e.target).val('');
                this.searchAlerts('');
            }
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
            this.updateSelectedCount();
        });
        
        $(document).on('change', '#select-all-alerts', (e) => {
            $('.alert-checkbox').prop('checked', e.target.checked);
            this.updateBulkActions();
            this.updateSelectedCount();
        });
        
        // 🔧 NOUVEAU: Double-clic pour voir les détails
        $(document).on('dblclick', '.alert-card', (e) => {
            const alertId = $(e.currentTarget).data('alert-id');
            if (alertId) {
                this.showAlertDetails(alertId);
            }
        });
        
        // 🔧 NOUVEAU: Actions rapides avec raccourcis clavier dans le modal
        $(document).on('keydown', (e) => {
            // Seulement si le modal des alertes est ouvert
            if ($('#alertsModal').hasClass('show')) {
                switch(e.key) {
                    case 'r': // Refresh
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            this.loadAlerts();
                        }
                        break;
                    case 'a': // Select All
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            $('#select-all-alerts').prop('checked', true).trigger('change');
                        }
                        break;
                    case 'Escape': // Clear selection
                        $('.alert-checkbox').prop('checked', false);
                        $('#select-all-alerts').prop('checked', false);
                        this.updateBulkActions();
                        this.updateSelectedCount();
                        break;
                }
            }
        });
        
        // 🔧 NOUVEAU: Mise à jour en temps réel des compteurs
        $(document).on('alertsUpdated', () => {
            this.updateStatistics();
        });
    }
    
    async loadAlerts() {
        try {
            console.log('🔄 Chargement des alertes actives...');
            
            // Charger uniquement les alertes actives
            const response = await fetch('/api/alerts/active');
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
                console.log(`✅ ${this.alerts.length} alertes actives chargées`);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement des alertes actives');
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement des alertes actives:', error);
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
                    <small class="text-muted">Les alertes résolues et acquittées sont consultables dans le module d'historique</small>
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
        const severityLabel = this.getSeverityLabel(alert.severity);
        const timeAgo = this.formatTimeAgo(alert.created_at);
        
        // Gérer correctement les valeurs undefined/null
        const serverName = alert.server_name && alert.server_name !== 'undefined' ? alert.server_name : 'Système';
        const alertTitle = alert.title && alert.title !== 'undefined' ? alert.title : 'Alerte';
        const alertMessage = alert.message && alert.message !== 'undefined' ? alert.message : 'Aucun message';
        
        // Calcul des informations d'occurrence
        const occurrenceCount = alert.occurrence_count || 1;
        const firstOccurrence = alert.first_occurrence || alert.created_at;
        const lastOccurrence = alert.last_occurrence || alert.updated_at || alert.created_at;
        
        // Calcul de la durée depuis la première occurrence
        let durationText = '';
        if (firstOccurrence && lastOccurrence && firstOccurrence !== lastOccurrence) {
            const firstDate = new Date(firstOccurrence);
            const lastDate = new Date(lastOccurrence);
            const diffHours = Math.floor((lastDate - firstDate) / (1000 * 60 * 60));
            const diffDays = Math.floor(diffHours / 24);
            
            if (diffDays > 0) {
                durationText = `${diffDays} jour(s)`;
            } else if (diffHours > 0) {
                durationText = `${diffHours} heure(s)`;
            } else {
                durationText = 'Récente';
            }
        }
        
        return `
            <div class="alert-card border-start border-${severityClass} ${alert.is_read ? '' : 'alert-unread'}" 
                 data-alert-id="${alert.id}" ondblclick="window.alertManager.showAlertDetails(${alert.id})">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="form-check">
                            <input class="form-check-input alert-checkbox" type="checkbox" 
                                   value="${alert.id}" id="alert-${alert.id}">
                            <label class="form-check-label" for="alert-${alert.id}">
                                <span class="badge bg-${severityClass} text-dark me-2">
                                    ${severityIcon} ${severityLabel}
                                </span>
                                ${occurrenceCount > 1 ? `
                                    <span class="badge bg-info text-dark ms-1" title="Nombre d'occurrences">
                                        <i class="fas fa-redo me-1"></i>${occurrenceCount}
                                    </span>
                                ` : ''}
                            </label>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                    type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="#" onclick="window.alertManager.showAlertDetails(${alert.id})">
                                    <i class="fas fa-eye me-2"></i>Voir les détails
                                </a></li>
                                <li><hr class="dropdown-divider"></li>
                                ${!alert.acknowledged_at ? `
                                    <li><a class="dropdown-item" href="#" 
                                       data-action="acknowledge-alert" data-alert-id="${alert.id}">
                                        <i class="fas fa-check me-2"></i>Acquitter
                                    </a></li>
                                ` : ''}
                                <li><a class="dropdown-item" href="#" 
                                   data-action="resolve-alert" data-alert-id="${alert.id}">
                                    <i class="fas fa-times me-2"></i>Résoudre
                                </a></li>
                                ${!alert.is_read ? `
                                    <li><a class="dropdown-item" href="#" 
                                       data-action="mark-read" data-alert-id="${alert.id}">
                                        <i class="fas fa-eye me-2"></i>Marquer comme lu
                                    </a></li>
                                ` : ''}
                            </ul>
                        </div>
                    </div>
                    
                    <h6 class="card-title mb-2">${alertTitle}</h6>
                    <p class="card-text text-muted mb-2">${alertMessage}</p>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">
                                <i class="fas fa-server me-1"></i>
                                ${serverName}
                            </small>
                        </div>
                        <div class="col-md-6 text-end">
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>
                                ${timeAgo}
                            </small>
                        </div>
                    </div>
                    
                    ${occurrenceCount > 1 || durationText ? `
                        <div class="mt-2">
                            <small class="text-info">
                                ${occurrenceCount > 1 ? `
                                    <i class="fas fa-history me-1"></i>
                                    ${occurrenceCount} occurrences
                                ` : ''}
                                ${durationText ? `
                                    <span class="ms-2">
                                        <i class="fas fa-hourglass-half me-1"></i>
                                        Active depuis ${durationText}
                                    </span>
                                ` : ''}
                            </small>
                        </div>
                    ` : ''}
                    
                    <div class="mt-2 d-flex justify-content-between align-items-center">
                        <div>
                            ${alert.acknowledged_at ? `
                                <span class="badge bg-info text-dark">
                                    <i class="fas fa-check me-1"></i>
                                    Acquittée
                                </span>
                            ` : ''}
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="window.alertManager.showAlertDetails(${alert.id})" title="Voir les détails">
                            <i class="fas fa-info-circle me-1"></i>Détails
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateSummaryDisplay(summary) {
        // ✅ Mise à jour RESTREINTE aux sections appropriées uniquement
        
        // Badge navigation (section appropriée)
        const navBadges = document.querySelectorAll('.alerts-count-badge');
        navBadges.forEach(badge => {
            // Vérifier que le badge n'est pas dans une section serveurs
            const isInServerSection = badge.closest('#ntp-servers-clocks') !== null || 
                                    badge.closest('#servers-summary') !== null ||
                                    badge.closest('.server-card') !== null;
            
            if (!isInServerSection) {
                badge.textContent = summary.active_alerts || 0;
            }
        });
        
        // Widgets du dashboard (sections appropriées)
        $('#dashboard-alerts-count').text(summary.active_alerts || 0);
        $('#total-alerts').text(summary.active_alerts || 0);
        $('#critical-alerts').text(summary.by_severity?.critical?.active || 0);
        $('#warning-alerts').text(summary.by_severity?.warning?.active || 0);
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
        
        if (summary.by_severity?.critical?.active > 0) {
            healthClass = 'danger';
            healthText = 'Alertes critiques';
            healthIcon = 'exclamation-triangle';
        } else if (summary.by_severity?.error?.active > 0) {
            healthClass = 'warning';
            healthText = 'Problèmes détectés';
            healthIcon = 'exclamation-circle';
        } else if (summary.by_severity?.warning?.active > 0) {
            healthClass = 'info';
            healthText = 'Avertissements';
            healthIcon = 'info-circle';
        }
        
        healthIndicator.html(`
            <span class="badge bg-${healthClass}">
                <i class="fas fa-${healthIcon} me-1"></i>
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
        console.log(`🔍 Filtrage par sévérité: ${severity}`);
        
        if (!severity || severity === 'all') {
            $('.alert-card').show();
            $('#alert-severity-filter').val('all');
            return;
        }
        
        let visibleCount = 0;
        $('.alert-card').each(function() {
            const card = $(this);
            const alertData = {
                severity: card.data('severity') || card.find('[data-severity]').data('severity')
            };
            
            if (alertData.severity === severity) {
                card.show();
                visibleCount++;
            } else {
                card.hide();
            }
        });
        
        // Mettre à jour le compteur de résultats
        this.updateFilterResults(visibleCount);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(`${visibleCount} alerte(s) trouvée(s) pour la sévérité "${this.getSeverityLabel(severity)}"`, 'info', 3000);
        }
    }
    
    filterByStatus(status) {
        console.log(`🔍 Filtrage par statut: ${status}`);
        
        if (!status || status === 'all') {
            $('.alert-card').show();
            return;
        }
        
        let visibleCount = 0;
        $('.alert-card').each(function() {
            const card = $(this);
            const alertData = {
                status: card.data('status') || card.find('[data-status]').data('status')
            };
            
            if (alertData.status === status) {
                card.show();
                visibleCount++;
            } else {
                card.hide();
            }
        });
        
        this.updateFilterResults(visibleCount);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(`${visibleCount} alerte(s) trouvée(s) avec le statut "${status}"`, 'info', 3000);
        }
    }
    
    updateFilterResults(count) {
        // Mettre à jour l'affichage du nombre de résultats
        let filterInfo = $('#filter-results-info');
        if (!filterInfo.length) {
            // Créer l'élément s'il n'existe pas
            filterInfo = $('<div id="filter-results-info" class="text-muted small mb-2"></div>');
            $('#alerts-container').prepend(filterInfo);
        }
        
        if (count === this.alerts.length) {
            filterInfo.hide();
        } else {
            filterInfo.show().html(`
                <i class="fas fa-filter me-1"></i>
                ${count} sur ${this.alerts.length} alerte(s) affichée(s)
                <button class="btn btn-link btn-sm p-0 ms-2" onclick="window.alertManager.clearFilters()">
                    <i class="fas fa-times"></i> Effacer les filtres
                </button>
            `);
        }
    }
    
    clearFilters() {
        console.log('🧹 Effacement des filtres');
        
        // Réinitialiser les sélecteurs
        $('#alert-severity-filter').val('all');
        $('#alert-status-filter').val('all');
        
        // Afficher toutes les alertes
        $('.alert-card').show();
        
        // Masquer l'info des filtres
        $('#filter-results-info').hide();
        
        if (window.notificationSystem) {
            window.notificationSystem.show('Filtres effacés', 'success', 2000);
        }
    }
    
    searchAlerts(query) {
        console.log(`🔍 Recherche: "${query}"`);
        
        if (!query || query.trim() === '') {
            $('.alert-card').show();
            this.updateFilterResults(this.alerts.length);
            return;
        }
        
        const searchTerm = query.toLowerCase().trim();
        let visibleCount = 0;
        
        $('.alert-card').each(function() {
            const card = $(this);
            const title = card.find('.card-title').text().toLowerCase();
            const message = card.find('.card-text').text().toLowerCase();
            const serverName = card.find('[data-server-name]').text().toLowerCase();
            
            if (title.includes(searchTerm) || message.includes(searchTerm) || serverName.includes(searchTerm)) {
                card.show();
                visibleCount++;
            } else {
                card.hide();
            }
        });
        
        this.updateFilterResults(visibleCount);
        
        if (window.notificationSystem) {
            window.notificationSystem.show(`${visibleCount} alerte(s) trouvée(s) pour "${query}"`, 'info', 3000);
        }
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
    
    getSeverityLabel(severity) {
        const labels = {
            'info': 'Information',
            'warning': 'Avertissement',
            'error': 'Erreur',
            'critical': 'Critique'
        };
        return labels[severity] || 'Inconnu';
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
    
    // Redirection vers le module Configuration pour les alertes
    redirectToAlertsConfig() {
        console.log('🛠️ Redirection vers la configuration des alertes');
        
        // Fermer le modal des alertes
        const alertsModal = bootstrap.Modal.getInstance(document.getElementById('alertsModal'));
        if (alertsModal) {
            alertsModal.hide();
        }
        
        // Ouvrir le modal de configuration
        if (window.configManager) {
            const configModal = new bootstrap.Modal(document.getElementById('configModal'));
            configModal.show();
            
            // Charger directement la catégorie alertes
            setTimeout(() => {
                window.configManager.loadCategory('alerts');
            }, 500);
        } else {
            console.error('ConfigManager non disponible');
        }
    }
    
    // Méthode pour l'intégration avec le dashboard
    async getDashboardData() {
        const summary = await this.loadAlertsSummary();
        return {
            active_alerts: summary?.active_alerts || 0,
            critical: summary?.by_severity?.critical?.active || 0,
            warning: summary?.by_severity?.warning?.active || 0,
            info: summary?.by_severity?.info?.active || 0,
            unread: summary?.unread_count || 0,
            recent: summary?.recent_alerts || []
        };
    }
    
    // 🔧 NOUVELLES MÉTHODES UTILITAIRES
    
    updateSelectedCount() {
        const selectedCount = $('.alert-checkbox:checked').length;
        $('#selected-alerts').text(selectedCount);
        $('#selected-count').text(selectedCount);
    }
    
    updateStatistics() {
        if (!this.alerts) return;
        
        const stats = {
            total: this.alerts.length,
            critical: this.alerts.filter(a => a.severity === 'critical').length,
            warning: this.alerts.filter(a => a.severity === 'warning').length,
            info: this.alerts.filter(a => a.severity === 'info').length,
            unread: this.alerts.filter(a => !a.is_read).length
        };
        
        $('#total-alerts').text(stats.total);
        $('#critical-alerts').text(stats.critical);
        $('#warning-alerts').text(stats.warning);
        $('#info-alerts').text(stats.info);
        $('#unread-alerts').text(stats.unread);
        
        console.log('📊 Statistiques mises à jour:', stats);
    }
    
    async showAlertDetails(alertId) {
        try {
            console.log(`🔍 Chargement des détails de l'alerte ${alertId}`);
            
            // Chercher l'alerte dans la liste actuelle
            const alert = this.alerts.find(a => a.id === alertId);
            if (!alert) {
                console.error('Alerte non trouvée dans la liste actuelle');
                return;
            }
            
            // Récupérer les détails complets de l'alerte avec historique
            const response = await fetch(`/api/alerts/${alertId}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.openAlertDetailModal(data.alert);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement des détails');
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement des détails:', error);
            // Fallback: utiliser les données disponibles
            const alert = this.alerts.find(a => a.id === alertId);
            if (alert) {
                this.openAlertDetailModal(alert);
            }
        }
    }
    
    openAlertDetailModal(alertData) {
        // Créer le modal de détails s'il n'existe pas
        let modal = $('#alertDetailModal');
        if (!modal.length) {
            modal = this.createAlertDetailModal();
            $('body').append(modal);
        }
        
        // Remplir le contenu
        this.populateAlertDetailModal(modal, alertData);
        
        // Afficher le modal avec Bootstrap 5
        const bootstrapModal = new bootstrap.Modal(modal[0]);
        bootstrapModal.show();
    }
    
    createAlertDetailModal() {
        return $(`
            <div class="modal fade" id="alertDetailModal" tabindex="-1" role="dialog">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="alertDetailModalLabel">Détails de l'alerte</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="alertDetailModalBody">
                            <!-- Contenu dynamique -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                            <button type="button" class="btn btn-warning" id="acknowledgeAlertBtn" 
                                    onclick="window.alertManager.acknowledgeAlertFromModal()">
                                <i class="fas fa-check me-1"></i>Acquitter
                            </button>
                            <button type="button" class="btn btn-success" id="resolveAlertBtn" 
                                    onclick="window.alertManager.resolveAlertFromModal()">
                                <i class="fas fa-check-double me-1"></i>Résoudre
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }
    
    populateAlertDetailModal(modal, alertData) {
        const modalBody = modal.find('#alertDetailModalBody');
        const modalTitle = modal.find('#alertDetailModalLabel');
        
        // Stocker l'ID pour les actions
        modal.data('alert-id', alertData.id);
        
        // Titre avec icône de sévérité
        const severityIcon = this.getSeverityIcon(alertData.severity);
        modalTitle.html(`${severityIcon} ${alertData.title || 'Alerte'} #${alertData.id}`);
        
        // Calculer les statistiques d'occurrence
        const createdDate = new Date(alertData.created_at);
        const updatedDate = new Date(alertData.updated_at);
        const daysSinceCreated = Math.ceil((Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24));
        
        // Gérer les valeurs undefined/null pour éviter l'affichage "undefined"
        const safeValue = (value, defaultValue = 'Non spécifié') => {
            if (value === null || value === undefined || value === 'undefined' || value === '') {
                return defaultValue;
            }
            return value;
        };
        
        // Fonction pour calculer la fréquence des occurrences
        const calculateFrequency = (alert) => {
            if (!alert.first_occurrence || !alert.last_occurrence || alert.occurrence_count <= 1) {
                return 'Occurrence unique';
            }
            const first = new Date(alert.first_occurrence);
            const last = new Date(alert.last_occurrence);
            const daysDiff = Math.ceil((last - first) / (1000 * 60 * 60 * 24));
            const frequency = daysDiff > 0 ? (alert.occurrence_count / daysDiff).toFixed(1) : alert.occurrence_count;
            return `${frequency} occurrence(s)/jour`;
        };
        
        // Contenu détaillé avec historique et statistiques
        modalBody.html(`
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card border-${this.getSeverityClass(alertData.severity)}">
                        <div class="card-header bg-${this.getSeverityClass(alertData.severity)} text-dark">
                            <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Informations Générales</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Sévérité:</strong> 
                                <span class="badge bg-${this.getSeverityClass(alertData.severity)} text-dark">
                                    ${this.getSeverityLabel(alertData.severity)}
                                </span>
                            </p>
                            <p><strong>Type:</strong> <span class="badge bg-secondary">${safeValue(alertData.alert_type)}</span></p>
                            <p><strong>Statut:</strong> <span class="badge bg-secondary">${safeValue(alertData.status)}</span></p>
                            <p><strong>Serveur:</strong> ${safeValue(alertData.server_name, 'Système')}</p>
                            ${alertData.server_id ? `<p><strong>ID Serveur:</strong> ${alertData.server_id}</p>` : ''}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-clock me-2"></i>Historique Temporel</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Créée le:</strong><br>
                                <small class="text-muted">${createdDate.toLocaleString('fr-FR')}</small>
                            </p>
                            <p><strong>Dernière mise à jour:</strong><br>
                                <small class="text-muted">${updatedDate.toLocaleString('fr-FR')}</small>
                            </p>
                            <p><strong>Durée:</strong> 
                                <span class="badge bg-info text-dark">${daysSinceCreated} jour(s)</span>
                            </p>
                            ${alertData.acknowledged_at ? `
                                <p><strong>Acquittée le:</strong><br>
                                    <small class="text-muted">${new Date(alertData.acknowledged_at).toLocaleString('fr-FR')}</small>
                                </p>
                            ` : ''}
                            ${alertData.resolved_at ? `
                                <p><strong>Résolue le:</strong><br>
                                    <small class="text-muted">${new Date(alertData.resolved_at).toLocaleString('fr-FR')}</small>
                                </p>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-comment me-2"></i>Message de l'Alerte</h6>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-${this.getSeverityClass(alertData.severity)} border-${this.getSeverityClass(alertData.severity)}">
                                <h6 class="alert-heading">${safeValue(alertData.title, 'Alerte')}</h6>
                                <p class="mb-0">${safeValue(alertData.message, 'Aucun message')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            ${alertData.details ? `
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header bg-light">
                                <h6 class="mb-0"><i class="fas fa-cog me-2"></i>Détails Techniques</h6>
                            </div>
                            <div class="card-body">
                                <pre class="bg-dark text-light p-3 rounded small" style="max-height: 300px; overflow-y: auto;"><code>${JSON.stringify(alertData.details, null, 2)}</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-chart-line me-2"></i>Statistiques d'Occurrence</h6>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-md-3">
                                    <div class="border rounded p-2">
                                        <h5 class="text-primary mb-1">${alertData.occurrence_count || 1}</h5>
                                        <small class="text-muted">Occurrences totales</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="border rounded p-2">
                                        <h5 class="text-info mb-1">${daysSinceCreated}</h5>
                                        <small class="text-muted">Jours actifs</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="border rounded p-2">
                                        <h5 class="text-warning mb-1">${alertData.status === 'active' ? 'En cours' : 'Terminée'}</h5>
                                        <small class="text-muted">État actuel</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="border rounded p-2">
                                        <h5 class="text-success mb-1">${alertData.acknowledged_at ? 'Oui' : 'Non'}</h5>
                                        <small class="text-muted">Acquittée</small>
                                    </div>
                                </div>
                            </div>
                            
                            ${alertData.occurrence_count > 1 ? `
                                <div class="mt-3 p-3 bg-light rounded">
                                    <h6><i class="fas fa-repeat me-2"></i>Historique des Occurrences</h6>
                                    <div class="row text-center">
                                        <div class="col-md-4">
                                            <strong>Première occurrence:</strong><br>
                                            <small class="text-muted">${alertData.first_occurrence ? new Date(alertData.first_occurrence).toLocaleString('fr-FR') : 'Non disponible'}</small>
                                        </div>
                                        <div class="col-md-4">
                                            <strong>Dernière occurrence:</strong><br>
                                            <small class="text-muted">${alertData.last_occurrence ? new Date(alertData.last_occurrence).toLocaleString('fr-FR') : 'Non disponible'}</small>
                                        </div>
                                        <div class="col-md-4">
                                            <strong>Fréquence:</strong><br>
                                            <small class="text-muted">${calculateFrequency(alertData)}</small>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-history me-2"></i>Chronologie des Actions</h6>
                        </div>
                        <div class="card-body">
                            <div class="timeline">
                                <div class="timeline-item">
                                    <i class="fas fa-plus-circle text-danger"></i>
                                    <span><strong>Alerte créée</strong> - ${createdDate.toLocaleString('fr-FR')}</span>
                                </div>
                                ${alertData.acknowledged_at ? `
                                    <div class="timeline-item">
                                        <i class="fas fa-check text-warning"></i>
                                        <span><strong>Alerte acquittée</strong> - ${new Date(alertData.acknowledged_at).toLocaleString('fr-FR')}</span>
                                    </div>
                                ` : ''}
                                ${alertData.resolved_at ? `
                                    <div class="timeline-item">
                                        <i class="fas fa-check-double text-success"></i>
                                        <span><strong>Alerte résolue</strong> - ${new Date(alertData.resolved_at).toLocaleString('fr-FR')}</span>
                                    </div>
                                ` : ''}
                                ${alertData.updated_at !== alertData.created_at ? `
                                    <div class="timeline-item">
                                        <i class="fas fa-edit text-info"></i>
                                        <span><strong>Dernière modification</strong> - ${updatedDate.toLocaleString('fr-FR')}</span>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        // Gérer l'affichage des boutons
        const acknowledgeBtn = modal.find('#acknowledgeAlertBtn');
        const resolveBtn = modal.find('#resolveAlertBtn');
        
        if (alertData.status === 'resolved') {
            acknowledgeBtn.hide();
            resolveBtn.hide();
        } else if (alertData.acknowledged_at) {
            acknowledgeBtn.hide();
        }
    }
    
    async acknowledgeAlertFromModal() {
        const modal = $('#alertDetailModal');
        const alertId = modal.data('alert-id');
        
        if (alertId) {
            await this.acknowledgeAlert(alertId);
            const bootstrapModal = bootstrap.Modal.getInstance(modal[0]);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        }
    }
    
    async resolveAlertFromModal() {
        const modal = $('#alertDetailModal');
        const alertId = modal.data('alert-id');
        
        if (alertId) {
            await this.resolveAlert(alertId);
            const bootstrapModal = bootstrap.Modal.getInstance(modal[0]);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
        }
    }
    
    // OPTIMISATION HOLISTIQUE - Gestion d'erreurs robuste
    async loadAlertsWithRetry(maxRetries = 3) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                await this.loadAlerts();
                return;
            } catch (error) {
                console.warn(`Tentative ${i + 1}/${maxRetries} échouée:`, error);
                if (i === maxRetries - 1) {
                    console.error('Échec définitif du chargement des alertes');
                    this.alerts = [];
                    this.updateAlertsDisplay();
                }
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }
}

// Export global
window.AlertManager = AlertManager;

// Instance globale automatique
document.addEventListener('DOMContentLoaded', function() {
    if (!window.alertManager) {
        window.alertManager = new AlertManager();
        console.log('✅ Instance globale alertManager créée');
    }
});

// Fonction globale pour voir le détail d'une alerte depuis le tableau des 3 dernières
function viewAlertDetail(alertId) {
    console.log(`🔍 Affichage détail alerte depuis alert-manager: ${alertId}`);
    
    // Validation de l'ID
    if (!alertId || alertId === 'undefined' || alertId === 'null') {
        console.error('ID d\'alerte invalide:', alertId);
        alert('Erreur: ID d\'alerte invalide');
        return;
    }
    
    // Récupérer les détails via API
    fetch(`/api/alerts/${alertId}`, { credentials: 'include' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('📊 Détails alerte récupérés:', data.alert);
                if (window.alertManager) {
                    window.alertManager.openAlertDetailModal(data.alert);
                } else {
                    console.error('AlertManager non disponible');
                }
            } else {
                throw new Error(data.error || 'Erreur lors du chargement');
            }
        })
        .catch(error => {
            console.error('❌ Erreur chargement détails alerte:', error);
            alert(`Impossible d'afficher les détails de l'alerte #${alertId}: ${error.message}`);
        });
}

// Export global de la fonction
window.viewAlertDetail = viewAlertDetail;
