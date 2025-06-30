/**
 * Dashboard JavaScript - NTP Monitor Enterprise
 */

let offsetChart = null;
let dashboardData = {};
let alertManager = null;

// Variables globales pour le timer
let localTimeTimer = null;

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
    console.log('🎯 Initialisation du dashboard EmaraudeNTP VIZ');
    
    // Diagnostic des éléments DOM
    diagnosticDOMElements();
    
    // Initialiser le graphique des écarts
    initOffsetChart();
    
    // Démarrer les mises à jour temps réel de l'heure locale
    startLocalTimeUpdates();
    
    // Démarrer la mise à jour des heures des serveurs NTP en temps réel
    setInterval(updateServerTimesRealTime, 1000); // Mise à jour chaque seconde
    
    // Charger les données initiales
    loadDashboardData();
    loadSystemInfo();
    loadNTPServers();
    
    // Charger les statistiques et alertes
    loadStatistics();
    
    // Démarrer l'auto-actualisation
    startAutoRefresh();
    
    // Connecter le WebSocket si disponible
    if (typeof connectWebSocket === 'function') {
        connectWebSocket();
    }
    
    // Initialiser le monitoring des clients si disponible
    if (window.clientMonitor && typeof window.clientMonitor.start === 'function') {
        window.clientMonitor.start();
    } else {
        // Créer une instance de ClientMonitor si elle n'existe pas
        if (typeof ClientMonitor !== 'undefined') {
            window.clientMonitor = new ClientMonitor();
            window.clientMonitor.start();
        }
    }
    
    console.log('✅ Dashboard EmaraudeNTP VIZ initialisé');
}

// Charger les données du dashboard - EmaraudeNTP VIZ
function loadDashboardData() {
    fetch('/api/dashboard/summary', { credentials: 'include' })
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
        // Stocker les données des serveurs globalement pour la mise à jour en temps réel
        window.lastServersData = data.servers.data;
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
    
    // 🔧 CORRECTION : Trier d'abord par PRIORITÉ, puis par localité
    // Les serveurs priorité 1 doivent être affichés en premier, qu'ils soient locaux ou non
    const sortedServers = servers.sort((a, b) => {
        // D'abord trier par priorité (plus faible = plus prioritaire)
        const priorityA = a.priority || 999;
        const priorityB = b.priority || 999;
        
        if (priorityA !== priorityB) {
            return priorityA - priorityB;
        }
        
        // À priorité égale, serveurs locaux avant serveurs distants
        const isLocalA = a.address && (
            a.address.startsWith('192.168.') || 
            a.address.startsWith('10.') || 
            a.address.startsWith('172.') ||
            a.address.includes('localhost') ||
            a.address.includes('127.0.0.1')
        );
        const isLocalB = b.address && (
            b.address.startsWith('192.168.') || 
            b.address.startsWith('10.') || 
            b.address.startsWith('172.') ||
            b.address.includes('localhost') ||
            b.address.includes('127.0.0.1')
        );
        
        if (isLocalA && !isLocalB) return -1;
        if (!isLocalA && isLocalB) return 1;
        
        // À priorité et localité égales, trier par nom
        return (a.name || '').localeCompare(b.name || '');
    });
    
    // Statistiques de tri pour debug
    const localCount = sortedServers.filter(s => s.address && (
        s.address.startsWith('192.168.') || s.address.startsWith('10.') || s.address.startsWith('172.') ||
        s.address.includes('localhost') || s.address.includes('127.0.0.1')
    )).length;
    const priority1Count = sortedServers.filter(s => s.priority === 1).length;
    
    console.log(`🏆 Serveurs priorité 1: ${priority1Count}`);
    console.log(`🏠 Serveurs locaux: ${localCount}`);
    console.log(`📊 Total serveurs triés: ${sortedServers.length}`);
    
    // NOUVEAU: Calculer la dernière synchronisation globale
    const mostRecentSync = servers
        .filter(s => s.last_sync)
        .map(s => new Date(s.last_sync))
        .sort((a, b) => b - a)[0]; // La plus récente
        
    // Mettre à jour l'affichage global de la dernière synchronisation (FORMAT AMÉLIORÉ)
    const globalLastSyncEl = document.getElementById('global-last-sync');
    const syncHealthStatusEl = document.getElementById('sync-health-status');
    
    if (globalLastSyncEl && mostRecentSync) {
        const timeAgo = getTimeAgo(mostRecentSync);
        // 🔧 AMÉLIORATION : Format HH:MM sans secondes + temps écoulé clair
        const timeFormat = mostRecentSync.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit'
        });
        
        // Formater le temps écoulé de manière plus claire
        const now = new Date();
        const diffMs = now - mostRecentSync;
        const diffMinutes = Math.floor(diffMs / 60000);
        
        let displayText;
        if (diffMinutes < 1) {
            displayText = `${timeFormat} (maintenant)`;
        } else if (diffMinutes < 60) {
            displayText = `${timeFormat} (il y a ${diffMinutes}min)`;
        } else {
            const diffHours = Math.floor(diffMinutes / 60);
            displayText = `${timeFormat} (il y a ${diffHours}h${diffMinutes % 60 > 0 ? ` ${diffMinutes % 60}min` : ''})`;
        }
        globalLastSyncEl.textContent = displayText;
    } else if (globalLastSyncEl) {
        globalLastSyncEl.textContent = 'Aucune synchronisation';
    }
    
    // Déterminer le statut de santé global
    const onlineServers = servers.filter(s => s.status === 'online' || s.status === 'ok').length;
    const totalServers = servers.length;
    const recentSyncs = servers.filter(s => s.last_sync && new Date() - new Date(s.last_sync) < 300000).length; // 5 min
    
    if (syncHealthStatusEl) {
        if (recentSyncs === totalServers) {
            syncHealthStatusEl.textContent = 'Excellent';
            syncHealthStatusEl.className = 'fw-bold text-success';
        } else if (recentSyncs > totalServers / 2) {
            syncHealthStatusEl.textContent = 'Bon';
            syncHealthStatusEl.className = 'fw-bold text-warning';
        } else {
            syncHealthStatusEl.textContent = 'Problème';
            syncHealthStatusEl.className = 'fw-bold text-danger';
        }
    }
    
    // NOUVEAU: Identifier le serveur priorité 1 et séparer des autres
    const priorityOneServer = sortedServers.find(s => s.priority === 1);
    const otherServers = sortedServers.filter(s => s.priority !== 1);
    
    // Générer l'affichage avec layout spécial pour priorité 1
    let serversHtml = '';
    
    // SERVEUR PRIORITÉ 1 - DOUBLE LARGEUR
    if (priorityOneServer) {
        serversHtml += renderServerCard(priorityOneServer, 'col-12', true);
    }
    
    // AUTRES SERVEURS - RÉPARTIS SUR 2 LIGNES
    otherServers.forEach(server => {
        serversHtml += renderServerCard(server, 'col-md-6 col-lg-4', false);
    });
    
    container.innerHTML = serversHtml;
}

