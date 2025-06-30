/**
 * Dashboard JavaScript - NTP Monitor Enterprise
 */

let offsetChart = null;
let dashboardData = {};
let alertManager = null;

// DIAGNOSTIC: Vérifier que tous les éléments DOM requis existent
function diagnosticDOMElements() {
    const requiredElements = [
        'servers-count',
        'sync-count', 
        'alerts-count',
        'clients-count',
        'ntp-servers-clocks',
        'servers-summary',
        'local-time',
        'utc-time',
        'system-timezone',
        'dst-status',
        'offsetChart'
    ];
    
    const missingElements = [];
    const foundElements = [];
    
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            foundElements.push(id);
        } else {
            missingElements.push(id);
        }
    });
    
    console.log('🔍 Diagnostic DOM EmaraudeNTP VIZ:');
    console.log(`✅ Éléments trouvés (${foundElements.length}):`, foundElements);
    
    if (missingElements.length > 0) {
        console.warn(`❌ Éléments manquants (${missingElements.length}):`, missingElements);
        console.warn('Cela peut causer des erreurs JavaScript');
    } else {
        console.log('🎯 Tous les éléments DOM requis sont présents !');
    }
    
    return { found: foundElements, missing: missingElements };
}

// Initialisation du dashboard
function initDashboard() {
    console.log('🎯 Initialisation EmaraudeNTP VIZ Dashboard');
    
    // DIAGNOSTIC: Vérifier les éléments DOM
    const domDiagnostic = diagnosticDOMElements();
    
    // Utiliser le gestionnaire d'alertes global s'il existe
    if (window.alertManager) {
        alertManager = window.alertManager;
    }
    
    // Charger les données initiales
    loadDashboardData();
    
    // Initialiser le graphique des écarts
    initOffsetChart();
    
    // Programmer les mises à jour automatiques
    setInterval(loadDashboardData, 30000); // Toutes les 30 secondes
    
    // CORRECTION: Rafraîchissement automatique du graphique des écarts (toutes les 5 minutes)
    setInterval(loadOffsetChartData, 300000); // 5 minutes
    console.log('📊 Graphique des écarts: rafraîchissement automatique activé (5 min)');
    
    // Charger les informations système
    loadSystemInfo();
    
    // Mise à jour automatique des informations système (toutes les 5 minutes)
    setInterval(updateSystemLocalInfo, 300000);
    
    // Charger les statistiques d'alertes
    if (typeof loadStatistics === 'function') {
        loadStatistics();
    } else {
        console.warn('⚠️ Fonction loadStatistics non disponible - chargement basique des alertes');
        loadBasicAlerts();
    }
    
    // Démarrer les mises à jour automatiques
    startAutoRefresh();
    
    // Afficher un message de succès si tout va bien
    if (domDiagnostic.missing.length === 0) {
        console.log('🚀 EmaraudeNTP VIZ initialisé avec succès !');
    }
}

// Charger les données du dashboard - EmaraudeNTP VIZ
function loadDashboardData() {
    fetch('/api/dashboard/summary')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('❌ Erreur chargement dashboard:', data.error);
                return;
            }
            
            dashboardData = data;
            updateDashboardDisplay(data);
        })
        .catch(error => {
            console.error('❌ Erreur réseau dashboard:', error);
            
            // Fallback: charger les serveurs directement si l'API dashboard ne marche pas
            loadNTPServers().then(servers => {
                if (servers) {
                    console.log('📡 Fallback: chargement direct des serveurs NTP');
                    updateServersClocks(servers);
                }
            });
        });
}

