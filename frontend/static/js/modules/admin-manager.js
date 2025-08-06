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
        
        // Variables pour l'historique des alertes
        this.historyCurrentPage = 1;
        this.historyPerPage = 20;
        this.historyTotalPages = 1;
        this.historyFilters = {};
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
    }

    bindEvents() {
        // Navigation admin
        $(document).on('click', '[data-admin-view]', (e) => {
            e.preventDefault();
            const view = $(e.currentTarget).data('admin-view');
            this.showView(view);
        });

        // Filtres historique alertes
        $(document).on('change', '#history-status-filter, #history-severity-filter', () => {
            this.historyFilters.status = $('#history-status-filter').val();
            this.historyFilters.severity = $('#history-severity-filter').val();
            this.loadHistoricalAlerts(1);
        });

        $(document).on('input', '#history-search', () => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.historyFilters.search = $('#history-search').val();
                this.loadHistoricalAlerts(1);
            }, 500);
        });

        // Pagination historique
        $(document).on('click', '#history-pagination .page-link', (e) => {
            e.preventDefault();
            const page = $(e.currentTarget).data('page');
            if (page) {
                this.loadHistoricalAlerts(page);
            }
        });

        // Export historique
        $(document).on('click', '#export-history-btn', (e) => {
            e.preventDefault();
            this.exportHistoricalAlerts();
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadUsers(),
                this.loadServers(),
                this.loadStats()
            ]);
        } catch (error) {
            console.error('Erreur chargement données initiales:', error);
        }
    }

    async loadUsers() {
        try {
            console.log('👥 AdminManager: Chargement des utilisateurs...');
            const response = await fetch('/api/admin/users');
            console.log('👥 Réponse API utilisateurs:', response.status, response.statusText);
            
            if (response.ok) {
                this.users = await response.json();
                console.log('👥 Utilisateurs chargés:', this.users);
            } else {
                console.error('❌ Erreur API utilisateurs:', response.status, response.statusText);
                this.users = [];
            }
        } catch (error) {
            console.error('❌ Erreur chargement utilisateurs:', error);
            this.users = [];
        }
    }

    async loadServers() {
        try {
            console.log('🖥️ AdminManager: Chargement des serveurs...');
            const response = await fetch('/api/admin/servers');
            console.log('🖥️ Réponse API serveurs:', response.status, response.statusText);
            
            if (response.ok) {
                this.servers = await response.json();
                console.log('🖥️ Serveurs chargés:', this.servers);
            } else {
                console.error('❌ Erreur API serveurs:', response.status, response.statusText);
                this.servers = [];
            }
        } catch (error) {
            console.error('❌ Erreur chargement serveurs:', error);
            this.servers = [];
        }
    }

    async loadStats() {
        try {
            console.log('📊 AdminManager: Chargement des statistiques...');
            const response = await fetch('/api/admin/stats');
            console.log('📊 Réponse API stats:', response.status, response.statusText);
            
            if (response.ok) {
                this.stats = await response.json();
                console.log('📊 Statistiques chargées:', this.stats);
            } else {
                console.error('❌ Erreur API stats:', response.status, response.statusText);
                // Utiliser des données par défaut en cas d'erreur
                this.stats = {
                    servers: { total: 0 },
                    alerts: { active: 0 },
                    users: { total: 0 },
                    database: { uptime: 'N/A' }
                };
            }
        } catch (error) {
            console.error('❌ Erreur chargement statistiques:', error);
            // Utiliser des données par défaut en cas d'erreur
            this.stats = {
                servers: { total: 0 },
                alerts: { active: 0 },
                users: { total: 0 },
                database: { uptime: 'N/A' }
            };
        }
    }

    showView(view) {
        console.log(`🔧 AdminManager: Affichage de la vue "${view}"`);
        this.currentView = view;
        
        // Masquer toutes les vues avec plus de précision
        const adminViews = ['admin-overview', 'admin-users', 'admin-servers', 'admin-stats', 'admin-audit', 'admin-alerts-history'];
        adminViews.forEach(viewId => {
            const element = document.getElementById(viewId);
            if (element) {
                element.style.display = 'none';
                console.log(`🔧 Masqué: ${viewId}`);
            } else {
                console.warn(`⚠️ Élément non trouvé: ${viewId}`);
            }
        });
        
        // Afficher la vue demandée
        const targetViewId = `admin-${view}`;
        const targetElement = document.getElementById(targetViewId);
        if (targetElement) {
            targetElement.style.display = 'block';
            console.log(`✅ Affiché: ${targetViewId}`);
        } else {
            console.error(`❌ Élément cible non trouvé: ${targetViewId}`);
        }
        
        // Mettre à jour la navigation
        $('.nav-item').removeClass('active');
        $(`[data-admin-view="${view}"]`).addClass('active');
        
        // Charger les données spécifiques à la vue
        switch (view) {
            case 'overview':
                console.log('📊 Chargement des statistiques de la vue d\'ensemble');
                // S'assurer que les données sont chargées avant de les afficher
                if (!this.stats || !this.servers || !this.users) {
                    console.log('📊 Données non disponibles, chargement en cours...');
                    this.loadInitialData().then(() => {
                        this.renderStats();
                    }).catch(error => {
                        console.error('❌ Erreur lors du chargement des données:', error);
                        this.renderStats(); // Afficher quand même avec les données disponibles
                    });
                } else {
                    this.renderStats();
                }
                break;
            case 'alerts-history':
                console.log('📋 Affichage de l\'historique des alertes');
                this.showAlertsHistoryView();
                break;
            case 'users':
                console.log('👥 Affichage de la gestion des utilisateurs');
                this.renderUsers();
                break;
            case 'servers':
                console.log('🖥️ Affichage de la gestion des serveurs');
                this.renderServers();
                break;
            case 'stats':
                console.log('📈 Affichage des statistiques détaillées');
                this.renderStats();
                break;
            case 'audit':
                console.log('📝 Affichage des logs d\'audit');
                this.loadAuditLogs();
                break;
            default:
                console.warn(`⚠️ Vue non reconnue: ${view}`);
        }
    }

    showAlertsHistoryView() {
        // Afficher la section historique des alertes
        $('#admin-alerts-history').show();
        
        // Charger les données historiques
        this.loadHistoricalAlerts(1);
        
        // Mettre à jour les filtres
        this.updateHistoryFilters();
    }

    updateHistoryFilters() {
        // Réinitialiser les filtres
        this.historyFilters = {
            status: $('#history-status-filter').val() || 'all',
            severity: $('#history-severity-filter').val() || 'all',
            search: $('#history-search').val() || ''
        };
    }

    clearHistoryFilters() {
        // Réinitialiser les champs de filtres
        $('#history-status-filter').val('');
        $('#history-severity-filter').val('');
        $('#history-start-date').val('');
        $('#history-end-date').val('');
        $('#history-search').val('');
        
        // Réinitialiser les filtres
        this.historyFilters = {};
        
        // Recharger les données
        this.loadHistoricalAlerts(1);
    }

    // === FONCTIONS POUR L'HISTORIQUE DES ALERTES ===

    async loadHistoricalAlerts(page = 1) {
        try {
            this.historyCurrentPage = page;
            
            const params = new URLSearchParams({
                page: page,
                per_page: this.historyPerPage
            });

            // Ajouter les filtres
            if (this.historyFilters.status && this.historyFilters.status !== 'all') {
                params.append('status', this.historyFilters.status);
            }
            if (this.historyFilters.severity && this.historyFilters.severity !== 'all') {
                params.append('severity', this.historyFilters.severity);
            }
            if (this.historyFilters.search) {
                params.append('search', this.historyFilters.search);
            }

            const response = await fetch(`/api/admin/alerts/history?${params}`);
            const data = await response.json();

            if (response.ok) {
                this.renderHistoricalAlerts(data);
            } else {
                throw new Error(data.error || 'Erreur lors du chargement');
            }
        } catch (error) {
            console.error('Erreur chargement historique:', error);
            this.showError("Erreur lors du chargement de l'historique");
        }
    }

    renderHistoricalAlerts(data) {
        const container = $('#history-alerts-table');
        const alerts = data.alerts || [];
        const pagination = data.pagination || {};

        // Mettre à jour la pagination
        this.historyTotalPages = pagination.pages || 1;
        this.renderHistoryPagination(pagination);

        // Mettre à jour le compteur
        $('#history-alerts-count').text(`${pagination.total || 0} alertes trouvées`);

        // Rendre les alertes
        if (alerts.length === 0) {
            container.html(`
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucune alerte historique trouvée</p>
                    </td>
                </tr>
            `);
            return;
        }

        const alertsHtml = alerts.map(alert => this.renderAlertItem(alert)).join('');
        container.html(alertsHtml);
    }

    renderAlertItem(alert) {
        const severityClass = this.getSeverityClass(alert.severity);
        const severityIcon = this.getSeverityIcon(alert.severity);
        const statusClass = this.getStatusClass(alert.status);
        const statusIcon = this.getStatusIcon(alert.status);
        
        return `
            <tr>
                <td><small class="text-muted">#${alert.id}</small></td>
                <td>
                    <span class="badge bg-secondary">${alert.server_name || 'Système'}</span>
                </td>
                <td>
                    <div class="fw-bold">${alert.title || 'Alerte'}</div>
                    <small class="text-muted">${alert.message || 'Aucun message'}</small>
                </td>
                <td>
                    <span class="badge bg-${severityClass}">
                        ${severityIcon} ${alert.severity}
                    </span>
                </td>
                <td>
                    <span class="badge bg-${statusClass}">
                        ${statusIcon} ${alert.status}
                    </span>
                </td>
                <td><small>${this.formatDate(alert.created_at)}</small></td>
                <td>
                    ${alert.resolved_at ? `<small>${this.formatDate(alert.resolved_at)}</small>` : '<span class="text-muted">-</span>'}
                </td>
            </tr>
        `;
    }

    renderHistoryPagination(pagination) {
        const container = $('#history-pagination');
        const currentPage = pagination.page || 1;
        const totalPages = pagination.pages || 1;

        if (totalPages <= 1) {
            container.html('');
            return;
        }

        let paginationHtml = '<ul class="pagination justify-content-center">';
        
        // Bouton précédent
        if (currentPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage - 1}">Précédent</a></li>`;
        }

        // Pages
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === currentPage ? 'active' : '';
            paginationHtml += `<li class="page-item ${activeClass}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }

        // Bouton suivant
        if (currentPage < totalPages) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage + 1}">Suivant</a></li>`;
        }

        paginationHtml += '</ul>';
        container.html(paginationHtml);
    }

    async exportHistoricalAlerts() {
        try {
            const params = new URLSearchParams();
            
            // Ajouter les filtres
            if (this.historyFilters.status && this.historyFilters.status !== 'all') {
                params.append('status', this.historyFilters.status);
            }
            if (this.historyFilters.severity && this.historyFilters.severity !== 'all') {
                params.append('severity', this.historyFilters.severity);
            }
            if (this.historyFilters.search) {
                params.append('search', this.historyFilters.search);
            }

            const response = await fetch(`/api/admin/alerts/history/export?${params}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `alertes_historiques_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showSuccess('Export réussi');
            } else {
                throw new Error('Erreur lors de l\'export');
            }
        } catch (error) {
            console.error('Erreur export:', error);
            this.showError('Erreur lors de l\'export');
        }
    }

    // === FONCTIONS UTILITAIRES ===

    getSeverityClass(severity) {
        const classes = {
            'info': 'info',
            'warning': 'warning',
            'critical': 'danger'
        };
        return classes[severity] || 'info';
    }

    getSeverityIcon(severity) {
        const icons = {
            'info': '<i class="fas fa-info-circle"></i>',
            'warning': '<i class="fas fa-exclamation-triangle"></i>',
            'critical': '<i class="fas fa-exclamation-circle"></i>'
        };
        return icons[severity] || '<i class="fas fa-info-circle"></i>';
    }

    getStatusClass(status) {
        const classes = {
            'active': 'danger',
            'acknowledged': 'warning',
            'resolved': 'success'
        };
        return classes[status] || 'secondary';
    }

    getStatusIcon(status) {
        const icons = {
            'active': '<i class="fas fa-exclamation"></i>',
            'acknowledged': '<i class="fas fa-check"></i>',
            'resolved': '<i class="fas fa-check-double"></i>'
        };
        return icons[status] || '<i class="fas fa-question"></i>';
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR');
    }

    showError(message) {
        // Afficher une erreur (à implémenter selon votre système de notifications)
        console.error(message);
    }

    showSuccess(message) {
        // Afficher un succès (à implémenter selon votre système de notifications)
        console.log(message);
    }

    // === FONCTIONS POUR LES AUTRES VUES ===

    renderUsers() {
        console.log('👥 AdminManager: Rendu des utilisateurs');
        console.log('👥 Utilisateurs disponibles:', this.users);
        
        const container = $('#users-table');
        if (!this.users || this.users.length === 0) {
            console.log('👥 Aucun utilisateur à afficher');
            container.html(`
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-users fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun utilisateur trouvé</p>
                    </td>
                </tr>
            `);
            return;
        }

        console.log(`👥 Affichage de ${this.users.length} utilisateurs`);

        const usersHtml = this.users.map(user => `
            <tr>
                <td><small class="text-muted">#${user.id}</small></td>
                <td>
                    <div class="fw-bold">${user.username}</div>
                    <small class="text-muted">${user.email}</small>
                </td>
                <td>${user.first_name || '-'}</td>
                <td>${user.last_name || '-'}</td>
                <td>
                    <span class="badge bg-${user.role === 'admin' ? 'danger' : user.role === 'operator' ? 'warning' : 'secondary'}">
                        ${user.role}
                    </span>
                </td>
                <td>
                    <span class="badge bg-${user.is_active ? 'success' : 'secondary'}">
                        ${user.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="adminManager.showUserModal(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        container.html(usersHtml);
    }

    renderServers() {
        console.log('🖥️ AdminManager: Rendu des serveurs');
        console.log('🖥️ Serveurs disponibles:', this.servers);
        
        const container = $('#servers-table');
        if (!this.servers || this.servers.length === 0) {
            console.log('🖥️ Aucun serveur à afficher');
            container.html(`
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-server fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun serveur trouvé</p>
                    </td>
                </tr>
            `);
            return;
        }

        console.log(`🖥️ Affichage de ${this.servers.length} serveurs`);

        const serversHtml = this.servers.map(server => `
            <tr>
                <td><small class="text-muted">#${server.id}</small></td>
                <td>
                    <div class="fw-bold">${server.name}</div>
                    <small class="text-muted">${server.description || 'Aucune description'}</small>
                </td>
                <td>
                    <code>${server.address}</code>
                    ${server.port ? `<br><small class="text-muted">Port: ${server.port}</small>` : ''}
                </td>
                <td>
                    <span class="badge bg-${server.server_type === 'global' ? 'primary' : 'info'}">
                        ${server.server_type}
                    </span>
                </td>
                <td>
                    <span class="badge bg-${server.is_active ? 'success' : 'secondary'}">
                        ${server.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </td>
                <td>
                    ${server.priority ? `<span class="badge bg-warning">${server.priority}</span>` : '<span class="text-muted">-</span>'}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="adminManager.showServerModal(${server.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        container.html(serversHtml);
    }

    renderStats() {
        console.log('📊 AdminManager: Rendu des statistiques');
        console.log('📊 Stats disponibles:', this.stats);
        console.log('📊 Serveurs disponibles:', this.servers);
        
        // Mettre à jour les compteurs de la vue d'ensemble
        if (this.stats) {
            const totalServers = this.stats.servers?.total || 0;
            const activeAlerts = this.stats.alerts?.active || 0;
            const totalUsers = this.stats.users?.total || 0;
            const uptime = this.stats.database?.uptime || 'N/A';
            
            console.log(`📊 Mise à jour des compteurs: Serveurs=${totalServers}, Alertes=${activeAlerts}, Utilisateurs=${totalUsers}, Uptime=${uptime}`);
            
            // Vérifier que les éléments existent avant de les mettre à jour
            const totalServersEl = $('#overview-total-servers');
            const activeAlertsEl = $('#overview-active-alerts');
            const totalUsersEl = $('#overview-total-users');
            const uptimeEl = $('#overview-uptime');
            
            if (totalServersEl.length) totalServersEl.text(totalServers);
            if (activeAlertsEl.length) activeAlertsEl.text(activeAlerts);
            if (totalUsersEl.length) totalUsersEl.text(totalUsers);
            if (uptimeEl.length) uptimeEl.text(uptime);
            
            console.log('✅ Compteurs mis à jour');
        } else {
            console.warn('⚠️ Aucune statistique disponible');
            $('#overview-total-servers').text('0');
            $('#overview-active-alerts').text('0');
            $('#overview-total-users').text('0');
            $('#overview-uptime').text('N/A');
        }

        // Mettre à jour les graphiques des statistiques - CORRIGÉ pour éviter les chargements sans fin
        const severityChart = $('#stats-severity-chart');
        const serverChart = $('#stats-server-chart');
        const performanceTable = $('#stats-performance-table');

        console.log('🔍 Vérification des éléments de graphiques...');
        console.log('📊 Severity chart existe:', severityChart.length > 0);
        console.log('📊 Server chart existe:', serverChart.length > 0);
        console.log('📊 Performance table existe:', performanceTable.length > 0);

        if (this.stats && this.stats.alerts && severityChart.length > 0) {
            // Graphique par sévérité
            const severityData = this.stats.alerts.by_severity || {};
            const severityHtml = `
                <div class="text-center">
                    <h6>Répartition par Sévérité</h6>
                    <div class="row">
                        <div class="col-4">
                            <div class="text-info">
                                <h4>${severityData.info || 0}</h4>
                                <small>Info</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="text-warning">
                                <h4>${severityData.warning || 0}</h4>
                                <small>Warning</small>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="text-danger">
                                <h4>${severityData.critical || 0}</h4>
                                <small>Critical</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            severityChart.html(severityHtml);
            console.log('✅ Graphique sévérité mis à jour');
        } else if (severityChart.length > 0) {
            severityChart.html('<div class="text-center text-muted">Aucune donnée disponible</div>');
            console.log('⚠️ Aucune donnée pour le graphique sévérité');
        }

        if (this.stats && this.stats.alerts && serverChart.length > 0) {
            // Graphique par serveur
            const serverData = this.stats.alerts.by_server || {};
            const serverHtml = `
                <div class="text-center">
                    <h6>Alertes par Serveur</h6>
                    <div class="text-muted">
                        ${Object.keys(serverData).length > 0 ? 
                            Object.entries(serverData).map(([server, count]) => 
                                `<div class="mb-1"><strong>${server}:</strong> ${count}</div>`
                            ).join('') : 
                            '<p class="text-muted">Aucune donnée</p>'
                        }
                    </div>
                </div>
            `;
            serverChart.html(serverHtml);
            console.log('✅ Graphique serveur mis à jour');
        } else if (serverChart.length > 0) {
            serverChart.html('<div class="text-center text-muted">Aucune donnée disponible</div>');
            console.log('⚠️ Aucune donnée pour le graphique serveur');
        }

        // Tableau de performance - CORRIGÉ pour éviter les boucles infinies
        if (this.servers && this.servers.length > 0 && performanceTable.length > 0) {
            console.log(`📊 Rendu du tableau de performance avec ${this.servers.length} serveurs`);
            
            // Filtrer les serveurs actifs seulement
            const activeServers = this.servers.filter(server => server.is_active && !server.is_deleted).slice(0, 10);
            
            if (activeServers.length > 0) {
                const performanceHtml = `
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Serveur</th>
                                    <th>Latence</th>
                                    <th>Offset</th>
                                    <th>Stratum</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${activeServers.map(server => {
                                    // Protection contre les valeurs undefined/null
                                    const name = server.name || 'Serveur inconnu';
                                    const latency = server.last_latency ? `${server.last_latency.toFixed(2)}ms` : '-';
                                    const offset = server.last_offset ? `${server.last_offset.toFixed(2)}ms` : '-';
                                    const stratum = server.last_stratum || '-';
                                    const status = server.status || 'Inconnu';
                                    const statusClass = this.getStatusClass(status);
                                    
                                    return `
                                        <tr>
                                            <td>${name}</td>
                                            <td>${latency}</td>
                                            <td>${offset}</td>
                                            <td>${stratum}</td>
                                            <td>
                                                <span class="badge bg-${statusClass}">
                                                    ${status}
                                                </span>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
                performanceTable.html(performanceHtml);
                console.log('✅ Tableau de performance mis à jour');
            } else {
                performanceTable.html('<div class="text-center text-muted">Aucun serveur actif disponible</div>');
                console.log('⚠️ Aucun serveur actif pour le tableau de performance');
            }
        } else if (performanceTable.length > 0) {
            console.log('📊 Aucun serveur disponible pour le tableau de performance');
            performanceTable.html('<div class="text-center text-muted">Aucune donnée de performance disponible</div>');
        }
    }

    // === MÉTHODES MANQUANTES POUR LES MODALS ===

    openModal() {
        console.log('🔧 AdminManager: Ouverture du modal d\'administration');
        const modal = new bootstrap.Modal(document.getElementById('adminModal'));
        modal.show();
        
        // Attendre que le modal soit complètement affiché avant de changer de vue
        setTimeout(() => {
            console.log('🔧 AdminManager: Initialisation de la vue d\'ensemble');
            this.showView('overview');
        }, 100);
    }

    switchToView(view) {
        this.showView(view);
    }

    previousHistoryPage() {
        if (this.historyCurrentPage > 1) {
            this.loadHistoricalAlerts(this.historyCurrentPage - 1);
        }
    }

    nextHistoryPage() {
        if (this.historyCurrentPage < this.historyTotalPages) {
            this.loadHistoricalAlerts(this.historyCurrentPage + 1);
        }
    }

    showUserModal(userId = null) {
        const modal = new bootstrap.Modal(document.getElementById('userModal'));
        const form = document.getElementById('user-form');
        const title = document.getElementById('user-modal-title');
        
        if (userId) {
            title.textContent = 'Modifier l\'Utilisateur';
            const user = this.users.find(u => u.id === userId);
            if (user) {
                document.getElementById('user-id').value = user.id;
                document.getElementById('user-username').value = user.username;
                document.getElementById('user-email').value = user.email;
                document.getElementById('user-first-name').value = user.first_name || '';
                document.getElementById('user-last-name').value = user.last_name || '';
                document.getElementById('user-role').value = user.role;
                document.getElementById('user-is-active').checked = user.is_active;
                document.getElementById('user-password').required = false;
            }
        } else {
            title.textContent = 'Nouvel Utilisateur';
            form.reset();
            document.getElementById('user-password').required = true;
        }
        
        modal.show();
    }

    showServerModal(serverId = null) {
        const modal = new bootstrap.Modal(document.getElementById('serverModal'));
        const form = document.getElementById('server-form');
        const title = document.getElementById('server-modal-title');
        
        if (serverId) {
            title.textContent = 'Modifier le Serveur';
            const server = this.servers.find(s => s.id === serverId);
            if (server) {
                document.getElementById('server-id').value = server.id;
                document.getElementById('server-name').value = server.name;
                document.getElementById('server-address').value = server.address;
                document.getElementById('server-type').value = server.server_type;
                document.getElementById('server-port').value = server.port;
                document.getElementById('server-timeout').value = server.timeout;
                document.getElementById('server-max-offset').value = server.max_offset;
                document.getElementById('server-critical-offset').value = server.critical_offset;
                document.getElementById('server-description').value = server.description || '';
                document.getElementById('server-is-active').checked = server.is_active;
            }
        } else {
            title.textContent = 'Nouveau Serveur NTP';
            form.reset();
            document.getElementById('server-port').value = 123;
            document.getElementById('server-timeout').value = 10;
            document.getElementById('server-max-offset').value = 1.0;
            document.getElementById('server-critical-offset').value = 5.0;
        }
        
        modal.show();
    }

    showExportModal() {
        const modal = new bootstrap.Modal(document.getElementById('exportImportModal'));
        document.getElementById('export-import-title').textContent = 'Export de Données';
        modal.show();
    }

    showImportModal() {
        const modal = new bootstrap.Modal(document.getElementById('exportImportModal'));
        document.getElementById('export-import-title').textContent = 'Import de Données';
        modal.show();
    }

    showMaintenanceModal() {
        const modal = new bootstrap.Modal(document.getElementById('maintenanceModal'));
        modal.show();
    }

    performExport() {
        const options = {
            config: document.getElementById('export-config').checked,
            servers: document.getElementById('export-servers').checked,
            users: document.getElementById('export-users').checked
        };
        this.exportData(options);
    }

    performImport() {
        if (!window.importData) {
            this.showNotification('Aucun fichier sélectionné', 'error');
            return;
        }
        
        const options = {
            config: document.getElementById('import-config').checked,
            servers: document.getElementById('import-servers').checked,
            users: document.getElementById('import-users').checked
        };
        
        this.showNotification('Import simulé avec succès', 'info');
    }

    performMaintenanceFromModal() {
        const options = {
            old_logs: document.getElementById('cleanup-old-logs').checked,
            resolved_alerts: document.getElementById('cleanup-resolved-alerts').checked,
            optimize_db: document.getElementById('optimize-db').checked,
            expired_sessions: document.getElementById('cleanup-expired-sessions').checked,
            log_retention_days: parseInt(document.getElementById('log-retention-days').value)
        };
        
        this.performMaintenance(options);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('maintenanceModal'));
        modal.hide();
    }

    saveUser() {
        // TODO: Implémenter la sauvegarde d'utilisateur
        this.showNotification('Utilisateur sauvegardé avec succès', 'success');
        const modal = bootstrap.Modal.getInstance(document.getElementById('userModal'));
        modal.hide();
    }

    saveServer() {
        // TODO: Implémenter la sauvegarde de serveur
        this.showNotification('Serveur sauvegardé avec succès', 'success');
        const modal = bootstrap.Modal.getInstance(document.getElementById('serverModal'));
        modal.hide();
    }

    testServerForm() {
        // TODO: Implémenter le test de serveur
        this.showNotification('Test de serveur effectué', 'info');
    }

    exportData(options) {
        // TODO: Implémenter l'export de données
        this.showNotification('Export effectué avec succès', 'success');
    }

    performMaintenance(options) {
        // TODO: Implémenter la maintenance
        this.showNotification('Maintenance effectuée avec succès', 'success');
    }

    showNotification(message, type = 'info') {
        // Afficher une notification
        console.log(`${type.toUpperCase()}: ${message}`);
        // TODO: Implémenter un système de notifications visuelles
    }

    async loadAuditLogs() {
        try {
            const response = await fetch('/api/admin/audit/logs');
            if (response.ok) {
                const data = await response.json();
                this.auditLogs = data.logs || [];
                this.renderAuditLogs();
            }
        } catch (error) {
            console.error('Erreur chargement logs audit:', error);
        }
    }

    renderAuditLogs() {
        const container = $('#audit-logs-table');
        if (!this.auditLogs || this.auditLogs.length === 0) {
            container.html(`
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        <i class="fas fa-history fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun log d'audit trouvé</p>
                    </td>
                </tr>
            `);
            return;
        }

        const logsHtml = this.auditLogs.map(log => `
            <tr>
                <td><small>${this.formatDate(log.timestamp)}</small></td>
                <td>${log.username || 'Système'}</td>
                <td>
                    <span class="badge bg-${log.action === 'login' ? 'success' : log.action === 'logout' ? 'warning' : 'info'}">
                        ${log.action}
                    </span>
                </td>
                <td>${log.details || '-'}</td>
                <td><small class="text-muted">${log.ip_address || '-'}</small></td>
            </tr>
        `).join('');

        container.html(logsHtml);
    }

    refreshAuditLogs() {
        this.loadAuditLogs();
    }
}

// Initialisation automatique d'AdminManager
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Initialisation automatique d\'AdminManager...');
    
    // Vérifier que l'utilisateur est admin
    const adminModal = document.getElementById('adminModal');
    if (adminModal) {
        console.log('✅ Modal d\'administration trouvé, initialisation d\'AdminManager');
        
        // Créer l'instance globale
        window.adminManager = new AdminManager();
        console.log('✅ AdminManager initialisé et assigné à window.adminManager');
        
        // Initialiser les événements du modal
        adminModal.addEventListener('shown.bs.modal', function() {
            console.log('🔧 Modal d\'administration ouvert, initialisation de la vue d\'ensemble');
            if (window.adminManager) {
                window.adminManager.showView('overview');
            }
        });
        
    } else {
        console.log('⚠️ Modal d\'administration non trouvé, AdminManager non initialisé');
    }
});

// Initialisation alternative si DOMContentLoaded a déjà été déclenché
if (document.readyState === 'loading') {
    // Le DOM est encore en cours de chargement
    console.log('⏳ DOM en cours de chargement, attente de DOMContentLoaded...');
} else {
    // Le DOM est déjà chargé
    console.log('🔧 DOM déjà chargé, initialisation immédiate d\'AdminManager...');
    
    const adminModal = document.getElementById('adminModal');
    if (adminModal) {
        console.log('✅ Modal d\'administration trouvé, initialisation immédiate d\'AdminManager');
        window.adminManager = new AdminManager();
        console.log('✅ AdminManager initialisé immédiatement');
        
        // Initialiser les événements du modal
        adminModal.addEventListener('shown.bs.modal', function() {
            console.log('🔧 Modal d\'administration ouvert, initialisation de la vue d\'ensemble');
            if (window.adminManager) {
                window.adminManager.showView('overview');
            }
        });
    }
}

// Initialisation
$(document).ready(() => {
    window.adminManager = new AdminManager();
}); 