// NOUVELLE FONCTION: Générer le HTML d'un encart serveur
function renderServerCard(server, colClass, isPriorityOne) {
    const isLocal = server.address && (server.address.startsWith('192.168.') || server.address.startsWith('10.') || server.address.startsWith('172.'));
    const isHighPriority = server.priority === 1;
    
    // Classes spéciales pour les serveurs locaux et priorité 1
    const cardClass = isPriorityOne ? 'border-success border-3' : (isLocal ? 'border-info' : '');
    const headerClass = isPriorityOne ? 'bg-success text-white' : (isLocal ? 'bg-info text-white' : '');
    
    const statusClass = getStatusClass(server.status || 'unknown');
    const statusIcon = getStatusIcon(server.status || 'unknown');
    const statusLabel = getStatusLabel(server.status || 'unknown');
    
    // CALCUL DE L'HEURE ACTUELLE DU SERVEUR (pas dernière sync)
    const now = new Date();
    const serverTime = server.last_offset !== null ? 
        new Date(now.getTime() + (server.last_offset || 0) * 1000) : 
        new Date(); // Fallback sur heure locale si pas d'offset
    
    const isServerOnline = server.status === 'online' || server.status === 'ok';
    const currentTimeFormatted = isServerOnline ? 
        serverTime.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        }) : '--:--:--';
    
    // Format de la DERNIÈRE SYNCHRONISATION avec secondes
    const lastSyncFormatted = server.last_sync ? 
        new Date(server.last_sync).toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        }) : 'Jamais';
    
    const timeAgo = server.last_sync ? getTimeAgo(new Date(server.last_sync)) : '';
    
    return `
        <div class="${colClass} mb-3">
            <div class="card h-100 ${cardClass}">
                ${(isLocal || isPriorityOne) ? `<div class="card-header ${headerClass} py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="mb-0">
                            ${isPriorityOne ? 
                                '<i class="fas fa-crown me-1"></i>SERVEUR PRINCIPAL (Priorité ' + server.priority + ')' : 
                                '<i class="fas fa-server me-1"></i>SERVEUR LOCAL (Priorité ' + server.priority + ')'
                            }
                        </small>
                        ${!server.is_active ? '<span class="badge bg-warning">INACTIF</span>' : ''}
                        ${isLocal ? '<span class="badge bg-secondary">🏠 LOCAL</span>' : ''}
                        ${isPriorityOne && !isLocal ? '<span class="badge bg-warning">🏆 PRIORITÉ 1</span>' : ''}
                    </div>
                </div>` : ''}
                <div class="card-body ${isPriorityOne ? 'p-4' : ''}">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h${isPriorityOne ? '5' : '6'} class="card-title mb-1 ${isPriorityOne ? 'text-success fw-bold' : ''}">${server.name}</h${isPriorityOne ? '5' : '6'}>
                            <p class="text-muted mb-0">
                                <i class="fas fa-globe me-1"></i>
                                ${server.address}${server.port && server.port !== 123 ? ':' + server.port : ''}
                            </p>
                        </div>
                        <span class="badge bg-${statusClass} fs-6">
                            ${statusIcon} ${statusLabel}
                        </span>
                    </div>
                    
                    <!-- HEURE ACTUELLE DU SERVEUR -->
                    <div class="text-center mb-3 ${isPriorityOne ? 'py-3' : 'py-2'}" style="background: rgba(0,0,0,0.05); border-radius: 8px;">
                        <div class="text-muted mb-1">
                            <i class="fas fa-clock me-1"></i>
                            Heure actuelle du serveur
                        </div>
                        <div class="fs-${isPriorityOne ? '3' : '4'} fw-bold text-primary font-monospace" id="server-time-${server.id}">
                            ${currentTimeFormatted}
                        </div>
                    </div>
                    
                    <div class="row text-center mb-3">
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
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-sync me-1"></i>
                            Dernière sync: ${lastSyncFormatted}${timeAgo ? ' (' + timeAgo + ')' : ''}
                        </small>
                        ${isPriorityOne ? '<small class="text-success fw-bold"><i class="fas fa-star me-1"></i>Référence temporelle</small>' : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// NOUVELLE FONCTION: Mettre à jour les heures en temps réel
function updateServerTimesRealTime() {
    // Mettre à jour toutes les heures des serveurs affichées
    const servers = window.lastServersData || [];
    
    servers.forEach(server => {
        const timeElement = document.getElementById(`server-time-${server.id}`);
        if (timeElement) {
            const now = new Date();
            const serverTime = server.last_offset !== null ? 
                new Date(now.getTime() + (server.last_offset || 0) * 1000) : 
                new Date();
            
            const isServerOnline = server.status === 'online' || server.status === 'ok';
            const currentTimeFormatted = isServerOnline ? 
                serverTime.toLocaleTimeString('fr-FR', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    second: '2-digit'
                }) : '--:--:--';
            
            timeElement.textContent = currentTimeFormatted;
        }
    });
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
    fetch('/api/system/time', { credentials: 'include' })
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

// Initialiser le graphique des écarts de synchronisation
function initOffsetChart() {
    const canvas = document.getElementById('offsetChart');
    if (!canvas) {
        console.error('Canvas offsetChart non trouvé');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Vérifier si Chart.js a le plugin zoom (optionnel)
    const hasZoomPlugin = typeof Chart !== 'undefined' && Chart.registry && Chart.registry.plugins.get('zoom');
    
    const chartConfig = {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Écarts de synchronisation NTP (24h glissantes)',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const label = context[0].label;
                            return `Temps: ${label}`;
                        },
                        label: function(context) {
                            const value = context.parsed.y;
                            const serverName = context.dataset.label;
                            return `${serverName}: ${value.toFixed(1)}ms`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',  // CORRECTION: Changé de 'time' vers 'category'
                    title: {
                        display: true,
                        text: 'Temps'
                    },
                    ticks: {
                        maxTicksLimit: 12,  // Limite le nombre de labels affichés
                        callback: function(value, index, values) {
                            // Formatter les labels pour afficher uniquement HH:MM
                            const label = this.getLabelForValue(value);
                            if (label && label.includes(' ')) {
                                const timePart = label.split(' ')[1]; // Prendre la partie heure
                                return timePart ? timePart.substring(0, 5) : label; // HH:MM seulement
                            }
                            return label;
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Écart (milliseconds)'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + 'ms';
                        }
                    }
                    // SUPPRESSION: Les limites fixes qui causaient le problème
                    // min: -50,
                    // max: 50
                }
            },
            animation: {
                duration: 300
            }
        }
    };
    
    // AMÉLIORATION: Ajouter le zoom avec limites dynamiques si le plugin est disponible
    if (hasZoomPlugin) {
        chartConfig.options.plugins.zoom = {
            limits: {
                // NOUVEAU: Limites dynamiques calculées selon les données
                y: {
                    min: 'original',  // Utilise les limites originales des données
                    max: 'original'
                },
                x: {
                    minRange: 5  // Minimum 5 points visibles
                }
            },
            pan: {
                enabled: true,
                mode: 'xy',
                threshold: 10
            },
            zoom: {
                wheel: {
                    enabled: true,
                },
                pinch: {
                    enabled: true
                },
                mode: 'xy',
                onZoomComplete: function(context) {
                    console.log('Zoom appliqué sur le graphique des écarts');
                },
                onZoomRejected: function(context) {
                    console.log('Zoom rejeté (limites atteintes)');
                }
            }
        };
        
        console.log('Plugin Zoom Chart.js détecté et activé avec limites dynamiques');
    } else {
        console.log('Plugin Zoom Chart.js non disponible');
    }
    
    offsetChart = new Chart(ctx, chartConfig);
    
    // Charger les données du graphique
    loadOffsetChartData();
}

// Charger les données pour le graphique - FENÊTRE GLISSANTE 24H AMÉLIORÉE
function loadOffsetChartData() {
    // Configuration de la requête avec headers d'authentification
    const fetchOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'include'  // Inclure les cookies de session
    };
    
    fetch('/api/ntp/analytics/offset-trends?hours=24&interval_minutes=30', fetchOptions)
        .then(response => {
            console.log(`📊 Réponse API offset-trends: ${response.status} ${response.statusText}`);
            
            // Vérifier si la réponse est du HTML (page de connexion)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                console.warn('⚠️ API retourne du HTML au lieu de JSON - Session expirée ou problème d\'authentification');
                // Tenter de recharger la page pour récupérer une session valide
                setTimeout(() => {
                    console.log('🔄 Rechargement de la page pour récupérer la session...');
                    window.location.reload();
                }, 2000);
                throw new Error('Session expirée - Rechargement en cours');
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('📊 Données reçues:', data);
            
            if (data.success && data.trends && typeof data.trends === 'object') {
                // Convertir l'objet trends en tableau
                const trendsArray = Object.keys(data.trends).map(serverId => ({
                    server_id: serverId,
                    server_name: data.trends[serverId].server_name || `Serveur ${serverId}`,
                    data: data.trends[serverId].data || []
                }));
                
                if (trendsArray.length > 0) {
                    console.log(`📊 Graphique mis à jour: ${data.servers_count} serveurs, ${data.data_points_per_server} points/serveur`);
                    updateOffsetChart(trendsArray, data);
                } else {
                    console.warn('⚠️ Aucun serveur avec données disponibles');
                    showChartError('Aucune donnée disponible pour le graphique');
                }
            } else if (data.success && (!data.trends || Object.keys(data.trends || {}).length === 0)) {
                console.warn('⚠️ Aucune donnée de tendance disponible');
                showChartError('Aucune donnée disponible pour le graphique');
            } else {
                console.warn('⚠️ Format de données incorrect:', data);
                showChartError('Format de données invalide');
            }
        })
        .catch(error => {
            console.error('❌ Erreur chargement données graphique:', error);
            
            // Amélioration de la gestion des erreurs
            if (error.message.includes('Session expirée')) {
                showChartError('Rechargement en cours...');
                return; // Éviter l'affichage d'erreurs supplémentaires
            }
            
            // Gestion spécifique des erreurs d'authentification
            if (error.message.includes('non authentifié') || error.message.includes('401')) {
                showChartError('Session expirée - Veuillez vous reconnecter');
                // Optionnel: rediriger vers la page de connexion après un délai
                setTimeout(() => {
                    if (confirm('Votre session a expiré. Voulez-vous vous reconnecter ?')) {
                        window.location.href = '/login';
                    }
                }, 5000);
            } else {
                showChartError('Erreur de chargement des données');
            }
        });
}

// Fonction pour afficher les erreurs sur le graphique - VERSION AMÉLIORÉE
function showChartError(message) {
    console.warn(`📊 Affichage erreur graphique: ${message}`);
    
    if (offsetChart) {
        // Effacer les données existantes
        offsetChart.data.labels = [];
        offsetChart.data.datasets = [];
        
        // Ajouter un dataset d'erreur
        offsetChart.data.labels = ['Erreur'];
        offsetChart.data.datasets = [{
            label: message,
            data: [0],
            borderColor: '#dc3545',
            backgroundColor: '#dc354520',
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5
        }];
        
        // Configurer les échelles pour l'erreur
        offsetChart.options.scales.y.min = -10;
        offsetChart.options.scales.y.max = 10;
        
        // Mettre à jour le titre si disponible
        if (offsetChart.options.plugins.title) {
            offsetChart.options.plugins.title.text = `Graphique NTP - ${message}`;
        }
        
        // Mettre à jour le graphique
        offsetChart.update('none'); // Animation désactivée pour les erreurs
        
        console.log(`📊 Graphique mis à jour avec message d'erreur: ${message}`);
    } else {
        console.error('❌ Impossible d\'afficher l\'erreur - Graphique non initialisé');
        
        // Essayer de trouver le conteneur du graphique pour afficher un message
        const chartContainer = document.getElementById('offsetChart');
        if (chartContainer && chartContainer.parentElement) {
            // Remplacer le canvas par un message d'erreur
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-warning d-flex align-items-center';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>Graphique indisponible</strong><br>
                    ${message}
                </div>
            `;
            chartContainer.style.display = 'none';
            chartContainer.parentElement.appendChild(errorDiv);
        }
    }
}

// Mettre à jour le graphique des écarts - VERSION AMÉLIORÉE ET STABILISÉE
function updateOffsetChart(trends, metadata = null) {
    // Vérifications améliorées
    if (!offsetChart) {
        console.error('❌ Graphique non initialisé');
        return;
    }
    
    if (!trends || !Array.isArray(trends) || trends.length === 0) {
        console.warn('⚠️ Données insuffisantes pour le graphique:', trends);
        showChartError('Aucune donnée de serveur disponible');
        return;
    }
    
    // Vérifier que les données contiennent des points valides
    const validTrends = trends.filter(serverData => 
        serverData && serverData.data && Array.isArray(serverData.data) && serverData.data.length > 0
    );
    
    if (validTrends.length === 0) {
        console.warn('⚠️ Aucune donnée valide trouvée dans les tendances');
        showChartError('Aucune donnée temporelle disponible');
        return;
    }
    
    console.log(`📊 Traitement de ${validTrends.length} serveurs avec données valides`);
    
    // Convertir les données en format Chart.js pour axe category
    const datasets = [];
    const colors = [
        '#28a745', // Vert
        '#007bff', // Bleu  
        '#ffc107', // Jaune
        '#dc3545', // Rouge
        '#6f42c1', // Violet
        '#fd7e14', // Orange
        '#20c997', // Teal
        '#e83e8c'  // Rose
    ];
    
    // Calculer les limites dynamiques des données et collecter tous les timestamps
    let allValues = [];
    let allTimestamps = [];
    
    // Collecter tous les timestamps uniques pour créer les labels
    validTrends.forEach(serverData => {
        serverData.data.forEach(point => {
            if (point && point.timestamp) {
                const timestamp = point.timestamp;
                if (!allTimestamps.includes(timestamp)) {
                    allTimestamps.push(timestamp);
                }
            }
        });
    });
    
    if (allTimestamps.length === 0) {
        console.warn('⚠️ Aucun timestamp valide trouvé');
        showChartError('Données temporelles invalides');
        return;
    }
    
    // Trier les timestamps chronologiquement
    allTimestamps.sort();
    
    // Créer des labels formatés pour l'affichage
    const formattedLabels = allTimestamps.map(timestamp => {
        const date = new Date(timestamp);
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
    
    // Créer les datasets avec des valeurs alignées sur les timestamps
    validTrends.forEach((serverData, index) => {
        // Créer un mapping des timestamps vers les valeurs pour ce serveur
        const dataMap = {};
        let validPointsCount = 0;
        
        serverData.data.forEach(point => {
            if (point && point.timestamp) {
                // Essayer différents champs pour l'offset (avg_offset, offset, etc.)
                let offset = null;
                if (typeof point.avg_offset === 'number') {
                    offset = point.avg_offset * 1000; // Convertir en millisecondes
                } else if (typeof point.offset === 'number') {
                    offset = point.offset * 1000;
                } else if (typeof point.raw_avg === 'number') {
                    offset = point.raw_avg * 1000;
                }
                
                if (offset !== null) {
                    dataMap[point.timestamp] = offset;
                    allValues.push(offset);
                    validPointsCount++;
                }
            }
        });
        
        if (validPointsCount === 0) {
            console.warn(`⚠️ Aucun point valide pour le serveur ${serverData.server_name || index}`);
            return;
        }
        
        // Créer le tableau de données aligné sur tous les timestamps
        const alignedData = allTimestamps.map(timestamp => {
            return dataMap[timestamp] !== undefined ? dataMap[timestamp] : null;
        });
        
        if (alignedData.some(val => val !== null)) {
            datasets.push({
                label: serverData.server_name || `Serveur ${index + 1}`,
                data: alignedData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                spanGaps: false  // Ne pas connecter les valeurs null
            });
        }
    });
    
    if (datasets.length === 0) {
        console.warn('⚠️ Aucun dataset valide généré');
        showChartError('Impossible de générer le graphique');
        return;
    }
    
    // NOUVEAU: Calculer les limites dynamiques avec marge de sécurité
    if (allValues.length > 0) {
        const minValue = Math.min(...allValues);
        const maxValue = Math.max(...allValues);
        const range = maxValue - minValue;
        const margin = Math.max(range * 0.1, 10); // Marge de 10% ou minimum 10ms
        
        // Appliquer les nouvelles limites dynamiques
        const dynamicMin = minValue - margin;
        const dynamicMax = maxValue + margin;
        
        offsetChart.options.scales.y.min = dynamicMin;
        offsetChart.options.scales.y.max = dynamicMax;
        
        // AMÉLIORATION: Mettre à jour les limites de zoom si disponibles
        if (offsetChart.options.plugins.zoom && offsetChart.options.plugins.zoom.limits) {
            offsetChart.options.plugins.zoom.limits.y = {
                min: dynamicMin - margin, // Encore plus de marge pour le zoom
                max: dynamicMax + margin
            };
        }
        
        console.log(`📊 Limites dynamiques appliquées: Y [${dynamicMin.toFixed(1)}, ${dynamicMax.toFixed(1)}]ms`);
    }
    
    // Mettre à jour les données du graphique
    offsetChart.data.labels = formattedLabels;
    offsetChart.data.datasets = datasets;
    
    // Mettre à jour le graphique
    offsetChart.update('active');
    
    // Log des statistiques
    const totalPoints = allValues.length;
    const avgOffset = totalPoints > 0 ? (allValues.reduce((a, b) => a + b, 0) / totalPoints).toFixed(1) : 0;
    
    console.log(`✅ Graphique mis à jour avec succès: ${datasets.length} serveurs, ${totalPoints} points total, offset moyen: ${avgOffset}ms`);
    
    // Mettre à jour les métadonnées si disponibles
    if (metadata && offsetChart.options.plugins.title) {
        if (metadata.period_hours) {
            offsetChart.options.plugins.title.text = `Écarts de synchronisation NTP (${metadata.period_hours}h glissantes)`;
        }
    }
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
        const response = await fetch('/api/system/time', { credentials: 'include' });
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
        const timezoneEl = document.getElementById('system-timezone');
        timezoneEl.textContent = timezone;
        
        // Ajouter indicateur visuel si erreur système
        if (!systemData.success) {
            timezoneEl.className = 'badge bg-warning';
            timezoneEl.title = 'Données système partiellement disponibles';
        } else {
            timezoneEl.className = 'badge bg-info';
            timezoneEl.title = 'Données système en temps réel';
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
        
        const timezoneEl = document.getElementById('system-timezone');
        timezoneEl.textContent = 'Erreur API';
        timezoneEl.className = 'badge bg-danger';
        timezoneEl.title = 'Impossible de récupérer les données système';
        
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
        
        const response = await fetch('/api/ntp/servers', { credentials: 'include' });
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
        // Attendre que le gestionnaire d'alertes soit disponible
        if (window.alertManager && typeof window.alertManager.getDashboardData === 'function') {
            const alertData = await window.alertManager.getDashboardData();
            if (alertData) {
                updateAlertsWidget(alertData);
            }
        } else {
            // Réessayer après un court délai si le gestionnaire n'est pas encore prêt
            console.log('🔄 En attente du gestionnaire d\'alertes...');
            setTimeout(async () => {
                if (window.alertManager && typeof window.alertManager.getDashboardData === 'function') {
                    const alertData = await window.alertManager.getDashboardData();
                    if (alertData) {
                        updateAlertsWidget(alertData);
                    }
                } else {
                    console.warn('⚠️ Gestionnaire d\'alertes non disponible - Chargement des alertes basiques');
                    loadBasicAlerts();
                }
            }, 500); // Attendre 500ms
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des statistiques:', error);
        // Fallback vers les alertes basiques en cas d'erreur
        loadBasicAlerts();
    }
}

// AMÉLIORATION: Fonction pour mettre à jour le widget des alertes (3 alertes + synchronisation)
function updateAlertsWidget(alertData) {
    if (!alertData) return;
    
    console.log('Mise à jour widget alertes:', alertData);
    
    // SYNCHRONISATION: Mettre à jour TOUS les compteurs d'alertes
    const alertsCount = alertData.total_active || 0;
    
    // Compteur principal dashboard
    const dashboardAlertsCountEl = document.getElementById('alerts-count');
    if (dashboardAlertsCountEl) dashboardAlertsCountEl.textContent = alertsCount;
    
    // Compteur section "Alertes Récentes" avec couleur dynamique
    const activeAlertsCountEl = document.getElementById('active-alerts-count');
    if (activeAlertsCountEl) {
        activeAlertsCountEl.textContent = alertsCount;
        // AMÉLIORATION: Badge coloré selon le nombre d'alertes
        if (alertsCount === 0) {
            activeAlertsCountEl.className = 'badge bg-success';
        } else if (alertsCount <= 3) {
            activeAlertsCountEl.className = 'badge bg-warning';
        } else {
            activeAlertsCountEl.className = 'badge bg-danger';
        }
    }
    
    // NOUVEAU: Synchroniser le badge navigation
    const navBadges = document.querySelectorAll('.alerts-count-badge');
    navBadges.forEach(badge => {
        badge.textContent = alertsCount;
        badge.className = `badge ms-1 alerts-count-badge ${alertsCount > 0 ? 'bg-danger' : 'bg-secondary'}`;
    });
    
    // Compteurs détaillés (si présents)
    const dashboardTotalAlertsEl = document.getElementById('dashboard-total-alerts');
    const dashboardCriticalAlertsEl = document.getElementById('dashboard-critical-alerts');
    const dashboardWarningAlertsEl = document.getElementById('dashboard-warning-alerts');
    
    if (dashboardTotalAlertsEl) dashboardTotalAlertsEl.textContent = alertsCount;
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
    
    // AMÉLIORATION: Afficher les 3 dernières alertes CLIQUABLES
    const recentAlertsContainer = document.getElementById('recent-alerts');
    if (recentAlertsContainer) {
        if (alertData.recent && alertData.recent.length > 0) {
            let recentHtml = '';
            // Afficher les 3 dernières alertes
            alertData.recent.slice(0, 3).forEach(alert => {
                const severityClass = window.alertManager ? window.alertManager.getSeverityClass(alert.severity) : 'secondary';
                const severityIcon = getSeverityIcon(alert.severity);
                const timeAgo = getTimeAgo(new Date(alert.created_at));
                
                // NOUVEAU: Rendre chaque alerte cliquable
                recentHtml += `
                    <div class="alert alert-${severityClass} alert-dismissible fade show mb-2 cursor-pointer" 
                         onclick="viewAlertDetail(${alert.id})" 
                         style="cursor: pointer; transition: all 0.2s;"
                         onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'"
                         onmouseout="this.style.boxShadow='none'">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="alert-heading mb-1">
                                    ${severityIcon} ${alert.title}
                                </h6>
                                <p class="mb-1 small">${alert.description}</p>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>${timeAgo}
                                    <span class="ms-2">
                                        <i class="fas fa-server me-1"></i>${alert.server_name || 'Système'}
                                    </span>
                                </small>
                            </div>
                            <div class="text-end">
                                <small class="text-muted">Cliquer pour détails</small>
                                <br>
                                <i class="fas fa-chevron-right text-muted"></i>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            // NOUVEAU: Ajouter un lien vers toutes les alertes si plus de 3
            if (alertData.recent.length > 3) {
                recentHtml += `
                    <div class="text-center mt-2">
                        <button class="btn btn-outline-primary btn-sm" onclick="openAlertsModal()">
                            <i class="fas fa-list me-1"></i>
                            Voir toutes les alertes (${alertData.total_active})
                        </button>
                    </div>
                `;
            }
            
            recentAlertsContainer.innerHTML = recentHtml;
        } else {
            recentAlertsContainer.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-check-circle text-success me-2 fa-2x"></i>
                    <p class="mb-0">Aucune alerte active</p>
                    <small>Système fonctionnel</small>
                </div>
            `;
        }
    }
    
    console.log(`Widget alertes mis à jour: ${alertsCount} alertes actives`);
}

// NOUVELLE FONCTION: Obtenir l'icône selon la sévérité
function getSeverityIcon(severity) {
    switch(severity?.toLowerCase()) {
        case 'critical':
            return '<i class="fas fa-exclamation-circle text-danger"></i>';
        case 'warning':
            return '<i class="fas fa-exclamation-triangle text-warning"></i>';
        case 'info':
            return '<i class="fas fa-info-circle text-info"></i>';
        default:
            return '<i class="fas fa-bell text-secondary"></i>';
    }
}

// NOUVELLE FONCTION: Voir le détail d'une alerte
function viewAlertDetail(alertId) {
    console.log(`🔍 Affichage détail alerte: ${alertId}`);
    
    // 🔧 AMÉLIORATION : Récupérer d'abord les détails de l'alerte via API
    fetch(`/api/alerts/${alertId}`, { credentials: 'include' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(alertData => {
            console.log('📊 Détails alerte récupérés:', alertData);
            
            // Créer et afficher un modal avec les détails complets
            showAlertDetailModal(alertData);
        })
        .catch(error => {
            console.warn('⚠️ Impossible de récupérer les détails de l\'alerte:', error);
            
            // Fallback : ouvrir le modal des alertes générique
            if (typeof openAlertsModal === 'function') {
                openAlertsModal();
                // Mettre en évidence l'alerte spécifique dans le modal
                setTimeout(() => {
                    const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
                    if (alertElement) {
                        alertElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        alertElement.classList.add('border-primary', 'border-2');
                        setTimeout(() => {
                            alertElement.classList.remove('border-primary', 'border-2');
                        }, 3000);
                    }
                }, 500);
            } else {
                // Notification d'erreur plus informative
                const errorMsg = `Impossible d'afficher les détails de l'alerte #${alertId}. 
                \nErreur: ${error.message}
                \n\nVeuillez vérifier votre connexion ou contacter l'administrateur.`;
                alert(errorMsg);
            }
        });
}

