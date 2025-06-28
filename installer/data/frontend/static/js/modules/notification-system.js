/**
 * Système de Notifications Globales
 * NTP Monitor Enterprise
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        this.container = null;
        
        this.init();
    }
    
    init() {
        this.createContainer();
        this.setupStyles();
        this.bindGlobalFunction();
    }
    
    createContainer() {
        // Vérifier si le conteneur existe déjà
        this.container = document.getElementById('notification-container');
        
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
    }
    
    setupStyles() {
        // Injecter les styles CSS si pas déjà fait
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    pointer-events: none;
                    max-width: 400px;
                    width: 100%;
                }
                
                .notification {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    margin-bottom: 12px;
                    padding: 16px 20px;
                    border-left: 4px solid;
                    animation: slideInRight 0.3s ease-out;
                    pointer-events: auto;
                    position: relative;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                
                .notification:hover {
                    transform: translateX(-4px);
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
                }
                
                .notification.notification-success {
                    border-left-color: #28a745;
                    background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
                }
                
                .notification.notification-error {
                    border-left-color: #dc3545;
                    background: linear-gradient(135deg, #ffffff 0%, #fff8f8 100%);
                }
                
                .notification.notification-warning {
                    border-left-color: #ffc107;
                    background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
                }
                
                .notification.notification-info {
                    border-left-color: #17a2b8;
                    background: linear-gradient(135deg, #ffffff 0%, #f0fcff 100%);
                }
                
                .notification-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }
                
                .notification-icon {
                    font-size: 20px;
                    margin-right: 12px;
                    flex-shrink: 0;
                }
                
                .notification-icon.icon-success { color: #28a745; }
                .notification-icon.icon-error { color: #dc3545; }
                .notification-icon.icon-warning { color: #ffc107; }
                .notification-icon.icon-info { color: #17a2b8; }
                
                .notification-title {
                    font-weight: 600;
                    color: #495057;
                    flex-grow: 1;
                    font-size: 14px;
                }
                
                .notification-close {
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #6c757d;
                    cursor: pointer;
                    padding: 0;
                    line-height: 1;
                    transition: color 0.2s ease;
                }
                
                .notification-close:hover {
                    color: #495057;
                }
                
                .notification-message {
                    color: #6c757d;
                    font-size: 13px;
                    line-height: 1.4;
                    margin: 0;
                }
                
                .notification-actions {
                    margin-top: 12px;
                    display: flex;
                    gap: 8px;
                }
                
                .notification-btn {
                    background: none;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .notification-btn:hover {
                    background: #f8f9fa;
                    border-color: #adb5bd;
                }
                
                .notification-btn.btn-primary {
                    background: #007bff;
                    border-color: #007bff;
                    color: white;
                }
                
                .notification-btn.btn-primary:hover {
                    background: #0056b3;
                    border-color: #0056b3;
                }
                
                .notification-progress {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: rgba(0, 0, 0, 0.1);
                    transition: width linear;
                }
                
                .notification-progress.progress-success { background: #28a745; }
                .notification-progress.progress-error { background: #dc3545; }
                .notification-progress.progress-warning { background: #ffc107; }
                .notification-progress.progress-info { background: #17a2b8; }
                
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                
                @keyframes slideOutRight {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
                
                .notification.removing {
                    animation: slideOutRight 0.3s ease-in;
                }
                
                @media (max-width: 768px) {
                    .notification-container {
                        top: 10px;
                        right: 10px;
                        left: 10px;
                        max-width: none;
                    }
                    
                    .notification {
                        padding: 12px 16px;
                        margin-bottom: 8px;
                    }
                    
                    .notification-title {
                        font-size: 13px;
                    }
                    
                    .notification-message {
                        font-size: 12px;
                    }
                }
                
                /* Animation pour empiler les notifications */
                .notification:not(:first-child) {
                    margin-top: -8px;
                    transform: scale(0.98);
                    opacity: 0.9;
                }
                
                .notification:not(:first-child):not(:nth-child(2)) {
                    transform: scale(0.96);
                    opacity: 0.8;
                }
                
                .notification:nth-child(n+4) {
                    display: none;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    bindGlobalFunction() {
        // Rendre la fonction globalement accessible
        window.showNotification = (message, type = 'info', duration = this.defaultDuration, options = {}) => {
            return this.show(message, type, duration, options);
        };
        
        window.hideNotification = (id) => {
            return this.hide(id);
        };
        
        window.clearAllNotifications = () => {
            return this.clearAll();
        };
    }
    
    show(message, type = 'info', duration = this.defaultDuration, options = {}) {
        const notification = this.createNotification(message, type, duration, options);
        
        // Limiter le nombre de notifications
        if (this.notifications.length >= this.maxNotifications) {
            this.hide(this.notifications[0].id);
        }
        
        this.notifications.push(notification);
        this.container.appendChild(notification.element);
        
        // Auto-hide après la durée spécifiée
        if (duration > 0) {
            this.startProgressBar(notification, duration);
            notification.timeout = setTimeout(() => {
                this.hide(notification.id);
            }, duration);
        }
        
        return notification.id;
    }
    
    createNotification(message, type, duration, options) {
        const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const notification = {
            id,
            type,
            message,
            duration,
            options,
            element: null,
            timeout: null
        };
        
        const element = document.createElement('div');
        element.className = `notification notification-${type}`;
        element.setAttribute('data-notification-id', id);
        
        const icon = this.getIcon(type);
        const title = options.title || this.getDefaultTitle(type);
        
        element.innerHTML = `
            <div class="notification-header">
                <div style="display: flex; align-items: center;">
                    <i class="notification-icon icon-${type} ${icon}"></i>
                    <div class="notification-title">${title}</div>
                </div>
                <button class="notification-close" onclick="hideNotification('${id}')">×</button>
            </div>
            <div class="notification-message">${message}</div>
            ${options.actions ? this.createActions(options.actions, id) : ''}
            ${duration > 0 ? `<div class="notification-progress progress-${type}" style="width: 100%;"></div>` : ''}
        `;
        
        notification.element = element;
        
        // Ajouter les event listeners
        this.attachEventListeners(notification, options);
        
        return notification;
    }
    
    createActions(actions, notificationId) {
        const actionsHTML = actions.map(action => `
            <button class="notification-btn ${action.class || ''}" 
                    onclick="notificationSystem.handleAction('${notificationId}', '${action.id}')">
                ${action.text}
            </button>
        `).join('');
        
        return `<div class="notification-actions">${actionsHTML}</div>`;
    }
    
    attachEventListeners(notification, options) {
        const element = notification.element;
        
        // Pause sur hover
        element.addEventListener('mouseenter', () => {
            if (notification.timeout) {
                clearTimeout(notification.timeout);
                this.pauseProgressBar(notification);
            }
        });
        
        // Reprendre sur mouse leave
        element.addEventListener('mouseleave', () => {
            if (notification.duration > 0) {
                const remaining = this.getRemainingTime(notification);
                if (remaining > 0) {
                    this.resumeProgressBar(notification, remaining);
                    notification.timeout = setTimeout(() => {
                        this.hide(notification.id);
                    }, remaining);
                }
            }
        });
        
        // Callback personnalisés
        if (options.onClick) {
            element.addEventListener('click', options.onClick);
        }
        
        if (options.onShow) {
            setTimeout(options.onShow, 100);
        }
    }
    
    startProgressBar(notification, duration) {
        const progressBar = notification.element.querySelector('.notification-progress');
        if (progressBar) {
            progressBar.style.transition = `width ${duration}ms linear`;
            progressBar.style.width = '0%';
            notification.startTime = Date.now();
            notification.originalDuration = duration;
        }
    }
    
    pauseProgressBar(notification) {
        const progressBar = notification.element.querySelector('.notification-progress');
        if (progressBar) {
            const currentWidth = progressBar.style.width;
            progressBar.style.transition = 'none';
            progressBar.style.width = currentWidth;
        }
    }
    
    resumeProgressBar(notification, remainingTime) {
        const progressBar = notification.element.querySelector('.notification-progress');
        if (progressBar) {
            progressBar.style.transition = `width ${remainingTime}ms linear`;
            progressBar.style.width = '0%';
        }
    }
    
    getRemainingTime(notification) {
        if (!notification.startTime || !notification.originalDuration) return 0;
        const elapsed = Date.now() - notification.startTime;
        return Math.max(0, notification.originalDuration - elapsed);
    }
    
    hide(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;
        
        // Annuler le timeout
        if (notification.timeout) {
            clearTimeout(notification.timeout);
        }
        
        // Animation de sortie
        notification.element.classList.add('removing');
        
        // Supprimer après l'animation
        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
            
            // Retirer de la liste
            this.notifications = this.notifications.filter(n => n.id !== id);
            
            // Callback onHide
            if (notification.options.onHide) {
                notification.options.onHide();
            }
        }, 300);
    }
    
    clearAll() {
        this.notifications.slice().forEach(notification => {
            this.hide(notification.id);
        });
    }
    
    handleAction(notificationId, actionId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification || !notification.options.actions) return;
        
        const action = notification.options.actions.find(a => a.id === actionId);
        if (action && action.callback) {
            action.callback(notificationId);
        }
        
        // Auto-hide la notification après action
        if (action && action.autoHide !== false) {
            this.hide(notificationId);
        }
    }
    
    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    getDefaultTitle(type) {
        const titles = {
            success: 'Succès',
            error: 'Erreur',
            warning: 'Attention',
            info: 'Information'
        };
        return titles[type] || titles.info;
    }
    
    // Méthodes utilitaires pour types spécifiques
    success(message, duration, options) {
        return this.show(message, 'success', duration, options);
    }
    
    error(message, duration, options) {
        return this.show(message, 'error', duration, options);
    }
    
    warning(message, duration, options) {
        return this.show(message, 'warning', duration, options);
    }
    
    info(message, duration, options) {
        return this.show(message, 'info', duration, options);
    }
    
    // Notifications avec actions
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const confirmOptions = {
                title: options.title || 'Confirmation',
                actions: [
                    {
                        id: 'cancel',
                        text: 'Annuler',
                        class: '',
                        callback: () => resolve(false)
                    },
                    {
                        id: 'confirm',
                        text: options.confirmText || 'Confirmer',
                        class: 'btn-primary',
                        callback: () => resolve(true)
                    }
                ],
                ...options
            };
            
            this.show(message, 'warning', 0, confirmOptions);
        });
    }
    
    // Notification de progression
    progress(message, options = {}) {
        const progressId = this.show(message, 'info', 0, {
            title: options.title || 'En cours...',
            ...options
        });
        
        return {
            id: progressId,
            update: (newMessage, percentage) => {
                const notification = this.notifications.find(n => n.id === progressId);
                if (notification) {
                    const messageElement = notification.element.querySelector('.notification-message');
                    if (messageElement) {
                        messageElement.textContent = newMessage;
                    }
                    
                    if (percentage !== undefined) {
                        let progressBar = notification.element.querySelector('.notification-progress');
                        if (!progressBar) {
                            progressBar = document.createElement('div');
                            progressBar.className = 'notification-progress progress-info';
                            notification.element.appendChild(progressBar);
                        }
                        progressBar.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
                    }
                }
            },
            complete: (finalMessage, type = 'success') => {
                this.hide(progressId);
                if (finalMessage) {
                    setTimeout(() => {
                        this.show(finalMessage, type, 3000);
                    }, 300);
                }
            }
        };
    }
    
    // Notification persistante
    persistent(message, type = 'info', options = {}) {
        return this.show(message, type, 0, {
            title: options.title || 'Notification persistante',
            actions: [
                {
                    id: 'dismiss',
                    text: 'Fermer',
                    class: 'btn-primary',
                    callback: () => {} // Auto-hide par défaut
                }
            ],
            ...options
        });
    }
}

// Initialisation automatique
let notificationSystem;

document.addEventListener('DOMContentLoaded', () => {
    notificationSystem = new NotificationSystem();
    
    // Exposer globalement pour faciliter l'utilisation
    window.notificationSystem = notificationSystem;
});

// Export pour utilisation en module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
} 