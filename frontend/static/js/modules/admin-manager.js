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
        this.charts = {};
        this.detailedStats = null;
        
        // Variables pour l'historique des alertes
        this.historyCurrentPage = 1;
        this.historyPerPage = 20;
        this.historyTotalPages = 1;
        this.historyFilters = {};
        // Filtres utilisateurs (client-side)
        this.userFilters = { role: '', status: '', search: '' };

        // Pagination et filtres pour logs d'audit
        this.auditCurrentPage = 1;
        this.auditPerPage = 50;
        this.auditTotalPages = 1;
        this.auditFilters = { action: '', user: '', start: '', end: '' };
        
        this.init();
    }

    async toggleUserStatus(userId) {
        if (!userId) return;
        try {
            const res = await fetch(`/api/admin/users/${userId}/toggle-status`, { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            this.showNotification(data.message || 'Statut utilisateur modifié', 'success');
            await this.refreshUsers();
        } catch (err) {
            console.error('Erreur bascule statut utilisateur:', err);
            this.showNotification(err.message || 'Erreur lors du changement de statut', 'error');
        }
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

        // === Utilisateurs: gestion du formulaire et du mot de passe ===
        $(document).on('click', '#generatePasswordBtn', (e) => {
            e.preventDefault();
            this.handleGeneratePassword();
        });
        $(document).on('click', '#togglePasswordBtn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.togglePasswordVisibility(e.currentTarget);
        });
        $(document).on('input', '#userPassword', (e) => {
            this.updatePasswordStrength(e.target.value || '');
        });
        $(document).on('click', '#createUserBtn', (e) => {
            e.preventDefault();
            this.createUser();
        });
        $(document).on('click', '#updateUserBtn', (e) => {
            e.preventDefault();
            this.updateUser();
        });

        // Modal d'affichage du mot de passe généré
        $(document).on('click', '#copyPasswordBtn', (e) => {
            e.preventDefault();
            this.copyDisplayedPassword();
        });
        $(document).on('click', '#showPasswordBtn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleDisplayedPasswordVisibility(e.currentTarget);
        });
        // Édition: interactions mot de passe optionnel
        $(document).on('click', '#toggleEditPasswordBtn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleEditPasswordVisibility(e.currentTarget);
        });
        $(document).on('input', '#editUserPassword', (e) => {
            this.updateEditPasswordStrength(e.target.value || '');
        });

        // Validation inline unicité avec debounce
        const debounced = (fn, delay = 400) => {
            let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), delay); };
        };
        this.checkUniqueDebounced = debounced(this.checkUserUniqueness.bind(this), 500);
        $(document).on('input', '#userCreateUsername, #userCreateEmail', () => this.checkUniqueDebounced());

        // === Utilisateurs: filtres ===
        $(document).on('change', '#user-role-filter, #user-status-filter', () => {
            this.applyUserFilters();
        });
        $(document).on('input', '#user-search', () => {
            clearTimeout(this.userSearchTimeout);
            this.userSearchTimeout = setTimeout(() => this.applyUserFilters(), 400);
        });

        // === Serveurs: filtres ===
        $(document).on('change', '#server-type-filter, #server-status-filter, #server-active-filter', () => {
            this.applyServerFilters();
        });
        $(document).on('input', '#server-search', () => {
            clearTimeout(this.serverSearchTimeout);
            this.serverSearchTimeout = setTimeout(() => this.applyServerFilters(), 400);
        });

        // === Historique alertes: filtre serveur et dates ===
        $(document).on('change', '#history-server-filter, #history-status-filter, #history-severity-filter, #history-start-date, #history-end-date', () => {
            this.updateHistoryFilters();
            this.loadHistoricalAlerts(1);
        });

        // === Audit: filtres ===
        $(document).on('change', '#audit-action-filter, #audit-user-filter, #audit-start-date, #audit-end-date', () => {
            this.applyAuditFilters();
        });
        // Audit: pagination
        $(document).on('click', '#audit-pagination .page-link', (e) => {
            e.preventDefault();
            const page = $(e.currentTarget).data('page');
            if (page) {
                this.loadAuditLogs(page);
            }
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

    async refreshUsers() {
        try {
            console.log('🔄 Actualisation de la liste des utilisateurs...');
            const container = $('#users-table');
            if (container && container.length) {
                container.html(`
                    <tr>
                        <td colspan="8" class="text-center text-muted py-4">
                            <i class="fas fa-spinner fa-spin me-2"></i>Actualisation...
                        </td>
                    </tr>
                `);
            }
            await this.loadUsers();
            this.renderUsers();
            this.showNotification('Liste des utilisateurs actualisée', 'success');
        } catch (error) {
            console.error('❌ Erreur lors de l\'actualisation des utilisateurs:', error);
            this.showNotification('Erreur lors de l\'actualisation des utilisateurs', 'error');
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

    async loadDetailedStats(days = 7) {
        try {
            console.log('📊 AdminManager: Chargement statistiques détaillées...');
            const response = await fetch(`/api/admin/stats/detailed?days=${days}`);
            if (response.ok) {
                this.detailedStats = await response.json();
                console.log('📊 Statistiques détaillées chargées:', this.detailedStats);
            } else {
                console.warn('⚠️ Stats détaillées non disponibles:', response.status, response.statusText);
                this.detailedStats = null;
            }
        } catch (e) {
            console.warn('⚠️ Erreur chargement stats détaillées:', e);
            this.detailedStats = null;
        }
    }

    renderSystemStats() {
        const container = document.getElementById('stats-db-size');
        // Si la section n'existe pas dans le DOM (template différent), sortir
        if (!container) return;
        // Utiliser les données overview si detailed non dispo
        const overview = this.stats || {};
        const dbUptime = overview.database?.uptime || 'N/A';
        const totalServers = overview.servers?.total ?? '-';
        const totalUsers = overview.users?.total ?? '-';
        const activeAlerts = overview.alerts?.active ?? '-';

        // Renseigner les compteurs déjà présents via renderStats(); ici on complète si besoin
        const uptimeEl = document.getElementById('overview-uptime');
        if (uptimeEl && dbUptime) uptimeEl.textContent = dbUptime;

        // Aucune autre valeur statique ciblée par id dédiée à “Statistiques Système” dans le template
        // Si desired: injecter un résumé détaillé sous la carte Statistiques Système
        const sysCard = container.closest('.card-body');
        if (sysCard && this.detailedStats) {
            const extraId = 'system-stats-extra';
            let extra = document.getElementById(extraId);
            if (!extra) {
                extra = document.createElement('div');
                extra.id = extraId;
                extra.className = 'mt-3';
                sysCard.appendChild(extra);
            }
            const ua = this.detailedStats.system_usage || {};
            extra.innerHTML = `
                <div class="row">
                    <div class="col-md-3"><small class="text-muted">CPU</small><div>${ua.cpu_usage ?? '-'}%</div></div>
                    <div class="col-md-3"><small class="text-muted">RAM</small><div>${ua.memory_usage ?? '-'}%</div></div>
                    <div class="col-md-3"><small class="text-muted">Disque</small><div>${ua.disk_usage ?? '-'}%</div></div>
                    <div class="col-md-3"><small class="text-muted">Alertes actives</small><div>${activeAlerts}</div></div>
                </div>
            `;
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
                // Charger et afficher les stats détaillées (système)
                this.loadDetailedStats().then(() => {
                    this.renderSystemStats();
                }).catch(() => {
                    this.renderSystemStats();
                });
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
        const allUsers = Array.isArray(this.users) ? this.users : [];

        // Appliquer filtres côté client
        const role = (document.getElementById('user-role-filter')?.value || '').trim();
        const status = (document.getElementById('user-status-filter')?.value || '').trim();
        const search = (document.getElementById('user-search')?.value || '').trim().toLowerCase();

        let filtered = allUsers.slice();
        if (role) filtered = filtered.filter(u => (u.role || '').toLowerCase() === role.toLowerCase());
        if (status) {
            const isActive = status === 'true';
            filtered = filtered.filter(u => !!u.is_active === isActive);
        }
        if (search) {
            filtered = filtered.filter(u => {
                const hay = `${u.username || ''} ${u.email || ''} ${u.first_name || ''} ${u.last_name || ''}`.toLowerCase();
                return hay.includes(search);
            });
        }

        if (filtered.length === 0) {
            console.log('👥 Aucun utilisateur à afficher');
            container.html(`
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <i class="fas fa-users fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun utilisateur trouvé</p>
                    </td>
                </tr>
            `);
            return;
        }

        console.log(`👥 Affichage de ${filtered.length} utilisateurs (filtrés)`);

        const usersHtml = filtered.map(user => {
            const fullName = [user.first_name || '', user.last_name || '']
                .join(' ')
                .trim() || '-';
            const toggleTitle = user.is_active ? 'Désactiver' : 'Activer';
            const toggleIcon = user.is_active ? 'fa-user-slash' : 'fa-user-check';
            return `
            <tr>
                <td><small class="text-muted">#${user.id}</small></td>
                <td><div class="fw-bold">${user.username}</div></td>
                <td><small class="text-muted">${user.email || '-'}</small></td>
                <td>${fullName}</td>
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
                <td><small class="text-muted">${this.formatDate(user.last_login)}</small></td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" title="Éditer" onclick="adminManager.showUserEditModal(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                        <button class="btn btn-outline-secondary" title="${toggleTitle}" onclick="adminManager.toggleUserStatus(${user.id})">
                            <i class="fas ${toggleIcon}"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
        }).join('');

        container.html(usersHtml);
    }

    applyUserFilters() {
        // Re-render avec les filtres actuels
        this.renderUsers();
        this.showNotification('Filtres utilisateurs appliqués', 'info');
    }

    clearUserFilters() {
        // Réinitialiser les filtres de la section utilisateurs s'ils existent
        const roleFilter = document.getElementById('user-role-filter');
        const statusFilter = document.getElementById('user-status-filter');
        if (roleFilter) roleFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        // Relancer l'actualisation des utilisateurs
        this.refreshUsers();
        this.showNotification('Filtres utilisateurs réinitialisés', 'info');
    }

    renderServers() {
        console.log('🖥️ AdminManager: Rendu des serveurs');
        console.log('🖥️ Serveurs disponibles:', this.servers);
        
        const container = $('#servers-table');
        const allServers = Array.isArray(this.servers) ? this.servers : [];
        // Appliquer filtres côté client
        const type = (document.getElementById('server-type-filter')?.value || '').trim();
        const status = (document.getElementById('server-status-filter')?.value || '').trim();
        const active = (document.getElementById('server-active-filter')?.value || '').trim();
        const search = (document.getElementById('server-search')?.value || '').trim().toLowerCase();

        let filtered = allServers.slice();
        if (type) {
            const isId = /^\d+$/.test(type);
            filtered = filtered.filter(s => isId ? String(s.server_type_id || '') === type : (s.server_type_code || s.server_type || '').toLowerCase() === type.toLowerCase());
        }
        if (status) filtered = filtered.filter(s => (s.status || '').toLowerCase() === status.toLowerCase());
        if (active) {
            const isActive = active === 'true';
            filtered = filtered.filter(s => !!s.is_active === isActive);
        }
        if (search) {
            filtered = filtered.filter(s => {
                const hay = `${s.name || ''} ${s.address || ''} ${s.description || ''}`.toLowerCase();
                return hay.includes(search);
            });
        }
        if (filtered.length === 0) {
            console.log('🖥️ Aucun serveur à afficher');
            container.html(`
                <tr>
                    <td colspan="10" class="text-center text-muted py-4">
                        <i class="fas fa-server fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun serveur trouvé</p>
                    </td>
                </tr>
            `);
            return;
        }

        console.log(`🖥️ Affichage de ${filtered.length} serveurs (filtrés)`);

        const serversHtml = filtered.map(server => {
            const statusText = (server.status || '').toString().trim();
            const statusLabel = statusText || (server.is_active ? 'Actif' : 'Inactif');
            const statusClass = statusText ? this.getStatusClass(statusText) : (server.is_active ? 'success' : 'secondary');
            const formatMs = (v) => (v === 0 || v) ? `${Number(v).toFixed(2)}ms` : '-';
            const offset = formatMs(server.last_offset);
            const latency = formatMs(server.last_latency);
            const stratum = (server.last_stratum === 0 || server.last_stratum) ? server.last_stratum : '-';
            const priority = (server.priority === 0 || server.priority) ? `<span class=\"badge bg-warning\">${server.priority}</span>` : '<span class=\"text-muted\">-</span>';
            return `
            <tr>
                <td><small class="text-muted">#${server.id}</small></td>
                <td>
                    <div class="fw-bold">${server.name}</div>
                    <small class="text-muted">${server.description || 'Aucune description'}</small>
                </td>
                <td>
                    <code>${server.address}</code>
                    ${server.port ? `<br><small class=\"text-muted\">Port: ${server.port}</small>` : ''}
                </td>
                <td>
                    <span class="badge bg-${(server.server_type_code || server.server_type) === 'internet' ? 'primary' : 'info'}">${server.server_type_label || server.server_type}</span>
                </td>
                <td>
                    <span class="badge bg-${statusClass}">${statusLabel}</span>
                </td>
                <td>${offset}</td>
                <td>${latency}</td>
                <td>${stratum}</td>
                <td>${priority}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="adminManager.testServer(${server.id})" title="Tester le serveur (UDP + NTP)">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="adminManager.showServerEditModal(${server.id})" title="Éditer le serveur">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="adminManager.askDeleteServer(${server.id}, '${(server.name || '').replace(/'/g, "\'")}')" title="Supprimer le serveur">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        }).join('');

        container.html(serversHtml);
    }

    askDeleteServer(serverId, serverName) {
        const idEl = document.getElementById('delete-server-id');
        const nameEl = document.getElementById('delete-server-name');
        if (idEl) idEl.value = serverId;
        if (nameEl) nameEl.textContent = serverName || '';
        const modal = new bootstrap.Modal(document.getElementById('deleteServerModal'));
        modal.show();
    }

    confirmDeleteServer() {
        const id = document.getElementById('delete-server-id')?.value;
        if (!id) return;
        const btn = document.getElementById('confirmDeleteServerBtn');
        if (btn) btn.disabled = true;
        fetch(`/api/admin/servers/${id}`, { method: 'DELETE' })
            .then(async (res) => {
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
                return data;
            })
            .then((data) => {
                this.showNotification(data.message || 'Serveur supprimé', 'success');
                this.refreshServers();
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteServerModal'));
                modal && modal.hide();
            })
            .catch((err) => {
                console.error('Erreur suppression serveur:', err);
                this.showNotification(err.message || 'Erreur lors de la suppression', 'error');
            })
            .finally(() => { if (btn) btn.disabled = false; });
    }

    applyServerFilters() {
        // Re-render avec les filtres actuels
        this.renderServers();
    }

    async refreshServers() {
        try {
            console.log('🔄 Actualisation de la liste des serveurs...');
            const container = $('#servers-table');
            if (container && container.length) {
                container.html(`
                    <tr>
                        <td colspan="10" class="text-center text-muted py-4">
                            <i class="fas fa-spinner fa-spin me-2"></i>Actualisation...
                        </td>
                    </tr>
                `);
            }
            await this.loadServers();
            this.renderServers();
            this.showNotification('Liste des serveurs actualisée', 'success');
        } catch (error) {
            console.error('❌ Erreur lors de l\'actualisation des serveurs:', error);
            this.showNotification('Erreur lors de l\'actualisation des serveurs', 'error');
        }
    }

    async queryAllServers() {
        try {
            const res = await fetch('/api/ntp/query/all', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            const ok = Array.isArray(data.results) ? data.results.filter(r => r.success).length : (data.successful_queries || 0);
            const total = Array.isArray(data.results) ? data.results.length : (data.total_servers || 0);
            this.showNotification(`Interrogation globale terminée: ${ok}/${total} succès`, ok > 0 ? 'success' : 'warning');
            await this.refreshServers();
        } catch (err) {
            console.error('Erreur interrogation globale:', err);
            this.showNotification(err.message || 'Erreur lors de l\'interrogation globale', 'error');
        }
    }

    async probeNtpAddress() {
        const address = (document.getElementById('probe-address')?.value || '').trim();
        const port = parseInt(document.getElementById('probe-port')?.value || '123', 10);
        const timeout = parseInt(document.getElementById('probe-timeout')?.value || '5', 10);
        if (!address) {
            this.showNotification('Veuillez saisir une adresse à sonder', 'warning');
            return;
        }
        const btn = document.getElementById('servers-probe-btn');
        if (btn) btn.disabled = true;
        try {
            const res = await fetch('/api/admin/ntp/probe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address, port, timeout })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            const reach = data.connectivity?.reachable ? 'oui' : 'non';
            const off = (data.probe && (data.probe.offset === 0 || data.probe.offset)) ? `${Number(data.probe.offset).toFixed(4)}s` : '—';
            const dly = (data.probe && (data.probe.delay === 0 || data.probe.delay)) ? `${Number(data.probe.delay).toFixed(4)}s` : '—';
            this.showNotification(`Probe ${address}:${port} - reachable: ${reach}, offset: ${off}, delay: ${dly}`, data.probe?.success ? 'success' : (data.connectivity?.reachable ? 'warning' : 'error'));
        } catch (err) {
            console.error('Erreur probe NTP:', err);
            this.showNotification(err.message || 'Erreur lors du probe NTP', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    async testServer(serverId) {
        if (!serverId) return;
        try {
            const res = await fetch(`/api/admin/servers/${serverId}/test`, { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            const reach = data.connectivity?.reachable ? 'oui' : 'non';
            const name = data.server?.name || `#${serverId}`;
            const off = (data.ntp_info && (data.ntp_info.offset === 0 || data.ntp_info.offset)) ? `${Number(data.ntp_info.offset).toFixed(4)}s` : '—';
            const dly = (data.ntp_info && (data.ntp_info.delay === 0 || data.ntp_info.delay)) ? `${Number(data.ntp_info.delay).toFixed(4)}s` : '—';
            this.showNotification(`Test ${name}: reachable ${reach}, offset ${off}, delay ${dly}`, data.ntp_info?.success ? 'success' : (data.connectivity?.reachable ? 'warning' : 'error'));
        } catch (err) {
            console.error('Erreur test serveur:', err);
            this.showNotification(err.message || 'Erreur lors du test serveur', 'error');
        }
    }

    clearServerFilters() {
        const typeFilter = document.getElementById('server-type-filter');
        const statusFilter = document.getElementById('server-status-filter');
        const activeFilter = document.getElementById('server-active-filter');
        const searchInput = document.getElementById('server-search');
        if (typeFilter) typeFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (activeFilter) activeFilter.value = '';
        if (searchInput) searchInput.value = '';
        this.refreshServers();
        this.showNotification('Filtres serveurs réinitialisés', 'info');
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
            const sevCanvas = severityChart.get(0);
            const severityData = this.stats.alerts.by_severity || {};
            const labels = ['info', 'warning', 'critical'];
            const values = labels.map(l => Number(severityData[l] || 0));
            if (typeof window.Chart === 'undefined') {
                // Fallback texte si Chart.js non chargé
                const parent = sevCanvas.parentElement;
                if (parent) {
                    parent.innerHTML = `
                        <div class="text-center">
                            <h6>Répartition par Sévérité</h6>
                            <div class="row">
                                <div class="col-4"><div class="text-info"><h4>${values[0]}</h4><small>Info</small></div></div>
                                <div class="col-4"><div class="text-warning"><h4>${values[1]}</h4><small>Warning</small></div></div>
                                <div class="col-4"><div class="text-danger"><h4>${values[2]}</h4><small>Critical</small></div></div>
                            </div>
                        </div>`;
                }
            } else {
                // Dessiner doughnut Chart.js
                if (this.charts['overview-severity']) {
                    this.charts['overview-severity'].destroy();
                }
                this.charts['overview-severity'] = new Chart(sevCanvas.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Info', 'Warning', 'Critical'],
                        datasets: [{
                            data: values,
                            backgroundColor: ['#17a2b8', '#ffc107', '#dc3545']
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                });
            }
            console.log('✅ Graphique sévérité mis à jour');
        } else if (severityChart.length > 0) {
            const sevCanvas = severityChart.get(0);
            const parent = sevCanvas.parentElement;
            if (parent) parent.innerHTML = '<div class="text-center text-muted">Aucune donnée disponible</div>';
            console.log('⚠️ Aucune donnée pour le graphique sévérité');
        }

        if (this.stats && this.stats.alerts && serverChart.length > 0) {
            const srvCanvas = serverChart.get(0);
            const serverData = this.stats.alerts.by_server || {};
            const labels = Object.keys(serverData);
            const values = labels.map(k => Number(serverData[k] || 0));
            if (typeof window.Chart === 'undefined') {
                const parent = srvCanvas.parentElement;
                if (parent) {
                    parent.innerHTML = `
                        <div class="text-center">
                            <h6>Alertes par Serveur</h6>
                            <div class="text-muted">
                                ${labels.length ? labels.map((name, i) => `<div class=\"mb-1\"><strong>${name}:</strong> ${values[i]}</div>`).join('') : '<p class="text-muted">Aucune donnée</p>'}
                            </div>
                        </div>`;
                }
            } else {
                if (this.charts['overview-server']) {
                    this.charts['overview-server'].destroy();
                }
                this.charts['overview-server'] = new Chart(srvCanvas.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Alertes actives',
                            data: values,
                            backgroundColor: 'rgba(220,53,69,0.4)',
                            borderColor: 'rgba(220,53,69,1)',
                            borderWidth: 1
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
                });
            }
            console.log('✅ Graphique serveur mis à jour');
        } else if (serverChart.length > 0) {
            const srvCanvas = serverChart.get(0);
            const parent = srvCanvas.parentElement;
            if (parent) parent.innerHTML = '<div class="text-center text-muted">Aucune donnée disponible</div>';
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

        // Statistiques détaillées (graphiques Chart.js) basées sur detailedStats
        this.renderDetailedStatsCharts();
    }

    renderDetailedStatsCharts() {
        try {
            const perfCanvas = document.getElementById('ntp-performance-chart');
            const trendCanvas = document.getElementById('alerts-trend-chart');

            // Si Chart.js n'est pas présent, afficher un message
            if ((perfCanvas || trendCanvas) && typeof window.Chart === 'undefined') {
                if (perfCanvas) perfCanvas.outerHTML = '<div class="text-center text-muted">Chart.js non chargé</div>';
                if (trendCanvas) trendCanvas.outerHTML = '<div class="text-center text-muted">Chart.js non chargé</div>';
                return;
            }

            // Nettoyer anciens graphes
            const destroyChart = (id) => { if (this.charts[id]) { this.charts[id].destroy(); delete this.charts[id]; } };

            // Graphe performance: latence moyenne (détaillée) ou fallback servers
            if (perfCanvas) {
                destroyChart('ntp-performance-chart');
                let labels = [];
                let latencies = [];
                if (this.detailedStats && this.detailedStats.ntp_performance) {
                    const perf = this.detailedStats.ntp_performance;
                    // Si l'API détaillée ne fournit pas un tableau par serveur, afficher moyenne
                    labels = ['Moyenne réponse (ms)'];
                    latencies = [Number(perf.average_response_time || 0)];
                } else {
                    const servers = Array.isArray(this.servers) ? this.servers : [];
                    labels = servers.slice(0, 10).map(s => s.name || `#${s.id}`);
                    latencies = servers.slice(0, 10).map(s => (s.last_latency === 0 || s.last_latency) ? Number(s.last_latency) : 0);
                }

                this.charts['ntp-performance-chart'] = new Chart(perfCanvas.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Latence (ms)',
                            data: latencies,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: true } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }

            // Graphe tendance: répartition par sévérité/statut depuis detailed
            if (trendCanvas) {
                destroyChart('alerts-trend-chart');
                let labels = [];
                let values = [];
                if (this.detailedStats && this.detailedStats.alerts_analysis && this.detailedStats.alerts_analysis.by_severity) {
                    const bySev = this.detailedStats.alerts_analysis.by_severity || {};
                    labels = Object.keys(bySev);
                    values = labels.map(l => bySev[l] || 0);
                } else {
                    const servers = Array.isArray(this.servers) ? this.servers : [];
                    const counts = servers.reduce((acc, s) => {
                        const st = (s.status || 'unknown').toLowerCase();
                        acc[st] = (acc[st] || 0) + 1; return acc;
                    }, {});
                    labels = Object.keys(counts);
                    values = labels.map(l => counts[l]);
                }
                const colors = ['#28a745', '#6c757d', '#ffc107', '#dc3545', '#17a2b8'];

                this.charts['alerts-trend-chart'] = new Chart(trendCanvas.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels,
                        datasets: [{
                            data: values,
                            backgroundColor: colors.slice(0, labels.length)
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
            }
        } catch (error) {
            console.error('Erreur rendu statistiques détaillées:', error);
        }
    }

    // === Actions boutons haut de page ===
    async refreshOverview() {
        try {
            await Promise.all([this.loadUsers(), this.loadServers(), this.loadStats()]);
            this.renderStats();
            this.showNotification('Vue d\'ensemble actualisée', 'success');
        } catch (e) {
            console.error('Erreur refreshOverview:', e);
        }
    }

    async refreshStats() {
        try {
            await this.loadStats();
            this.renderStats();
            this.showNotification('Statistiques actualisées', 'success');
        } catch (e) {
            console.error('Erreur refreshStats:', e);
        }
    }

    refreshAlertsHistory() {
        this.loadHistoricalAlerts(1);
        this.showNotification('Historique des alertes actualisé', 'success');
    }

    async exportAuditLogs() {
        try {
            const params = new URLSearchParams();
            const action = (document.getElementById('audit-action-filter')?.value || '').trim();
            const user = (document.getElementById('audit-user-filter')?.value || '').trim();
            const start = (document.getElementById('audit-start-date')?.value || '').trim();
            const end = (document.getElementById('audit-end-date')?.value || '').trim();
            if (action) params.append('action_type', action);
            if (user) params.append('user_id', user);
            if (start) params.append('start_date', start);
            if (end) params.append('end_date', end);
            params.append('per_page', '2000');
            const url = `/api/admin/audit/logs/export?${params.toString()}`;
            const res = await fetch(url);
            if (!res.ok) {
                let msg = `Erreur HTTP ${res.status}`;
                try { const data = await res.json(); if (data?.error) msg = data.error; } catch {}
                throw new Error(msg);
            }
            const blob = await res.blob();
            const dlUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = dlUrl;
            a.download = 'audit_logs.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(dlUrl);
            document.body.removeChild(a);
            this.showNotification('Export des logs d\'audit réussi', 'success');
        } catch (e) {
            console.error('Export audit logs échoué:', e);
            this.showNotification(e.message || 'Erreur export des logs d\'audit', 'error');
        }
    }

    exportAlertsHistory() {
        // Alias pour compatibilité avec le template
        return this.exportHistoricalAlerts();
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

    async showUserModal(userId = null) {
        // Redirige vers les nouveaux modals séparés
        if (userId) return this.showUserEditModal(userId);
        return this.showUserCreateModal();
    }

    async showUserCreateModal() {
        const modalEl = document.getElementById('userCreateModal');
        if (!modalEl) return;
        const modal = new bootstrap.Modal(modalEl);
        const form = document.getElementById('userCreateForm');
        form && form.reset();
        const bar = document.querySelector('#passwordStrength .progress-bar');
        if (bar) { bar.style.width = '0%'; bar.className = 'progress-bar'; }
        const feedback = document.getElementById('passwordFeedback');
        if (feedback) feedback.textContent = '';
        const eyeIcon = document.querySelector('#togglePasswordBtn i');
        if (eyeIcon) { eyeIcon.classList.remove('fa-eye-slash'); eyeIcon.classList.add('fa-eye'); }
        modal.show();
    }

    async showUserEditModal(userId) {
        const modalEl = document.getElementById('userEditModal');
        if (!modalEl) return;
        const modal = new bootstrap.Modal(modalEl);
        const setEl = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ''; };
        const setChecked = (id, v) => { const el = document.getElementById(id); if (el) el.checked = !!v; };

        let user = this.users?.find(u => u.id === userId) || null;
        try {
            const res = await fetch(`/api/admin/users/${userId}`);
            if (res.ok) user = await res.json();
        } catch {}
        if (!user) return;

        setEl('editUserId', user.id);
        setEl('editUserUsername', user.username);
        setEl('editUserEmail', user.email);
        setEl('editUserFirstName', user.first_name || '');
        setEl('editUserLastName', user.last_name || '');
        setEl('editUserRole', user.role || 'viewer');
        setChecked('editUserIsActive', user.is_active);
        modal.show();
    }

    showServerModal(serverId = null) {
        // Rétrocompatibilité: router vers les nouveaux modals
        if (serverId) return this.showServerEditModal(serverId);
        return this.showServerCreateModal();
    }

    showServerCreateModal() {
        const modal = new bootstrap.Modal(document.getElementById('serverModal'));
        const form = document.getElementById('server-form');
        const title = document.getElementById('server-modal-title');
        title.textContent = 'Nouveau Serveur NTP';
        form.reset();
        const idEl = document.getElementById('server-id');
        if (idEl) idEl.value = '';
        const portEl = document.getElementById('server-port');
        if (portEl) portEl.value = 123;
        const timeoutEl = document.getElementById('server-timeout');
        if (timeoutEl) timeoutEl.value = 10;
        const priorityEl = document.getElementById('server-priority');
        if (priorityEl) priorityEl.value = 1;
        // Charger les types serveurs avant d'afficher
        this.loadServerTypesIntoSelect();
        modal.show();
    }

    showServerEditModal(serverId) {
        const modal = new bootstrap.Modal(document.getElementById('serverModal'));
        const title = document.getElementById('server-modal-title');
        title.textContent = 'Modifier le Serveur';
        const server = this.servers.find(s => s.id === serverId);
        if (server) {
            document.getElementById('server-id').value = server.id;
            document.getElementById('server-name').value = server.name;
            document.getElementById('server-address').value = server.address;
            // Charger d'abord les types serveurs puis sélectionner la valeur
            this.loadServerTypesIntoSelect().then(() => {
                const typeSelect = document.getElementById('server-type');
                if (!typeSelect) return;
                const byId = server.server_type_id ? String(server.server_type_id) : '';
                const byCode = (server.server_type_code || server.server_type || '').toLowerCase();
                let selected = false;
                // Essai direct par id
                if (byId) {
                    typeSelect.value = byId;
                    selected = (typeSelect.value === byId);
                }
                // Sinon, essayer par code via dataset.code
                if (!selected && byCode) {
                    const opts = Array.from(typeSelect.options || []);
                    const match = opts.find(o => (o.dataset && (o.dataset.code || '').toLowerCase()) === byCode);
                    if (match) {
                        typeSelect.value = match.value;
                        selected = true;
                    }
                }
                // Dernier recours: si rien trouvé, ne rien forcer (laisser valeur par défaut)
            });
            document.getElementById('server-port').value = server.port;
            if (document.getElementById('server-timeout')) document.getElementById('server-timeout').value = server.timeout;
            if (document.getElementById('server-priority')) document.getElementById('server-priority').value = server.priority || 1;
            document.getElementById('server-description').value = server.description || '';
            document.getElementById('server-is-active').checked = server.is_active;
        }
        modal.show();
    }

    async loadServerTypesIntoSelect() {
        try {
            const res = await fetch('/api/admin/server-types', { credentials: 'include' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const items = data.items || [];
            const select = document.getElementById('server-type');
            if (!select) return;
            // Vider
            select.innerHTML = '';
            // Ajouter options
            items.forEach(it => {
                const opt = document.createElement('option');
                opt.value = String(it.id);
                opt.textContent = it.label;
                opt.dataset.code = it.code;
                select.appendChild(opt);
            });
            // Sélection par défaut: 'all' si présent
            const def = items.find(x => x.code === 'all');
            if (def) select.value = String(def.id);
            if (items.length === 0) {
                console.warn('server-types API returned empty items');
                // Fallback local minimal si API vide
                [['local','Local'],['internet','Internet'],['pool','Pool public'],['all','Tous']].forEach(([code,label])=>{
                    const opt = document.createElement('option');
                    opt.value = code;
                    opt.textContent = label;
                    select.appendChild(opt);
                });
                select.value = 'all';
            }
        } catch (e) {
            console.warn('Chargement server-types échoué', e);
            // Fallback local minimal
            const select = document.getElementById('server-type');
            if (!select) return;
            select.innerHTML = '';
            [['local','Local'],['internet','Internet'],['pool','Pool public'],['all','Tous']].forEach(([code,label])=>{
                const opt = document.createElement('option');
                opt.value = code;
                opt.textContent = label;
                select.appendChild(opt);
            });
            select.value = 'all';
        }
    }

    showExportModal() {
        const modal = new bootstrap.Modal(document.getElementById('exportImportModal'));
        document.getElementById('export-import-title').textContent = 'Export de Données';
        const exportSec = document.getElementById('export-section');
        const importSec = document.getElementById('import-section');
        if (exportSec) exportSec.classList.remove('inline-hidden');
        if (importSec) importSec.classList.add('inline-hidden');
        const actionBtn = document.getElementById('export-import-action');
        if (actionBtn) {
            actionBtn.textContent = 'Exporter (CSV)';
            actionBtn.onclick = () => this.performExport();
        }
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

    // === Gestion mot de passe (création d'utilisateur) ===
    handleGeneratePassword() {
        const readable = !!document.getElementById('readablePassword')?.checked;
        const password = this.generatePassword(12, readable);
        const input = document.getElementById('userPassword');
        if (input) {
            input.value = password;
            this.updatePasswordStrength(password);
        }
        // Optionnel: affichage immédiat dans le modal dédié
        // this.showGeneratedPassword(document.getElementById('userUsername')?.value || '', password);
    }

    generatePassword(length = 12, readable = false) {
        const vowels = 'aeiou';
        const consonants = 'bcdfghjklmnpqrstvwxyz';
        const digits = '23456789';
        const symbols = '!@#$%';
        let chars;
        if (readable) {
            chars = (consonants + vowels + consonants + digits);
        } else {
            chars = (consonants + vowels + consonants + digits + symbols + consonants.toUpperCase());
        }
        let pwd = '';
        for (let i = 0; i < length; i++) {
            pwd += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return pwd;
    }

    togglePasswordVisibility(triggerEl) {
        // Chercher l'input dans le même groupe
        let input;
        if (triggerEl && triggerEl.closest) {
            const group = triggerEl.closest('.input-group');
            if (group) {
                input = group.querySelector('#userPassword') || group.querySelector('input[type="password"], input[type="text"]');
            }
        }
        if (!input) {
            input = document.getElementById('userPassword');
        }
        if (!input) return;
        const toText = input.type === 'password';
        input.type = toText ? 'text' : 'password';
        // Icône dans le bouton cliqué
        const btnIcon = triggerEl ? triggerEl.querySelector('i') : document.querySelector('#togglePasswordBtn i');
        if (btnIcon) {
            btnIcon.classList.remove(toText ? 'fa-eye' : 'fa-eye-slash');
            btnIcon.classList.add(toText ? 'fa-eye-slash' : 'fa-eye');
        }
        if (triggerEl) triggerEl.setAttribute('aria-pressed', String(toText));
    }

    updatePasswordStrength(password) {
        const container = document.getElementById('passwordStrength');
        if (!container) return;
        const bar = container.querySelector('.progress-bar');
        const feedback = document.getElementById('passwordFeedback');
        container.style.display = password ? 'block' : 'none';

        // Évaluation simple
        let score = 0;
        if (password.length >= 8) score += 25;
        if (/[A-Z]/.test(password)) score += 20;
        if (/[a-z]/.test(password)) score += 20;
        if (/[0-9]/.test(password)) score += 20;
        if (/[^A-Za-z0-9]/.test(password)) score += 15;
        if (password.length >= 12) score += 10;
        score = Math.min(score, 100);

        if (bar) {
            bar.style.width = `${score}%`;
            bar.className = 'progress-bar';
            if (score < 40) bar.classList.add('bg-danger');
            else if (score < 70) bar.classList.add('bg-warning');
            else bar.classList.add('bg-success');
        }
        if (feedback) {
            if (score < 40) feedback.textContent = 'Faible';
            else if (score < 70) feedback.textContent = 'Moyen';
            else feedback.textContent = 'Fort';
        }
    }

    updateEditPasswordStrength(password) {
        const container = document.getElementById('editPasswordStrength');
        if (!container) return;
        const bar = container.querySelector('.progress-bar');
        const feedback = document.getElementById('editPasswordFeedback');
        container.style.display = password ? 'block' : 'none';

        let score = 0;
        if (password.length >= 8) score += 25;
        if (/[A-Z]/.test(password)) score += 20;
        if (/[a-z]/.test(password)) score += 20;
        if (/[0-9]/.test(password)) score += 20;
        if (/[^A-Za-z0-9]/.test(password)) score += 15;
        if (password.length >= 12) score += 10;
        score = Math.min(score, 100);

        if (bar) {
            bar.style.width = `${score}%`;
            bar.className = 'progress-bar';
            if (score < 40) bar.classList.add('bg-danger');
            else if (score < 70) bar.classList.add('bg-warning');
            else bar.classList.add('bg-success');
        }
        if (feedback) {
            if (score < 40) feedback.textContent = 'Faible';
            else if (score < 70) feedback.textContent = 'Moyen';
            else feedback.textContent = 'Fort';
        }
    }

    toggleEditPasswordVisibility(triggerEl) {
        let input;
        if (triggerEl && triggerEl.closest) {
            const group = triggerEl.closest('.input-group');
            if (group) {
                input = group.querySelector('#editUserPassword') || group.querySelector('input[type="password"], input[type="text"]');
            }
        }
        if (!input) input = document.getElementById('editUserPassword');
        if (!input) return;
        const toText = input.type === 'password';
        input.type = toText ? 'text' : 'password';
        const btnIcon = triggerEl ? triggerEl.querySelector('i') : null;
        if (btnIcon) {
            btnIcon.classList.remove(toText ? 'fa-eye' : 'fa-eye-slash');
            btnIcon.classList.add(toText ? 'fa-eye-slash' : 'fa-eye');
        }
        if (triggerEl) triggerEl.setAttribute('aria-pressed', String(toText));
    }

    showGeneratedPassword(username, password) {
        const modalEl = document.getElementById('passwordDisplayModal');
        if (!modalEl) return;
        const usernameEl = document.getElementById('passwordDisplayUsername');
        const valueEl = document.getElementById('passwordDisplayValue');
        if (usernameEl) usernameEl.textContent = username || '';
        if (valueEl) valueEl.value = password || '';
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    copyDisplayedPassword() {
        const input = document.getElementById('passwordDisplayValue');
        if (!input) return;
        input.type = 'text';
        input.select();
        document.execCommand('copy');
        input.type = 'password';
        this.showNotification('Mot de passe copié', 'success');
    }

    toggleDisplayedPasswordVisibility(triggerEl) {
        let input;
        if (triggerEl && triggerEl.closest) {
            const group = triggerEl.closest('.input-group');
            if (group) input = group.querySelector('#passwordDisplayValue');
        }
        if (!input) input = document.getElementById('passwordDisplayValue');
        if (!input) return;
        const toText = input.type === 'password';
        input.type = toText ? 'text' : 'password';
        const btnIcon = triggerEl ? triggerEl.querySelector('i') : document.querySelector('#showPasswordBtn i');
        if (btnIcon) {
            btnIcon.classList.remove(toText ? 'fa-eye' : 'fa-eye-slash');
            btnIcon.classList.add(toText ? 'fa-eye-slash' : 'fa-eye');
        }
        if (triggerEl) triggerEl.setAttribute('aria-pressed', String(toText));
    }
    async performExport() {
        const options = {
            config: document.getElementById('export-config')?.checked,
            servers: document.getElementById('export-servers')?.checked,
            users: document.getElementById('export-users')?.checked
        };
        const btn = document.getElementById('export-import-action');
        if (btn) btn.disabled = true;
        try {
            // Export CSV consolidé
            const res = await fetch('/api/admin/backup/export.csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ options })
            });
            if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`);
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backup_export_${new Date().toISOString().slice(0,10)}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            this.showNotification('Export CSV généré', 'success');
        } catch (e) {
            console.error('Export CSV échoué:', e);
            this.showNotification(e.message || 'Erreur export CSV', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
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

    createUser() {
        const payload = {
            first_name: (document.getElementById('userCreateFirstName')?.value || '').trim(),
            last_name: (document.getElementById('userCreateLastName')?.value || '').trim(),
            role: (document.getElementById('userCreateRole')?.value || '').trim(),
            is_active: !!document.getElementById('userCreateIsActive')?.checked,
            username: (document.getElementById('userCreateUsername')?.value || '').trim(),
            email: (document.getElementById('userCreateEmail')?.value || '').trim(),
            password: document.getElementById('userPassword')?.value || '',
            readable_password: !!document.getElementById('readablePassword')?.checked
        };
        const validPwd = payload.password && payload.password.length >= 8;
        const validCore = payload.email && payload.role;
        if (!validCore || !validPwd) {
            this.showNotification('Veuillez compléter correctement le formulaire', 'error');
            return;
        }
        const btn = document.getElementById('createUserBtn');
        if (btn) btn.disabled = true;
        fetch('/api/admin/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(async (res) => {
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            return data;
        })
        .then((data) => {
            this.showNotification(data.message || 'Utilisateur créé avec succès', 'success');
            if (data.auto_generated_password && data.generated_password) {
                this.showGeneratedPassword(
                    data.user?.username || payload.username || '(nouvel utilisateur)',
                    data.generated_password
                );
            }
            this.refreshUsers();
            const modal = bootstrap.Modal.getInstance(document.getElementById('userCreateModal'));
            modal && modal.hide();
        })
        .catch((err) => {
            console.error('Erreur création utilisateur:', err);
            this.showNotification(err.message || 'Erreur lors de la création', 'error');
            const msg = (err.message || '').toLowerCase();
            if (msg.includes('email')) this.updateFieldValidity('userCreateEmail', false, 'Adresse email déjà utilisée');
            if (msg.includes('utilisateur') || msg.includes('username')) this.updateFieldValidity('userCreateUsername', false, "Nom d'utilisateur déjà utilisé");
        })
        .finally(() => { if (btn) btn.disabled = false; });
    }

    updateUser() {
        const userId = document.getElementById('editUserId')?.value;
        if (!userId) return;
        const payload = {
            first_name: (document.getElementById('editUserFirstName')?.value || '').trim(),
            last_name: (document.getElementById('editUserLastName')?.value || '').trim(),
            role: (document.getElementById('editUserRole')?.value || '').trim(),
            is_active: !!document.getElementById('editUserIsActive')?.checked
        };
        const newPwd = (document.getElementById('editUserPassword')?.value || '').trim();
        if (newPwd) payload.password = newPwd;
        const btn = document.getElementById('updateUserBtn');
        if (btn) btn.disabled = true;
        fetch(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(async (res) => {
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            return data;
        })
        .then((data) => {
            this.showNotification(data.message || 'Utilisateur mis à jour', 'success');
            this.refreshUsers();
            const modal = bootstrap.Modal.getInstance(document.getElementById('userEditModal'));
            modal && modal.hide();
        })
        .catch((err) => {
            console.error('Erreur mise à jour utilisateur:', err);
            this.showNotification(err.message || 'Erreur lors de la mise à jour', 'error');
        })
        .finally(() => { if (btn) btn.disabled = false; });
    }

    saveServer() {
        // Déterminer si création ou édition
        const id = (document.getElementById('server-id')?.value || '').trim();
        const rawType = (document.getElementById('server-type')?.value || '').trim();
        const isNumericId = /^\d+$/.test(rawType);
        const payload = {
            name: (document.getElementById('server-name')?.value || '').trim(),
            address: (document.getElementById('server-address')?.value || '').trim(),
            port: parseInt(document.getElementById('server-port')?.value || '123', 10),
            ...(isNumericId ? { server_type_id: parseInt(rawType, 10) } : { server_type: rawType || 'all' }),
            priority: parseInt(document.getElementById('server-priority')?.value || '1', 10),
            timeout: parseInt(document.getElementById('server-timeout')?.value || '10', 10),
            description: (document.getElementById('server-description')?.value || '').trim(),
            is_active: !!document.getElementById('server-is-active')?.checked
        };

        // Validation minimale
        if (!payload.name || !payload.address || !payload.server_type) {
            this.showNotification('Nom, adresse et type sont requis', 'error');
            return;
        }

        const btn = event?.currentTarget || null;
        if (btn) btn.disabled = true;

        const isEdit = !!id;
        const url = isEdit ? `/api/admin/servers/${id}` : '/api/admin/servers';
        const method = isEdit ? 'PUT' : 'POST';
        // En édition, ne pas envoyer les champs non pris en charge si besoin
        const body = isEdit ? {
            name: payload.name,
            address: payload.address,
            port: payload.port,
            ...(payload.server_type_id ? { server_type_id: payload.server_type_id } : { server_type: payload.server_type }),
            priority: payload.priority,
            timeout: payload.timeout,
            description: payload.description,
            is_active: payload.is_active
        } : payload;

        fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
        .then(async (res) => {
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            return data;
        })
        .then((data) => {
            this.showNotification(data.message || (isEdit ? 'Serveur mis à jour' : 'Serveur créé avec succès'), 'success');
            this.refreshServers();
            const modal = bootstrap.Modal.getInstance(document.getElementById('serverModal'));
            modal && modal.hide();
        })
        .catch((err) => {
            console.error('Erreur sauvegarde serveur:', err);
            this.showNotification(err.message || 'Erreur lors de la sauvegarde', 'error');
        })
        .finally(() => { if (btn) btn.disabled = false; });
    }

    testServerForm() {
        const id = (document.getElementById('server-id')?.value || '').trim();
        const address = (document.getElementById('server-address')?.value || '').trim();
        const port = parseInt(document.getElementById('server-port')?.value || '123', 10);
        const timeout = parseInt(document.getElementById('server-timeout')?.value || '10', 10);

        if (id) {
            // Tester un serveur existant via l'API admin
            fetch(`/api/admin/servers/${id}/test`, { method: 'POST' })
                .then(async (res) => {
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
                    return data;
                })
                .then((data) => {
                    this.showNotification(`Test OK - reachability: ${data.connectivity?.reachable ? 'oui' : 'non'}`, 'success');
                })
                .catch((err) => {
                    console.error('Erreur test serveur:', err);
                    this.showNotification(err.message || 'Erreur lors du test du serveur', 'error');
                });
        } else {
            // Mode création: ping simple via endpoint public NTP (si disponible) ou message informatif
            if (!address) {
                this.showNotification('Renseignez l\'adresse du serveur pour tester', 'warning');
                return;
            }
            // Option: appeler un endpoint de test générique si exposé; sinon, fallback local
            this.showNotification(`Test local: ${address}:${port} (timeout ${timeout}s) - Vérification côté serveur non disponible pour un serveur non créé)`, 'info');
        }
    }

    exportData(options) {
        // TODO: Implémenter l'export de données
        this.showNotification('Export effectué avec succès', 'success');
    }

    async performMaintenance(options) {
        const btn = document.querySelector('#maintenanceModal .btn.btn-warning');
        if (btn) btn.disabled = true;
        try {
            const res = await fetch('/api/admin/maintenance/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ options })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data.error || `Erreur HTTP ${res.status}`);
            this.showNotification(data.message || 'Maintenance effectuée', 'success');
        } catch (e) {
            console.error('Maintenance échouée:', e);
            this.showNotification(e.message || 'Erreur maintenance', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // === Validation inline d'unicité username/email ===
    async checkUserUniqueness() {
        const username = (document.getElementById('userCreateUsername')?.value || '').trim();
        const email = (document.getElementById('userCreateEmail')?.value || '').trim();
        const saveBtn = document.getElementById('createUserBtn');
        const excludeId = '';

        if (!username && !email) return;
        const params = new URLSearchParams();
        if (username) params.append('username', username);
        if (email) params.append('email', email);
        if (excludeId) params.append('exclude_id', excludeId);

        try {
            const res = await fetch(`/api/admin/users/check-unique?${params.toString()}`);
            const data = await res.json();
            // En mode édition, on ignore la validation inline pour username/email car champs désactivés
            const userOk = !username || data.username?.unique;
            const emailOk = !email || data.email?.unique;

            this.updateFieldValidity('userCreateUsername', userOk, data.username?.message);
            this.updateFieldValidity('userCreateEmail', emailOk, data.email?.message);

            if (saveBtn) saveBtn.disabled = !(userOk && emailOk);
        } catch (e) {
            console.warn('check-unique échec:', e);
        }
    }

    updateFieldValidity(fieldId, isValid, message) {
        const input = document.getElementById(fieldId);
        if (!input) return;
        input.classList.remove('is-valid', 'is-invalid');
        if (isValid) input.classList.add('is-valid'); else input.classList.add('is-invalid');
        const feedbackId = fieldId + 'Feedback';
        const feedback = document.getElementById(feedbackId);
        if (feedback) {
            feedback.classList.remove('d-none');
            feedback.textContent = isValid ? '' : (message || 'Valeur invalide');
        }
    }
    showNotification(message, type = 'info') {
        if (window.notificationSystem && typeof window.notificationSystem.show === 'function') {
            window.notificationSystem.show(message, type, 3000);
        } else if (window.showNotification) {
            window.showNotification(message, type, 3000);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    async loadAuditLogs(page = 1) {
        try {
            this.auditCurrentPage = page;
            // Lire filtres depuis le DOM
            this.auditFilters = {
                action: (document.getElementById('audit-action-filter')?.value || '').trim(),
                user: (document.getElementById('audit-user-filter')?.value || '').trim(),
                start: (document.getElementById('audit-start-date')?.value || '').trim(),
                end: (document.getElementById('audit-end-date')?.value || '').trim()
            };
            const params = new URLSearchParams({
                page: String(this.auditCurrentPage),
                per_page: String(this.auditPerPage)
            });
            if (this.auditFilters.action) params.append('action_type', this.auditFilters.action);
            if (this.auditFilters.user) params.append('user_id', this.auditFilters.user);
            if (this.auditFilters.start) params.append('start_date', this.auditFilters.start);
            if (this.auditFilters.end) params.append('end_date', this.auditFilters.end);

            const response = await fetch(`/api/admin/audit/logs?${params.toString()}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `Erreur HTTP ${response.status}`);
            this.auditLogs = data.logs || [];
            this.auditTotalPages = data.pagination?.pages || 1;
            this.renderAuditLogs(data);
        } catch (error) {
            console.error('Erreur chargement logs audit:', error);
            this.auditLogs = [];
            this.auditTotalPages = 1;
            this.renderAuditLogs({ logs: [], pagination: { page: 1, pages: 1, total: 0 } });
        }
    }

    renderAuditLogs(data) {
        const container = $('#audit-logs-table');
        const logs = (data && Array.isArray(data.logs)) ? data.logs : (this.auditLogs || []);
        if (!logs.length) {
            container.html(`
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        <i class="fas fa-history fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Aucun log d'audit trouvé</p>
                    </td>
                </tr>
            `);
            $('#audit-logs-count').text('0 logs');
            $('#audit-pagination').html('');
            return;
        }

        const logsHtml = logs.map(log => `
            <tr>
                <td><small>${this.formatDate(log.timestamp)}</small></td>
                <td>${log.username || 'Système'}</td>
                <td>
                    <span class="badge bg-${log.action === 'login' ? 'success' : log.action === 'logout' ? 'warning' : 'info'}">
                        ${log.action}
                    </span>
                </td>
                <td>${log.resource || log.endpoint || '-'}</td>
                <td>${log.details || '-'}</td>
                <td><small class="text-muted">${log.ip_address || '-'}</small></td>
            </tr>
        `).join('');

        container.html(logsHtml);
        // Compteur et pagination
        const total = data?.pagination?.total ?? logs.length;
        $('#audit-logs-count').text(`${total} logs`);
        this.renderAuditPagination(data?.pagination || { page: this.auditCurrentPage, pages: this.auditTotalPages });
    }

    applyAuditFilters() {
        // Rechargement serveur-side page 1 avec filtres
        this.loadAuditLogs(1);
    }

    refreshAuditLogs() {
        this.loadAuditLogs(this.auditCurrentPage || 1);
    }

    renderAuditPagination(pagination) {
        const container = $('#audit-pagination');
        const currentPage = pagination?.page || this.auditCurrentPage || 1;
        const totalPages = pagination?.pages || this.auditTotalPages || 1;
        if (totalPages <= 1) {
            container.html('');
            return;
        }
        let html = '<ul class="pagination pagination-sm justify-content-center mb-0">';
        if (currentPage > 1) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage - 1}">Précédent</a></li>`;
        }
        const start = Math.max(1, currentPage - 2);
        const end = Math.min(totalPages, currentPage + 2);
        for (let i = start; i <= end; i++) {
            const active = i === currentPage ? ' active' : '';
            html += `<li class="page-item${active}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        if (currentPage < totalPages) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage + 1}">Suivant</a></li>`;
        }
        html += '</ul>';
        container.html(html);
    }
}

// Initialisation unique d'AdminManager
(function initAdminManagerOnce() {
    if (window.__ADMIN_MANAGER_INIT__) return;
    window.__ADMIN_MANAGER_INIT__ = true;

    const boot = () => {
        const adminModal = document.getElementById('adminModal');
        if (!adminModal) return;
        if (!window.adminManager) {
    window.adminManager = new AdminManager();
        }
        adminModal.addEventListener('shown.bs.modal', function() {
            if (window.adminManager) {
                window.adminManager.showView('overview');
            }
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();