// 🔧 NOUVELLE FONCTION : Afficher un modal détaillé pour une alerte
function showAlertDetailModal(alertData) {
    // Créer le modal dynamiquement s'il n'existe pas
    let modal = document.getElementById('alertDetailModal');
    if (!modal) {
        modal = createAlertDetailModal();
        document.body.appendChild(modal);
    }
    
    // Remplir le contenu du modal
    populateAlertDetailModal(modal, alertData);
    
    // Afficher le modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

// 🔧 NOUVELLE FONCTION : Créer le modal de détail d'alerte
function createAlertDetailModal() {
    const modalHtml = `
        <div class="modal fade" id="alertDetailModal" tabindex="-1" aria-labelledby="alertDetailModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="alertDetailModalLabel">
                            <i class="fas fa-exclamation-triangle me-2"></i>Détail de l'alerte
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="alertDetailModalBody">
                        <!-- Le contenu sera rempli dynamiquement -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        <button type="button" class="btn btn-warning" id="acknowledgeAlertBtn" onclick="acknowledgeAlert()">
                            <i class="fas fa-check me-1"></i>Acquitter
                        </button>
                        <button type="button" class="btn btn-success" id="resolveAlertBtn" onclick="resolveAlert()">
                            <i class="fas fa-check-double me-1"></i>Résoudre
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = modalHtml;
    return tempDiv.firstElementChild;
}

// 🔧 NOUVELLE FONCTION : Remplir le contenu du modal de détail
function populateAlertDetailModal(modal, alertData) {
    const modalBody = modal.querySelector('#alertDetailModalBody');
    const modalTitle = modal.querySelector('#alertDetailModalLabel');
    
    // Stocker l'ID de l'alerte pour les actions
    modal.setAttribute('data-alert-id', alertData.id);
    
    // Mettre à jour le titre
    const severityIcon = getSeverityIcon(alertData.severity);
    modalTitle.innerHTML = `${severityIcon} Alerte #${alertData.id} - ${alertData.title}`;
    
    // Déterminer les couleurs selon la sévérité
    const severityClass = alertData.severity === 'critical' ? 'danger' : 
                         alertData.severity === 'warning' ? 'warning' : 'info';
    
    // Formater les dates
    const createdAt = new Date(alertData.created_at).toLocaleString('fr-FR');
    const updatedAt = new Date(alertData.updated_at).toLocaleString('fr-FR');
    
    // Construire le contenu du modal
    modalBody.innerHTML = `
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card border-${severityClass}">
                    <div class="card-header bg-${severityClass} text-white">
                        <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Informations générales</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>Type :</strong> <span class="badge bg-${severityClass}">${alertData.alert_type}</span></p>
                        <p><strong>Sévérité :</strong> <span class="badge bg-${severityClass}">${alertData.severity_label}</span></p>
                        <p><strong>Statut :</strong> <span class="badge bg-secondary">${alertData.status}</span></p>
                        <p><strong>Créée le :</strong> ${createdAt}</p>
                        <p><strong>Mise à jour :</strong> ${updatedAt}</p>
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
        
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-comment me-2"></i>Message</h6>
                    </div>
                    <div class="card-body">
                        <p>${alertData.message}</p>
                    </div>
                </div>
            </div>
        </div>
        
        ${alertData.details ? `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-cog me-2"></i>Détails techniques</h6>
                    </div>
                    <div class="card-body">
                        <pre class="bg-light p-3 rounded"><code>${JSON.stringify(alertData.details, null, 2)}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
        ${alertData.acknowledged_at || alertData.resolved_at ? `
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-history me-2"></i>Historique des actions</h6>
                    </div>
                    <div class="card-body">
                        ${alertData.acknowledged_at ? `
                            <p><i class="fas fa-check text-warning me-2"></i>
                            Acquittée le ${new Date(alertData.acknowledged_at).toLocaleString('fr-FR')}</p>
                        ` : ''}
                        ${alertData.resolved_at ? `
                            <p><i class="fas fa-check-double text-success me-2"></i>
                            Résolue le ${new Date(alertData.resolved_at).toLocaleString('fr-FR')}</p>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
    `;
    
    // Gérer l'affichage des boutons selon le statut
    const acknowledgeBtn = modal.querySelector('#acknowledgeAlertBtn');
    const resolveBtn = modal.querySelector('#resolveAlertBtn');
    
    if (alertData.status === 'resolved') {
        acknowledgeBtn.style.display = 'none';
        resolveBtn.style.display = 'none';
    } else if (alertData.status === 'acknowledged') {
        acknowledgeBtn.style.display = 'none';
    }
}

// 🔧 NOUVELLES FONCTIONS : Actions sur les alertes
function acknowledgeAlert() {
    const modal = document.getElementById('alertDetailModal');
    const alertId = modal.getAttribute('data-alert-id');
    
    if (!alertId) return;
    
    fetch(`/api/alerts/${alertId}/acknowledge`, { 
        method: 'POST',
        credentials: 'include' 
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Alerte acquittée avec succès');
            // Fermer le modal et recharger les alertes
            bootstrap.Modal.getInstance(modal).hide();
            if (typeof loadBasicAlerts === 'function') {
                loadBasicAlerts();
            }
        } else {
            alert('Erreur lors de l\'acquittement: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erreur acquittement alerte:', error);
        alert('Erreur de communication avec le serveur');
    });
}

function resolveAlert() {
    const modal = document.getElementById('alertDetailModal');
    const alertId = modal.getAttribute('data-alert-id');
    
    if (!alertId) return;
    
    if (!confirm('Êtes-vous sûr de vouloir marquer cette alerte comme résolue ?')) {
        return;
    }
    
    fetch(`/api/alerts/${alertId}/resolve`, { 
        method: 'POST',
        credentials: 'include' 
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Alerte résolue avec succès');
            // Fermer le modal et recharger les alertes
            bootstrap.Modal.getInstance(modal).hide();
            if (typeof loadBasicAlerts === 'function') {
                loadBasicAlerts();
            }
        } else {
            alert('Erreur lors de la résolution: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erreur résolution alerte:', error);
        alert('Erreur de communication avec le serveur');
    });
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
    
    // Actualisation des données principales toutes les 30 secondes
    setInterval(() => {
        loadDashboardData();
        if (typeof loadStatistics === 'function') {
            loadStatistics();
        }
    }, 30000);
    
    // 🔧 NOUVEAU: Actualisation du graphique moins fréquente (toutes les 2 minutes)
    // pour éviter l'instabilité visuelle
    setInterval(() => {
        if (typeof loadOffsetChartData === 'function') {
            console.log('📊 Actualisation programmée du graphique des écarts');
            loadOffsetChartData();
        }
    }, 120000);  // 2 minutes au lieu de 30 secondes
}

// Fonction basique pour charger les alertes si le gestionnaire principal n'est pas disponible
function loadBasicAlerts() {
    try {
        fetch('/api/alerts/recent', { credentials: 'include' })
            .then(response => {
                console.log(`🔍 Réponse API alertes: ${response.status} ${response.statusText}`);
                
                // Vérifier si la réponse est du HTML (page de connexion)
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('text/html')) {
                    console.warn('⚠️ Session expirée pour API alertes - redirection page de connexion');
                    return { active_count: 0, alerts: [] }; // Valeurs par défaut
                }
                
                return response.json();
            })
            .then(data => {
                console.log('📢 Alertes basiques chargées:', data);
                
                // Mise à jour simple du compteur d'alertes - TOUJOURS AFFICHER LE BADGE
                const alertsCountEl = document.getElementById('alerts-count');
                const activeAlertsCountEl = document.getElementById('active-alerts-count');
                
                const alertCount = data.active_count || 0;
                
                if (alertsCountEl) {
                    alertsCountEl.textContent = alertCount;
                }
                
                if (activeAlertsCountEl) {
                    activeAlertsCountEl.textContent = alertCount;
                    // TOUJOURS AFFICHER LE BADGE avec couleur selon le nombre
                    activeAlertsCountEl.style.display = 'inline';
                    
                    // Couleurs du badge selon le niveau d'alerte
                    if (alertCount === 0) {
                        activeAlertsCountEl.className = 'badge bg-success';
                    } else if (alertCount <= 3) {
                        activeAlertsCountEl.className = 'badge bg-warning';
                    } else {
                        activeAlertsCountEl.className = 'badge bg-danger';
                    }
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
                        data.alerts.slice(0, 3).forEach((alert, index) => {
                            const severityClass = alert.severity === 'critical' ? 'danger' : 
                                                alert.severity === 'warning' ? 'warning' : 'info';
                            html += `
                                <div class="d-flex align-items-center mb-2 alert-item" style="cursor: pointer;" onclick="viewAlertDetail(${alert.id})">
                                    <i class="fas fa-exclamation-triangle text-${severityClass} me-2"></i>
                                    <div class="flex-grow-1">
                                        <small class="fw-semibold">${alert.title || 'Alerte'}</small>
                                        <div class="text-muted small">${alert.message || ''}</div>
                                        <small class="text-muted"><i class="fas fa-hand-pointer me-1"></i>Cliquer pour détails</small>
                                    </div>
                                </div>
                            `;
                        });
                        
                        // Ajouter un bouton "Voir toutes" si plus de 3 alertes
                        if (data.alerts.length > 3) {
                            html += `
                                <div class="text-center mt-2">
                                    <button class="btn btn-sm btn-outline-primary" onclick="openAlertsModal()">
                                        <i class="fas fa-eye me-1"></i>Voir toutes les alertes (${data.alerts.length})
                                    </button>
                                </div>
                            `;
                        }
                        
                        recentAlertsEl.innerHTML = html;
                    }
                }
            })
            .catch(error => {
                console.warn('⚠️ Impossible de charger les alertes basiques:', error);
                
                // Fallback: réinitialiser les compteurs à 0 mais TOUJOURS AFFICHER LE BADGE
                const alertsCountEl = document.getElementById('alerts-count');
                const activeAlertsCountEl = document.getElementById('active-alerts-count');
                
                if (alertsCountEl) alertsCountEl.textContent = '0';
                if (activeAlertsCountEl) {
                    activeAlertsCountEl.textContent = '0';
                    activeAlertsCountEl.className = 'badge bg-success'; // Vert pour 0 alerte
                    activeAlertsCountEl.style.display = 'inline'; // TOUJOURS VISIBLE
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
            fetch('/api/ntp/clients/connections', { credentials: 'include' }),
            fetch('/api/ntp/clients/statistics?hours=24', { credentials: 'include' }),
            fetch('/api/ntp/service/status', { credentials: 'include' })
        ]).then(responses => Promise.all(responses.map(r => r.json())));
        
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

// Fonction pour démarrer la mise à jour en temps réel de l'heure locale
function startLocalTimeUpdates() {
    // Arrêter le timer existant s'il y en a un
    if (localTimeTimer) {
        clearInterval(localTimeTimer);
    }
    
    // Fonction de mise à jour de l'heure locale
    function updateLocalTime() {
        const now = new Date();
        
        // Heure locale utilisateur (navigateur)
        const localTimeEl = document.getElementById('local-time');
        if (localTimeEl) {
            localTimeEl.textContent = now.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
        
        // Heure UTC
        const utcTimeEl = document.getElementById('utc-time');
        if (utcTimeEl) {
            utcTimeEl.textContent = now.toUTCString().slice(17, 25); // HH:MM:SS uniquement
        }
        
        // Timezone détecté automatiquement
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const timezoneEl = document.getElementById('system-timezone');
        if (timezoneEl) {
            // Simplifier l'affichage du timezone
            const shortTimezone = timezone.split('/').pop() || timezone;
            timezoneEl.textContent = shortTimezone;
            timezoneEl.className = 'badge bg-success';
            timezoneEl.title = `Timezone: ${timezone}`;
        }
        
        // Offset UTC du navigateur
        const offsetMinutes = now.getTimezoneOffset();
        const offsetHours = Math.abs(offsetMinutes) / 60;
        const offsetSign = offsetMinutes <= 0 ? '+' : '-'; // Inversé car getTimezoneOffset retourne l'inverse
        const offsetStr = `${offsetSign}${Math.floor(offsetHours).toString().padStart(2, '0')}:${(Math.abs(offsetMinutes) % 60).toString().padStart(2, '0')}`;
        
        // Heure d'été détectée automatiquement
        const january = new Date(now.getFullYear(), 0, 1);
        const july = new Date(now.getFullYear(), 6, 1);
        const stdOffset = Math.max(january.getTimezoneOffset(), july.getTimezoneOffset());
        const isDst = now.getTimezoneOffset() < stdOffset;
        
        const dstStatusEl = document.getElementById('dst-status');
        if (dstStatusEl) {
            dstStatusEl.textContent = isDst ? 'Oui' : 'Non';
            dstStatusEl.className = isDst ? 'badge bg-warning' : 'badge bg-info';
            dstStatusEl.title = isDst ? 'Heure d\'été active' : 'Heure standard active';
        }
        
        // Badge timezone principal dans l'en-tête
        const headerTimezoneEl = document.querySelector('.badge.bg-emerald-light');
        if (headerTimezoneEl) {
            const country = timezone.split('/')[0] === 'Africa' ? 'Afrique' : 
                          timezone.split('/')[0] === 'Europe' ? 'Europe' : 
                          timezone.split('/')[0] === 'America' ? 'Amérique' : timezone.split('/')[0];
            headerTimezoneEl.textContent = `${country} ${offsetStr}`;
        }
    }
    
    // Première exécution immédiate
    updateLocalTime();
    
    // Mettre à jour chaque seconde
    localTimeTimer = setInterval(updateLocalTime, 1000);
    
    console.log('✅ Mise à jour temps réel de l\'heure locale activée');
}

// Fonction pour arrêter les mises à jour
function stopLocalTimeUpdates() {
    if (localTimeTimer) {
        clearInterval(localTimeTimer);
        localTimeTimer = null;
        console.log('⏹️ Mise à jour temps réel de l\'heure locale arrêtée');
    }
}

// ================== AMÉLIORATIONS EMERAUDENTP VIZ ==================

// Surcharger la fonction initDashboard originale pour ajouter nos améliorations
(function() {
    const originalInitDashboard = window.initDashboard;
    window.initDashboard = function() {
        // Appeler la fonction originale
        if (originalInitDashboard) {
            originalInitDashboard();
        }
        
        // Ajouter nos améliorations
        console.log('🔧 Application des améliorations EmaraudeNTP VIZ...');
        
        // Démarrer les mises à jour temps réel
        setTimeout(() => {
            startLocalTimeUpdates();
        }, 1000); // Délai pour s'assurer que le DOM est prêt
    };
})();

// ⭐ NOUVELLE FONCTION: Calculer le temps écoulé depuis une date (pour dernière synchronisation)
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSeconds < 60) {
        return `${diffSeconds}s`;
    } else if (diffMinutes < 60) {
        return `${diffMinutes}min`;
    } else if (diffHours < 24) {
        return `${diffHours}h`;
    } else {
        return `${diffDays}j`;
    }
}

// ⭐ NOUVELLE FONCTION: Formater une durée en français
function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days} jour${days > 1 ? 's' : ''}`;
    } else if (hours > 0) {
        return `${hours} heure${hours > 1 ? 's' : ''}`;
    } else if (minutes > 0) {
        return `${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else {
        return `${seconds} seconde${seconds > 1 ? 's' : ''}`;
    }
}

/**
 * 🔧 CORRECTION: Fonction pour actualiser tous les badges d'alertes
 */
function updateAllAlertsBadges() {
    fetch('/api/alerts/summary', { credentials: 'include' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const alertsCount = data.total_active || 0;
                
                // Mettre à jour tous les badges d'alertes
                const selectors = [
                    '#alerts-count',
                    '#active-alerts-count', 
                    '.alerts-count-badge'
                ];
                
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        element.textContent = alertsCount;
                        
                        // Appliquer le style approprié
                        if (element.classList.contains('badge')) {
                            element.className = element.className.replace(/bg-(danger|secondary)/, 
                                alertsCount > 0 ? 'bg-danger' : 'bg-secondary');
                            element.style.display = alertsCount > 0 ? 'inline' : 'none';
                        }
                    });
                });
                
                console.log('✅ Badges alertes actualisés:', alertsCount);
            }
        })
        .catch(error => {
            console.error('❌ Erreur actualisation badges alertes:', error);
        });
}

// Appel automatique toutes les 30 secondes
setInterval(updateAllAlertsBadges, 30000);

// Appel initial
document.addEventListener('DOMContentLoaded', updateAllAlertsBadges);

// Fonction utilitaire pour gérer les erreurs d'authentification
function handleAuthenticationError(apiEndpoint) {
    console.warn(`🔒 Session expirée pour ${apiEndpoint} - Redirection vers login`);
    
    // Afficher une notification à l'utilisateur
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <div>
                <strong>Session expirée</strong><br>
                <small>Reconnexion automatique en cours...</small>
            </div>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Redirection automatique après 3 secondes
    setTimeout(() => {
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }, 3000);
    
    return false;
}

