/**
 * Dashboard JavaScript - NTP Monitor Enterprise
 */

let offsetChart = null;
let dashboardData = {};
let alertManager = null;

// Initialisation du dashboard
function initDashboard() {
    console.log('📊 Initialisation du dashboard NTP Monitor');
    
    // Utiliser le gestionnaire d'alertes global s'il existe
    if (window.alertManager) {
        alertManager = window.alertManager;
    }
    
    // Charger les données initiales
    loadDashboardData();
    
    // Initialiser le graphique
    initOffsetChart();
    
    // Programmer les mises à jour automatiques
    setInterval(loadDashboardData, 30000); // Toutes les 30 secondes
    
    // Charger les informations système
    loadSystemInfo();
    
    // Charger les statistiques d'alertes
    loadStatistics();
    
    // Démarrer les mises à jour automatiques
    startAutoRefresh();
}

// Charger les données du dashboard
function loadDashboardData() {
    fetch('/api/dashboard/summary')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Erreur chargement dashboard:', data.error);
                return;
            }
            
            dashboardData = data;
            updateDashboardDisplay(data);
        })
        .catch(error => {
            console.error('Erreur réseau dashboard:', error);
        });
}

// Mettre à jour l'affichage du dashboard
function updateDashboardDisplay(data) {
    // Mise à jour des statistiques générales
    document.getElementById('total-servers').textContent = data.servers.total;
    document.getElementById('synchronized-servers').textContent = data.servers.synchronized;
    document.getElementById('alerts-count').textContent = data.alerts.total;
    document.getElementById('clients-count').textContent = data.clients.total_connections;
    
    // Mise à jour des horloges serveurs
    updateServersClocks(data.servers.data);
    
    // Mise à jour des informations système
    updateSystemInfo(data.system);
    
    // Mise à jour du timestamp
    document.getElementById('last-update').textContent = 'Dernière MàJ: ' + new Date().toLocaleTimeString('fr-FR');
}

