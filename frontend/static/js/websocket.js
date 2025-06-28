/**
 * NTP Monitor Enterprise - Gestion WebSocket
 */

let socket = null;
let connectionAttempts = 0;
const maxConnectionAttempts = 5;
const reconnectDelay = 5000; // 5 secondes

/**
 * Initialiser la connexion WebSocket
 */
function initWebSocket() {
    console.log('Initialisation WebSocket...');
    
    try {
        socket = io(window.location.origin, {
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true
        });
        
        setupSocketEventHandlers();
        connectionAttempts = 0;
        
    } catch (error) {
        console.error('Erreur initialisation WebSocket:', error);
        scheduleReconnect();
    }
}

/**
 * Configurer les gestionnaires d'événements WebSocket
 */
function setupSocketEventHandlers() {
    if (!socket) return;
    
    // Connexion établie
    socket.on('connect', function() {
        console.log('WebSocket connecté');
        AppState.isConnected = true;
        updateConnectionStatus(true);
        
        if (typeof showNotification === 'function') {
            showNotification('Connexion temps réel établie', 'success', 3000);
        }
    });
    
    // Connexion fermée
    socket.on('disconnect', function(reason) {
        console.log('WebSocket déconnecté:', reason);
        AppState.isConnected = false;
        updateConnectionStatus(false);
        
        if (typeof showNotification === 'function') {
            showNotification('Connexion temps réel interrompue', 'warning', 3000);
        }
        
        // Tentative de reconnexion automatique
        if (reason === 'io server disconnect') {
            scheduleReconnect();
        }
    });
    
    // Erreur de connexion
    socket.on('connect_error', function(error) {
        console.error('Erreur connexion WebSocket:', error);
        AppState.isConnected = false;
        updateConnectionStatus(false);
        scheduleReconnect();
    });
    
    // Événements métier
    socket.on('ntp_update', handleNTPUpdate);
    socket.on('system_alert', handleSystemAlert);
    socket.on('server_status', handleServerStatus);
    socket.on('client_activity', handleClientActivity);
}

/**
 * Mettre à jour le statut de connexion dans l'interface
 */
function updateConnectionStatus(connected) {
    const statusIndicators = document.querySelectorAll('.connection-status');
    
    statusIndicators.forEach(indicator => {
        if (connected) {
            indicator.className = 'connection-status text-success';
            indicator.innerHTML = '<i class="fas fa-circle me-1"></i>Connecté';
        } else {
            indicator.className = 'connection-status text-danger';
            indicator.innerHTML = '<i class="fas fa-circle me-1"></i>Déconnecté';
        }
    });
}

/**
 * Programmer une tentative de reconnexion
 */
function scheduleReconnect() {
    if (connectionAttempts >= maxConnectionAttempts) {
        console.warn('Nombre maximum de tentatives de reconnexion atteint');
        if (typeof showNotification === 'function') {
            showNotification('Impossible de rétablir la connexion temps réel', 'danger', 0);
        }
        return;
    }
    
    connectionAttempts++;
    console.log(`Tentative de reconnexion ${connectionAttempts}/${maxConnectionAttempts} dans ${reconnectDelay/1000}s...`);
    
    setTimeout(() => {
        if (socket) {
            socket.connect();
        } else {
            initWebSocket();
        }
    }, reconnectDelay);
}

/**
 * Gestionnaire de mise à jour NTP
 */
function handleNTPUpdate(data) {
    console.log('Mise à jour NTP reçue:', data);
    
    if (typeof updateNTPServerDisplay === 'function') {
        updateNTPServerDisplay(data);
    }
    
    // Mettre à jour l'état global
    if (data.server_id) {
        const serverIndex = AppState.ntpServers.findIndex(s => s.id === data.server_id);
        if (serverIndex !== -1) {
            AppState.ntpServers[serverIndex] = { ...AppState.ntpServers[serverIndex], ...data };
        }
    }
}

/**
 * Gestionnaire d'alerte système
 */
function handleSystemAlert(data) {
    console.log('Alerte système reçue:', data);
    
    if (typeof showNotification === 'function') {
        const alertType = data.level === 'critical' ? 'danger' : 
                         data.level === 'warning' ? 'warning' : 'info';
        showNotification(data.message, alertType, 10000);
    }
    
    // Ajouter à l'état global
    AppState.alerts.unshift({
        id: data.id || Date.now(),
        message: data.message,
        level: data.level,
        timestamp: new Date()
    });
    
    // Limiter le nombre d'alertes en mémoire
    if (AppState.alerts.length > 50) {
        AppState.alerts = AppState.alerts.slice(0, 50);
    }
}

/**
 * Gestionnaire de statut serveur
 */
function handleServerStatus(data) {
    console.log('Statut serveur reçu:', data);
    
    if (typeof updateServerStatusDisplay === 'function') {
        updateServerStatusDisplay(data);
    }
}

/**
 * Gestionnaire d'activité client
 */
function handleClientActivity(data) {
    console.log('Activité client reçue:', data);
    
    if (typeof updateClientActivityDisplay === 'function') {
        updateClientActivityDisplay(data);
    }
}

/**
 * Envoyer un message via WebSocket
 */
function sendSocketMessage(event, data) {
    if (socket && AppState.isConnected) {
        socket.emit(event, data);
        return true;
    } else {
        console.warn('WebSocket non connecté, impossible d\'envoyer le message');
        return false;
    }
}

/**
 * S'abonner à un événement spécifique
 */
function subscribeToEvent(eventName, callback) {
    if (socket) {
        socket.on(eventName, callback);
    }
}

/**
 * Se désabonner d'un événement
 */
function unsubscribeFromEvent(eventName, callback) {
    if (socket) {
        socket.off(eventName, callback);
    }
}

// Exporter les fonctions pour usage global
window.initWebSocket = initWebSocket;
window.sendSocketMessage = sendSocketMessage;
window.subscribeToEvent = subscribeToEvent;
window.unsubscribeFromEvent = unsubscribeFromEvent; 