// Mettre à jour l'affichage du dashboard - EmaraudeNTP VIZ
function updateDashboardDisplay(data) {
    // Mise à jour des statistiques générales avec vérification d'existence des éléments
    const serversCountEl = document.getElementById('servers-count');
    const syncCountEl = document.getElementById('sync-count');
    const alertsCountEl = document.getElementById('alerts-count');
    const clientsCountEl = document.getElementById('clients-count');
    
    if (serversCountEl && data.servers) {
        serversCountEl.textContent = data.servers.total || 0;
    }
    
    if (syncCountEl && data.servers) {
        syncCountEl.textContent = data.servers.synchronized || 0;
    }
    
    if (alertsCountEl && data.alerts) {
        alertsCountEl.textContent = data.alerts.total || 0;
    }
    
    if (clientsCountEl && data.clients) {
        clientsCountEl.textContent = data.clients.total_connections || 0;
    }
    
    // Mise à jour du résumé des serveurs
    const serversSummaryEl = document.getElementById('servers-summary');
    if (serversSummaryEl && data.servers) {
        serversSummaryEl.textContent = `${data.servers.total || 0} Serveurs actifs`;
    }
    
    // Mise à jour des horloges serveurs
    if (data.servers && data.servers.data) {
        updateServersClocks(data.servers.data);
    }
    
    // Mise à jour des informations système
    if (data.system) {
        updateSystemInfo(data.system);
    }
    
    console.log('📊 Dashboard EmaraudeNTP VIZ mis à jour:', new Date().toLocaleTimeString('fr-FR'));
}