// Mettre à jour l'affichage des serveurs
function updateServersClocks(servers) {
    const container = document.getElementById('ntp-servers-clocks');
    
    if (!servers || servers.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted p-4">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Aucun serveur NTP configuré
            </div>
        `;
        return;
    }
    
    let html = '';
    
    servers.forEach((server, index) => {
        const statusClass = getStatusClass(server.status);
        const statusIcon = getStatusIcon(server.status);
        const serverTime = server.last_sync ? new Date(server.last_sync).toLocaleTimeString('fr-FR') : '--:--:--';
        const offsetDisplay = server.last_offset !== null ? 
            `${server.last_offset >= 0 ? '+' : ''}${(server.last_offset * 1000).toFixed(1)}ms` : '--';
        
        html += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card border-${statusClass}">
                    <div class="card-header bg-${statusClass} text-white">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">
                                <i class="${statusIcon} me-2"></i>${server.name}
                            </h6>
                            <span class="badge bg-light text-dark">${server.server_type}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="text-center mb-2">
                            <div class="h4 text-primary" id="server-time-${server.id}">
                                ${serverTime}
                            </div>
                            <small class="text-muted">${server.address}</small>
                        </div>
                        <div class="row text-center">
                            <div class="col-6">
                                <small class="text-muted">Écart</small>
                                <div class="fw-bold ${server.last_offset !== null && Math.abs(server.last_offset) > server.max_offset ? 'text-warning' : 'text-success'}">
                                    ${offsetDisplay}
                                </div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Latence</small>
                                <div class="fw-bold">
                                    ${server.last_latency !== null ? server.last_latency.toFixed(1) + 'ms' : '--'}
                                </div>
                            </div>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">Status: </small>
                            <span class="badge bg-${statusClass}">${getStatusLabel(server.status)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Mettre à jour les horloges en temps réel
    updateServerTimes(servers);
}

// Mettre à jour les informations système avec timezone
function updateSystemInfo(systemData) {
    if (!systemData) return;
    
    const localTime = new Date(systemData.local_time);
    const utcTime = new Date(systemData.utc_time);
    
    // Affichage de l'heure avec timezone
    document.getElementById('local-time').textContent = localTime.toLocaleTimeString('fr-FR');
    document.getElementById('utc-time').textContent = utcTime.toLocaleTimeString('fr-FR');
    document.getElementById('system-timezone').textContent = systemData.timezone || 'UTC';
    
    // Informations supplémentaires si disponibles
    if (systemData.utc_offset_hours !== undefined) {
        const offset = systemData.utc_offset_hours;
        const offsetStr = `UTC${offset >= 0 ? '+' : ''}${offset}`;
        document.getElementById('utc-offset').textContent = offsetStr;
        document.getElementById('local-timezone-info').textContent = `${systemData.timezone} (${offsetStr})`;
    }
    
    if (systemData.is_dst !== undefined) {
        document.getElementById('dst-status').textContent = systemData.is_dst ? 'Activée' : 'Désactivée';
    }
}

// Charger les informations système détaillées
function loadSystemInfo() {
    fetch('/api/system/time')
        .then(response => response.json())
        .then(data => {
            updateSystemInfo(data);
        })
        .catch(error => {
            console.error('Erreur chargement info système:', error);
        });
}

// Mettre à jour les horloges des serveurs en temps réel
function updateServerTimes(servers) {
    servers.forEach(server => {
        const element = document.getElementById(`server-time-${server.id}`);
        if (element && server.last_sync) {
            setInterval(() => {
                const now = new Date();
                const serverTime = new Date(now.getTime() + (server.last_offset || 0) * 1000);
                element.textContent = serverTime.toLocaleTimeString('fr-FR');
            }, 1000);
        }
    });
}

// Initialiser le graphique des écarts
function initOffsetChart() {
    const ctx = document.getElementById('offsetChart');
    if (!ctx) return;
    
    offsetChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution des écarts de synchronisation'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Écart (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Temps'
                    }
                }
            }
        }
    });
    
    // Charger les données du graphique
    loadOffsetChartData();
}

// Charger les données pour le graphique
function loadOffsetChartData() {
    fetch('/api/ntp/analytics/offset-trends?hours=24&interval=1')
        .then(response => response.json())
        .then(data => {
            if (data.trends && offsetChart) {
                updateOffsetChart(data.trends);
            }
        })
        .catch(error => {
            console.error('Erreur chargement données graphique:', error);
        });
}

// Mettre à jour le graphique des écarts
function updateOffsetChart(trends) {
    if (!offsetChart) return;
    
    const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];
    const datasets = [];
    let labels = [];
    
    Object.keys(trends).forEach((serverId, index) => {
        const serverData = trends[serverId];
        if (serverData.data && serverData.data.length > 0) {
            if (labels.length === 0) {
                labels = serverData.data.map(point => {
                    const date = new Date(point.timestamp);
                    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
                });
            }
            
            datasets.push({
                label: serverData.server_name,
                data: serverData.data.map(point => point.avg_offset * 1000), // Convertir en ms
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                fill: false,
                tension: 0.1
            });
        }
    });
    
    offsetChart.data.labels = labels;
    offsetChart.data.datasets = datasets;
    offsetChart.update();
}

// Fonctions utilitaires pour les status
function getStatusClass(status) {
    switch (status) {
        case 'ok': return 'success';
        case 'warning': return 'warning';
        case 'critical': return 'danger';
        case 'offline': return 'secondary';
        default: return 'secondary';
    }
}

function getStatusIcon(status) {
    switch (status) {
        case 'ok': return 'fas fa-check-circle';
        case 'warning': return 'fas fa-exclamation-triangle';
        case 'critical': return 'fas fa-exclamation-circle';
        case 'offline': return 'fas fa-times-circle';
        default: return 'fas fa-question-circle';
    }
}

function getStatusLabel(status) {
    switch (status) {
        case 'ok': return 'Synchronisé';
        case 'warning': return 'Avertissement';
        case 'critical': return 'Critique';
        case 'offline': return 'Hors ligne';
        default: return 'Inconnu';
    }
}

// Fonction pour mettre à jour les données du dashboard
function updateDashboardData(data) {
    if (data.success) {
        dashboardData = data;
        updateDashboardDisplay(data);
    }
}

// Fonction pour charger les données des serveurs NTP
async function loadNTPServers() {
    try {
        console.log('🌐 Chargement des serveurs NTP...');
        
        const response = await fetch('/api/ntp/servers');
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
            console.log(`✅ ${data.servers.length} serveurs NTP chargés`);
            updateNTPServersDisplay(data.servers);
        } else {
            throw new Error(data.error || 'Erreur lors du chargement des serveurs');
        }
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement des serveurs NTP:', error);
        $('#ntp-servers-container').html(`
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Erreur lors du chargement des serveurs NTP: ${error.message}
            </div>
        `);
    }
}

// Fonction pour mettre à jour l'affichage des serveurs NTP
function updateNTPServersDisplay(servers) {
    const container = $('#ntp-servers-container');
    
    if (!servers || servers.length === 0) {
        container.html(`
            <div class="text-center py-4">
                <i class="fas fa-server text-muted fa-3x mb-3"></i>
                <h6 class="text-muted">Aucun serveur NTP configuré</h6>
                <p class="text-muted">Veuillez configurer au moins un serveur NTP.</p>
                <button class="btn btn-primary btn-sm" onclick="openModal('configModal')">
                    <i class="fas fa-cog mr-1"></i>
                    Configurer
                </button>
            </div>
        `);
        return;
    }
    
    let serversHtml = '';
    servers.forEach(server => {
        const statusClass = getServerStatusClass(server.status);
        const statusIcon = getServerStatusIcon(server.status);
        const lastSync = server.last_sync ? 
            new Date(server.last_sync).toLocaleString('fr-FR') : 
            'Jamais';
        
        serversHtml += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card server-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">${server.name}</h6>
                            <span class="badge badge-${statusClass}">
                                ${statusIcon} ${server.status}
                            </span>
                        </div>
                        
                        <p class="text-muted mb-2">
                            <i class="fas fa-globe mr-1"></i>
                            ${server.address}:${server.port}
                        </p>
                        
                        <div class="row text-center mb-2">
                            <div class="col-4">
                                <small class="text-muted d-block">Offset</small>
                                <strong class="${server.last_offset && Math.abs(server.last_offset) > 1 ? 'text-warning' : ''}">
                                    ${server.last_offset ? (server.last_offset * 1000).toFixed(1) + 'ms' : 'N/A'}
                                </strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted d-block">Délai</small>
                                <strong>
                                    ${server.last_delay ? (server.last_delay * 1000).toFixed(1) + 'ms' : 'N/A'}
                                </strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted d-block">Stratum</small>
                                <strong>
                                    ${server.last_stratum || 'N/A'}
                                </strong>
                            </div>
                        </div>
                        
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar bg-${statusClass}" 
                                 style="width: ${server.availability || 0}%"></div>
                        </div>
                        
                        <div class="d-flex justify-content-between">
                            <small class="text-muted">
                                Disponibilité: ${(server.availability || 0).toFixed(1)}%
                            </small>
                            <small class="text-muted" title="Dernière synchronisation">
                                ${lastSync}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = serversHtml;
}

// Fonctions utilitaires pour les serveurs
function getServerStatusClass(status) {
    switch(status) {
        case 'online': return 'success';
        case 'offline': return 'danger';
        case 'warning': return 'warning';
        default: return 'secondary';
    }
}

function getServerStatusIcon(status) {
    switch(status) {
        case 'online': return '<i class="fas fa-check-circle"></i>';
        case 'offline': return '<i class="fas fa-times-circle"></i>';
        case 'warning': return '<i class="fas fa-exclamation-triangle"></i>';
        default: return '<i class="fas fa-question-circle"></i>';
    }
}

// Charger les statistiques et alertes
async function loadStatistics() {
    try {
        // Utiliser le gestionnaire d'alertes global s'il existe
        if (window.alertManager && typeof window.alertManager.getDashboardData === 'function') {
            const alertData = await window.alertManager.getDashboardData();
            if (alertData) {
                updateAlertsWidget(alertData);
            }
        } else {
            console.warn('⚠️ Gestionnaire d\'alertes non disponible');
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des statistiques:', error);
    }
}

// Fonction pour mettre à jour le widget des alertes
function updateAlertsWidget(alertData) {
    if (!alertData) return;
    
    // Mettre à jour les compteurs
    const dashboardTotalAlertsEl = document.getElementById('dashboard-total-alerts');
    const dashboardCriticalAlertsEl = document.getElementById('dashboard-critical-alerts');
    const dashboardWarningAlertsEl = document.getElementById('dashboard-warning-alerts');
    
    if (dashboardTotalAlertsEl) dashboardTotalAlertsEl.textContent = alertData.total_active || 0;
    if (dashboardCriticalAlertsEl) dashboardCriticalAlertsEl.textContent = alertData.critical || 0;
    if (dashboardWarningAlertsEl) dashboardWarningAlertsEl.textContent = alertData.warning || 0;
    
    // Mettre à jour l'indicateur de santé global
    let healthClass = 'success';
    let healthText = 'Système sain';
    
    if (alertData.critical > 0) {
        healthClass = 'danger';
        healthText = `${alertData.critical} alerte(s) critique(s)`;
    } else if (alertData.warning > 0) {
        healthClass = 'warning';
        healthText = `${alertData.warning} avertissement(s)`;
    }
    
    const systemHealthEl = document.getElementById('system-health');
    if (systemHealthEl) {
        systemHealthEl.innerHTML = `
            <span class="badge bg-${healthClass}">
                ${healthText}
            </span>
        `;
    }
    
    // Afficher les alertes récentes
    const recentAlertsContainer = document.getElementById('recent-alerts');
    if (recentAlertsContainer) {
        if (alertData.recent && alertData.recent.length > 0) {
            let recentHtml = '';
            alertData.recent.slice(0, 5).forEach(alert => {
                const severityClass = window.alertManager ? window.alertManager.getSeverityClass(alert.severity) : 'secondary';
                recentHtml += `
                    <div class="d-flex align-items-center py-2 border-bottom">
                        <div class="me-2">
                            <span class="badge bg-${severityClass} badge-sm">
                                ${alert.severity}
                            </span>
                        </div>
                        <div class="flex-grow-1">
                            <div class="fw-bold">${alert.title}</div>
                            <small class="text-muted">${alert.message}</small>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">
                                ${window.alertManager ? window.alertManager.formatTimeAgo(alert.created_at) : alert.created_at}
                            </small>
                        </div>
                    </div>
                `;
            });
            recentAlertsContainer.innerHTML = recentHtml;
        } else {
            recentAlertsContainer.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="fas fa-check-circle fa-2x mb-2"></i>
                    <p>Aucune alerte récente</p>
                </div>
            `;
        }
    }
}

// Fonction pour ouvrir le modal des alertes
function openAlertsModal() {
    if (window.alertManager) {
        window.alertManager.loadAlerts();
        const alertsModal = new bootstrap.Modal(document.getElementById('alertsModal'));
        alertsModal.show();
    }
}

// Gérer les clics sur les liens d'alertes
document.addEventListener('click', function(e) {
    if (e.target.matches('[data-action="show-alerts"]') || e.target.closest('[data-action="show-alerts"]')) {
        e.preventDefault();
        openAlertsModal();
    }
});

// Fonction utilitaire pour charger un script (si nécessaire)
function loadScript(src, callback) {
    const script = document.createElement('script');
    script.src = src;
    script.onload = callback;
    script.onerror = function() {
        console.error('Erreur lors du chargement de:', src);
    };
    document.head.appendChild(script);
}

// Démarrer les mises à jour automatiques
function startAutoRefresh() {
    console.log('⏰ Démarrage des mises à jour automatiques');
    
    // Actualisation toutes les 30 secondes
    setInterval(() => {
        loadDashboardData();
        if (typeof loadStatistics === 'function') {
            loadStatistics();
        }
    }, 30000);
} 