// Mettre à jour l'affichage des serveurs
function updateServersClocks(servers) {
    const container = document.getElementById('ntp-servers-clocks');
    if (!container) return;
    
    // Trier les serveurs par priorité pour affichage
    const sortedServers = [...servers].sort((a, b) => (a.priority || 999) - (b.priority || 999));
    
    let html = '';
    
    sortedServers.forEach((server, index) => {
        const isOffline = server.status === 'offline';
        const isPrimary = server.priority === 1;
        
        // Couleurs selon le statut avec mise en avant du serveur priorité 1
        let statusClass = 'secondary';
        let statusIcon = '<i class="fas fa-question-circle"></i>';
        
        switch (server.status) {
            case 'online':
            case 'ok':
                statusClass = isPrimary ? 'success' : 'info';
                statusIcon = '<i class="fas fa-check-circle"></i>';
                break;
            case 'warning':
                statusClass = 'warning';
                statusIcon = '<i class="fas fa-exclamation-triangle"></i>';
                break;
            case 'critical':
                statusClass = 'danger';
                statusIcon = '<i class="fas fa-exclamation-circle"></i>';
                break;
            case 'offline':
                statusClass = 'secondary';
                statusIcon = '<i class="fas fa-times-circle"></i>';
                break;
            default:
                statusClass = 'info';
                statusIcon = '<i class="fas fa-question-circle"></i>';
        }
        
        // Calculer l'heure du serveur
        const now = new Date();
        const serverTime = new Date(now.getTime() + (server.last_offset || 0) * 1000);
        const timeDisplay = isOffline ? '--:--:--' : serverTime.toLocaleTimeString('fr-FR');
        
        // Affichage de l'écart
        const offsetDisplay = server.last_offset !== null && server.last_offset !== undefined
            ? (Math.abs(server.last_offset * 1000).toFixed(1) + 'ms')
            : '--';
        
        // Classes CSS spéciales pour le serveur priorité 1
        const containerClass = isPrimary ? 'col-md-12 col-lg-6' : 'col-md-6 col-lg-4';
        const cardClass = isPrimary ? 'border-success shadow-lg' : `border-${statusClass}`;
        const headerClass = isPrimary ? 'bg-success' : `bg-${statusClass}`;
        const badgeText = isPrimary ? 'PRINCIPAL' : server.server_type.toUpperCase();
        const priorityBadge = isPrimary ? '<span class="badge bg-warning text-dark me-2"><i class="fas fa-crown"></i> PRIORITÉ 1</span>' : '';
        
        html += `
            <div class="${containerClass} mb-3">
                <div class="card ${cardClass}">
                    <div class="card-header ${headerClass} text-white">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">
                                ${priorityBadge}
                                <i class="${statusIcon} me-2"></i>${server.name}
                            </h6>
                            <span class="badge bg-light text-dark">${badgeText}</span>
                        </div>
                    </div>
                    <div class="card-body ${isPrimary ? 'bg-light' : ''}">
                        <div class="text-center mb-2">
                            <div class="h${isPrimary ? '3' : '4'} text-primary ${isPrimary ? 'fw-bold' : ''}" id="server-time-${server.id}">
                                ${timeDisplay}
                            </div>
                            <small class="text-muted">${server.address}</small>
                            ${isPrimary ? '<div class="text-success small"><i class="fas fa-clock"></i> Référence temporelle principale</div>' : ''}
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
                        ${isPrimary ? `
                        <div class="mt-2 text-center">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i> 
                                Tous les équipements du réseau se synchronisent sur cette référence
                            </small>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Mettre à jour les horloges en temps réel
    updateServerTimes(sortedServers);
}

// Mettre à jour les informations système avec timezone - EmaraudeNTP VIZ
function updateSystemInfo(systemData) {
    if (!systemData) return;
    
    try {
        const localTime = new Date(systemData.local_time);
        const utcTime = new Date(systemData.utc_time);
        
        // Affichage de l'heure avec timezone (vérification d'existence)
        const localTimeEl = document.getElementById('local-time');
        const utcTimeEl = document.getElementById('utc-time');
        const timezoneEl = document.getElementById('system-timezone');
        const dstStatusEl = document.getElementById('dst-status');
        
        if (localTimeEl) {
            localTimeEl.textContent = localTime.toLocaleTimeString('fr-FR');
        }
        
        if (utcTimeEl) {
            utcTimeEl.textContent = utcTime.toLocaleTimeString('fr-FR');
        }
        
        if (timezoneEl) {
            timezoneEl.textContent = systemData.timezone || 'UTC';
        }
        
        // Informations supplémentaires si disponibles (éléments optionnels)
        if (systemData.utc_offset_hours !== undefined) {
            const offset = systemData.utc_offset_hours;
            const offsetStr = `UTC${offset >= 0 ? '+' : ''}${offset}`;
            
            const utcOffsetEl = document.getElementById('utc-offset');
            const timezoneInfoEl = document.getElementById('local-timezone-info');
            
            if (utcOffsetEl) {
                utcOffsetEl.textContent = offsetStr;
            }
            
            if (timezoneInfoEl) {
                timezoneInfoEl.textContent = `${systemData.timezone} (${offsetStr})`;
            }
        }
        
        if (systemData.is_dst !== undefined && dstStatusEl) {
            dstStatusEl.textContent = systemData.is_dst ? 'Oui' : 'Non';
            
            // Couleur du badge selon l'état DST
            dstStatusEl.className = systemData.is_dst ? 'badge bg-warning' : 'badge bg-info';
        }
        
        console.log('🌍 Informations système mises à jour:', systemData.timezone);
        
    } catch (error) {
        console.error('❌ Erreur mise à jour système:', error);
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

// Charger les données pour le graphique - FENÊTRE GLISSANTE 24H AMÉLIORÉE
function loadOffsetChartData() {
    fetch('/api/ntp/analytics/offset-trends?hours=24&interval_minutes=30')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.trends && offsetChart) {
                console.log(`📊 Graphique mis à jour: ${data.servers_count} serveurs, ${data.data_points_per_server} points/serveur`);
                updateOffsetChart(data.trends, data);
            } else {
                console.warn('⚠️ Données de tendances incomplètes ou invalides');
            }
        })
        .catch(error => {
            console.error('❌ Erreur chargement données graphique:', error);
            // Afficher un message d'erreur dans le graphique
            if (offsetChart) {
                offsetChart.data.labels = ['Erreur'];
                offsetChart.data.datasets = [{
                    label: 'Erreur de chargement',
                    data: [0],
                    borderColor: '#dc3545',
                    backgroundColor: '#dc354520'
                }];
                offsetChart.update();
            }
        });
}

// Mettre à jour le graphique des écarts - VERSION AMÉLIORÉE
function updateOffsetChart(trends, metadata = null) {
    if (!offsetChart) return;
    
    const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#17a2b8'];
    const datasets = [];
    let labels = [];
    
    // Compter les serveurs avec données
    const serversWithData = Object.keys(trends).filter(serverId => 
        trends[serverId].data && trends[serverId].data.length > 0
    );
    
    if (serversWithData.length === 0) {
        // Aucune donnée disponible
        offsetChart.data.labels = ['Aucune donnée'];
        offsetChart.data.datasets = [{
            label: 'Aucune donnée disponible',
            data: [0],
            borderColor: '#6c757d',
            backgroundColor: '#6c757d20'
        }];
        offsetChart.update();
        return;
    }
    
    Object.keys(trends).forEach((serverId, index) => {
        const serverData = trends[serverId];
        if (serverData.data && serverData.data.length > 0) {
            
            // Générer les labels temporels avec date si nécessaire
            if (labels.length === 0) {
                labels = serverData.data.map(point => {
                    const date = new Date(point.timestamp);
                    const now = new Date();
                    const isToday = date.toDateString() === now.toDateString();
                    
                    if (isToday) {
                        return date.toLocaleTimeString('fr-FR', { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                        });
                    } else {
                        return date.toLocaleDateString('fr-FR', { 
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit', 
                            minute: '2-digit' 
                        });
                    }
                });
            }
            
            // Préparer les données, gérer les valeurs nulles
            const chartData = serverData.data.map(point => {
                if (point.avg_offset === null || point.avg_offset === undefined) {
                    return null; // Chart.js gère automatiquement les valeurs null
                }
                return point.avg_offset * 1000; // Convertir en ms
            });
            
            datasets.push({
                label: serverData.server_name,
                data: chartData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                fill: false,
                tension: 0.1,
                spanGaps: false, // Ne pas connecter les points manquants
                pointRadius: 2,
                pointHoverRadius: 5
            });
        }
    });
    
    offsetChart.data.labels = labels;
    offsetChart.data.datasets = datasets;
    
    // Mise à jour du titre avec métadonnées
    if (metadata && offsetChart.options.plugins.title) {
        const windowDuration = metadata.period_hours || 24;
        const interval = metadata.interval_minutes || 30;
        offsetChart.options.plugins.title.text = 
            `Évolution des écarts de synchronisation (${windowDuration}h glissantes, ∆${interval}min)`;
    }
    
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
        case 'ok': return '<i class="fas fa-check-circle"></i>';
        case 'warning': return '<i class="fas fa-exclamation-triangle"></i>';
        case 'critical': return '<i class="fas fa-exclamation-circle"></i>';
        case 'offline': return '<i class="fas fa-times-circle"></i>';
        default: return '<i class="fas fa-question-circle"></i>';
    }
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

/**
 * Charger et afficher les informations système local - VERSION AMÉLIORÉE
 */
async function updateSystemLocalInfo() {
    try {
        const response = await fetch('/api/system/time');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const systemData = await response.json();
        
        // Vérifier si la réponse contient une erreur
        if (!systemData.success && systemData.error) {
            console.warn('API retourne une erreur:', systemData.error);
        }
        
        // Heure locale - Gestion des formats multiples
        let localTime;
        if (systemData.local_time) {
            // Support des formats ISO et string
            localTime = systemData.local_time.includes('T') ? 
                new Date(systemData.local_time) : 
                new Date(systemData.local_time.replace(' ', 'T'));
            
            if (isNaN(localTime.getTime())) {
                localTime = new Date(); // Fallback vers l'heure locale du navigateur
            }
        } else {
            localTime = new Date();
        }
        
        // Heure UTC - Gestion des formats multiples
        let utcTime;
        if (systemData.utc_time) {
            utcTime = systemData.utc_time.includes('T') ? 
                new Date(systemData.utc_time) : 
                new Date(systemData.utc_time.replace(' ', 'T'));
            
            if (isNaN(utcTime.getTime())) {
                utcTime = new Date();
            }
        } else {
            utcTime = new Date();
        }
        
        // Affichage des heures
        document.getElementById('local-time').textContent = localTime.toLocaleTimeString('fr-FR');
        document.getElementById('utc-time').textContent = utcTime.toLocaleTimeString('fr-FR');
        
        // Timezone avec indicateur de santé
        const timezone = systemData.timezone || 'UTC';
        const timezoneElement = document.getElementById('system-timezone');
        timezoneElement.textContent = timezone;
        
        // Ajouter indicateur visuel si erreur système
        if (!systemData.success) {
            timezoneElement.className = 'badge bg-warning';
            timezoneElement.title = 'Données système partiellement disponibles';
        } else {
            timezoneElement.className = 'badge bg-info';
            timezoneElement.title = 'Données système en temps réel';
        }
        
        // Décalage UTC - Support des deux formats
        let offsetStr = '+00:00';
        if (systemData.utc_offset) {
            // Format direct de l'API (+01:00)
            offsetStr = systemData.utc_offset;
        } else if (systemData.utc_offset_minutes !== undefined) {
            // Format en minutes pour compatibilité
            const offsetMinutes = systemData.utc_offset_minutes;
            const offsetHours = Math.abs(offsetMinutes) / 60;
            const offsetSign = offsetMinutes >= 0 ? '+' : '-';
            offsetStr = `${offsetSign}${Math.floor(offsetHours).toString().padStart(2, '0')}:${(Math.abs(offsetMinutes) % 60).toString().padStart(2, '0')}`;
        }
        
        document.getElementById('utc-offset').textContent = offsetStr;
        
        // Info timezone locale complète
        document.getElementById('local-timezone-info').textContent = `${timezone} (UTC${offsetStr})`;
        
        // Heure d'été avec indicateur
        const isDst = systemData.is_dst;
        const dstElement = document.getElementById('dst-status');
        dstElement.textContent = isDst ? 'Oui' : 'Non';
        dstElement.className = isDst ? 'fw-bold text-warning' : 'fw-bold text-info';
        dstElement.title = isDst ? 'Heure d\'été active' : 'Heure d\'hiver active';
        
        console.log('✅ Informations système mises à jour:', {
            timezone,
            offset: offsetStr,
            dst: isDst,
            success: systemData.success
        });
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement des infos système:', error);
        
        // Affichage d'erreur avec fallback
        const now = new Date();
        document.getElementById('local-time').textContent = now.toLocaleTimeString('fr-FR');
        document.getElementById('utc-time').textContent = now.toUTCString().split(' ')[4]; // Heure UTC seule
        
        const timezoneElement = document.getElementById('system-timezone');
        timezoneElement.textContent = 'Erreur API';
        timezoneElement.className = 'badge bg-danger';
        timezoneElement.title = 'Impossible de récupérer les données système';
        
        document.getElementById('utc-offset').textContent = '--';
        document.getElementById('local-timezone-info').textContent = 'Service système indisponible';
        document.getElementById('dst-status').textContent = '--';
    }
}

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

// Fonction basique pour charger les alertes si le gestionnaire principal n'est pas disponible
function loadBasicAlerts() {
    try {
        fetch('/api/alerts/recent')
            .then(response => response.json())
            .then(data => {
                console.log('📢 Alertes basiques chargées:', data);
                
                // Mise à jour simple du compteur d'alertes
                const alertsCountEl = document.getElementById('alerts-count');
                const activeAlertsCountEl = document.getElementById('active-alerts-count');
                
                if (alertsCountEl && data.active_count !== undefined) {
                    alertsCountEl.textContent = data.active_count || 0;
                }
                
                if (activeAlertsCountEl && data.active_count !== undefined) {
                    activeAlertsCountEl.textContent = data.active_count || 0;
                    activeAlertsCountEl.style.display = data.active_count > 0 ? 'inline' : 'none';
                }
                
                // Mise à jour basique de la liste des alertes récentes
                const recentAlertsEl = document.getElementById('recent-alerts');
                if (recentAlertsEl && data.alerts && Array.isArray(data.alerts)) {
                    if (data.alerts.length === 0) {
                        recentAlertsEl.innerHTML = `
                            <div class="text-center text-muted">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                Aucune alerte active
                            </div>
                        `;
                    } else {
                        let html = '';
                        data.alerts.slice(0, 3).forEach(alert => {
                            const severityClass = alert.severity === 'critical' ? 'danger' : 
                                                alert.severity === 'warning' ? 'warning' : 'info';
                            html += `
                                <div class="d-flex align-items-center mb-2">
                                    <i class="fas fa-exclamation-triangle text-${severityClass} me-2"></i>
                                    <div class="flex-grow-1">
                                        <small class="fw-semibold">${alert.title || 'Alerte'}</small>
                                        <div class="text-muted small">${alert.message || ''}</div>
                                    </div>
                                </div>
                            `;
                        });
                        recentAlertsEl.innerHTML = html;
                    }
                }
            })
            .catch(error => {
                console.warn('⚠️ Impossible de charger les alertes basiques:', error);
                
                // Fallback: réinitialiser les compteurs à 0
                const alertsCountEl = document.getElementById('alerts-count');
                const activeAlertsCountEl = document.getElementById('active-alerts-count');
                
                if (alertsCountEl) alertsCountEl.textContent = '0';
                if (activeAlertsCountEl) {
                    activeAlertsCountEl.textContent = '0';
                    activeAlertsCountEl.style.display = 'none';
                }
            });
    } catch (error) {
        console.error('❌ Erreur fonction loadBasicAlerts:', error);
    }
}

// ===== FONCTIONS MONITORING CLIENTS NTP =====

/**
 * Afficher les détails des clients connectés
 */
function showClientDetails() {
    if (!window.clientMonitor) {
        alert('Module de monitoring non chargé');
        return;
    }
    
    const data = window.clientMonitor.getCurrentData();
    if (!data) {
        alert('Aucune donnée de monitoring disponible');
        return;
    }
    
    // Créer le modal de détails
    const modalHtml = `
        <div class="modal fade" id="clientDetailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-network-wired me-2"></i>
                            Détails du Monitoring Clients NTP
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="client-details-content">
                            <div class="text-center">
                                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                                <p>Chargement des détails...</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        <button type="button" class="btn btn-primary" onclick="refreshClientDetails()">
                            <i class="fas fa-sync-alt me-1"></i>Actualiser
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer l'ancien modal s'il existe
    const existingModal = document.getElementById('clientDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Ajouter le nouveau modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Afficher le modal
    const modal = new bootstrap.Modal(document.getElementById('clientDetailsModal'));
    modal.show();
    
    // Charger les détails
    loadClientDetails();
}

/**
 * Charger les détails des clients
 */
async function loadClientDetails() {
    try {
        const [connections, statistics, serviceStatus] = await Promise.all([
            fetch('/api/ntp/clients/connections').then(r => r.json()),
            fetch('/api/ntp/clients/statistics?hours=24').then(r => r.json()),
            fetch('/api/ntp/service/status').then(r => r.json())
        ]);
        
        const contentElement = document.getElementById('client-details-content');
        if (!contentElement) return;
        
        let html = `
            <!-- Status du service -->
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-cog me-2"></i>Status du Service</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Service NTP:</strong> 
                            <span class="badge ${serviceStatus.service_status === 'active' ? 'bg-success' : 'bg-danger'}">
                                ${serviceStatus.service_status}
                            </span>
                        </div>
                        <div class="col-md-6">
                            <strong>Port d'écoute:</strong> 
                            <span class="badge ${serviceStatus.port_listening ? 'bg-success' : 'bg-warning'}">
                                ${serviceStatus.port} ${serviceStatus.port_listening ? '(actif)' : '(inactif)'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Connexions actives -->
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-users me-2"></i>Connexions Actives (${connections.length})</h6>
                </div>
                <div class="card-body">
        `;
        
        if (connections.length === 0) {
            html += '<p class="text-muted text-center">Aucune connexion active</p>';
        } else {
            html += '<div class="table-responsive"><table class="table table-sm">';
            html += '<thead><tr><th>IP Client</th><th>Port Client</th><th>Serveur</th><th>Status</th><th>Timestamp</th></tr></thead><tbody>';
            
            connections.forEach(conn => {
                html += `
                    <tr>
                        <td><code>${conn.client_ip}</code></td>
                        <td>${conn.client_port}</td>
                        <td><code>${conn.server_ip}:${conn.server_port}</code></td>
                        <td><span class="badge bg-success">${conn.status}</span></td>
                        <td><small>${new Date(conn.timestamp).toLocaleString()}</small></td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
        }
        
        html += `
                </div>
            </div>
            
            <!-- Statistiques -->
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Statistiques (24h)</h6>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <h4 class="text-primary">${statistics.total_connections || 0}</h4>
                            <small class="text-muted">Connexions totales</small>
                        </div>
                        <div class="col-md-3">
                            <h4 class="text-success">${statistics.unique_clients || 0}</h4>
                            <small class="text-muted">Clients uniques</small>
                        </div>
                        <div class="col-md-3">
                            <h4 class="text-info">${(statistics.average_connections_per_client || 0).toFixed(1)}</h4>
                            <small class="text-muted">Moy. conn./client</small>
                        </div>
                        <div class="col-md-3">
                            <h4 class="text-warning">${connections.length}</h4>
                            <small class="text-muted">Connexions actives</small>
                        </div>
                    </div>
        `;
        
        if (statistics.top_clients && statistics.top_clients.length > 0) {
            html += '<hr><h6>Top Clients</h6><div class="table-responsive"><table class="table table-sm">';
            html += '<thead><tr><th>IP Client</th><th>Connexions</th></tr></thead><tbody>';
            
            statistics.top_clients.slice(0, 10).forEach(client => {
                html += `
                    <tr>
                        <td><code>${client.ip}</code></td>
                        <td><span class="badge bg-info">${client.connections}</span></td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
        }
        
        html += '</div></div>';
        
        contentElement.innerHTML = html;
        
    } catch (error) {
        console.error('Erreur lors du chargement des détails:', error);
        const contentElement = document.getElementById('client-details-content');
        if (contentElement) {
            contentElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Erreur lors du chargement: ${error.message}
                </div>
            `;
        }
    }
}

/**
 * Actualiser les détails des clients
 */
function refreshClientDetails() {
    loadClientDetails();
}

/**
 * Basculer le monitoring des clients (pause/reprendre)
 */
function toggleClientMonitoring() {
    if (!window.clientMonitor) {
        alert('Module de monitoring non chargé');
        return;
    }
    
    if (window.clientMonitor.isMonitoringActive()) {
        window.clientMonitor.stop();
        
        // Mettre à jour le bouton
        const button = document.querySelector('button[onclick="toggleClientMonitoring()"]');
        if (button) {
            button.innerHTML = '<i class="fas fa-play me-1"></i>Reprendre';
            button.className = 'btn btn-sm btn-outline-success';
            button.title = 'Reprendre le monitoring';
        }
        
        // Notification
        if (window.notificationSystem) {
            window.notificationSystem.show('Monitoring des clients mis en pause', 'warning');
        }
        
    } else {
        window.clientMonitor.start();
        
        // Mettre à jour le bouton
        const button = document.querySelector('button[onclick="toggleClientMonitoring()"]');
        if (button) {
            button.innerHTML = '<i class="fas fa-pause me-1"></i>Pause';
            button.className = 'btn btn-sm btn-outline-secondary';
            button.title = 'Mettre en pause le monitoring';
        }
        
        // Notification
        if (window.notificationSystem) {
            window.notificationSystem.show('Monitoring des clients repris', 'success');
        }
    }
}

/**
 * Exporter les logs des clients (fonction future)
 */
function exportClientLogs() {
    // Notification temporaire
    if (window.notificationSystem) {
        window.notificationSystem.show('Fonctionnalité d\'export en cours de développement', 'info');
    }
}

 