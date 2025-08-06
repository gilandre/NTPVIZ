/**
 * Configuration Manager - Gestion avancée de la configuration système
 * NTP Monitor Enterprise
 */

class ConfigManager {
    constructor() {
        this.categories = {};
        this.currentCategory = null;
        this.isDirty = false;
        this.changeTimeout = null;
        this.validationErrors = {};
        
        this.init();
    }
    
    async init() {
        await this.loadCategories();
        this.setupEventListeners();
        this.setupValidation();
        this.setupAutoSave();
    }
    
    // ================== CHARGEMENT DES DONNÉES ==================
    
    async loadCategories() {
        try {
            const response = await fetch('/api/config/categories');
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Authentification requise. Veuillez vous reconnecter.');
                } else if (response.status === 403) {
                    throw new Error('Accès refusé. Permissions insuffisantes.');
                } else {
                    throw new Error(`Erreur serveur: ${response.status} ${response.statusText}`);
                }
            }
            
            this.categories = await response.json();
            this.renderCategoriesMenu();
            
            // Charger la première catégorie par défaut
            const firstCategory = Object.keys(this.categories)[0];
            if (firstCategory) {
                await this.loadCategory(firstCategory);
            }
            
        } catch (error) {
            console.error('Erreur lors du chargement des catégories:', error);
            this.showNotification(`Erreur de chargement des catégories: ${error.message}`, 'error');
            
            // Afficher un message d'erreur dans l'interface
            const menuContainer = document.getElementById('config-categories-menu');
            if (menuContainer) {
                menuContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Erreur de chargement</strong><br>
                        ${error.message}
                    </div>
                `;
            }
        }
    }
    
    async loadCategory(categoryName) {
        if (this.isDirty) {
            const confirmed = await this.confirmUnsavedChanges();
            if (!confirmed) return;
        }
        
        try {
            this.showLoadingSpinner(true);
            
            const response = await fetch(`/api/config/category/${categoryName}`);
            if (!response.ok) throw new Error('Erreur chargement catégorie');
            
            const categoryData = await response.json();
            this.currentCategory = categoryData;
            
            this.renderCategoryConfig(categoryData);
            this.updateCategoriesMenu(categoryName);
            this.isDirty = false;
            
        } catch (error) {
            console.error('Erreur lors du chargement de la catégorie:', error);
            this.showNotification(`Erreur de chargement: ${error.message}`, 'error');
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    // ================== RENDU DES INTERFACES ==================
    
    renderCategoriesMenu() {
        const menuContainer = document.getElementById('config-categories-menu');
        if (!menuContainer) return;
        
        const menuHTML = Object.entries(this.categories).map(([key, category]) => `
            <div class="category-item" data-category="${key}">
                <div class="category-header">
                    <i class="${category.icon}"></i>
                    <span class="category-name">${category.display_name}</span>
                    <span class="badge bg-secondary">${category.public_count}</span>
                </div>
                <div class="category-description">${category.description}</div>
            </div>
        `).join('');
        
        menuContainer.innerHTML = menuHTML;
    }
    
    renderCategoryConfig(categoryData) {
        const configContainer = document.getElementById('config-content');
        if (!configContainer) return;
        
        // Gestion spéciale pour la catégorie alertes
        if (categoryData.category === 'alerts') {
            this.renderAlertsConfig(categoryData);
            return;
        }
        
        const configHTML = `
            <div class="config-category-header">
                <h3>
                    <i class="${this.categories[categoryData.category]?.icon || 'fas fa-cog'}"></i>
                    ${categoryData.display_name}
                </h3>
                <p class="text-muted">${categoryData.description}</p>
                <div class="config-actions">
                    <button class="btn btn-success btn-sm" onclick="configManager.saveCategory()">
                        <i class="fas fa-save"></i> Sauvegarder
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="configManager.resetCategory()">
                        <i class="fas fa-undo"></i> Réinitialiser
                    </button>
                    <button class="btn btn-info btn-sm" onclick="configManager.testConfiguration()">
                        <i class="fas fa-flask"></i> Tester
                    </button>
                </div>
            </div>
            
            <div class="config-form">
                ${this.renderConfigFields(categoryData.configs)}
            </div>
            
            <div class="config-footer">
                <small class="text-muted">
                    <i class="fas fa-clock"></i>
                    Dernière modification: ${categoryData.last_updated ? 
                        new Date(categoryData.last_updated).toLocaleString() : 'Jamais'}
                </small>
            </div>
        `;
        
        configContainer.innerHTML = configHTML;
        this.attachFieldEvents();
    }
    
    renderAlertsConfig(categoryData) {
        const configContainer = document.getElementById('config-content');
        if (!configContainer) return;
        
        const configHTML = `
            <div class="config-category-header">
                <h3>
                    <i class="fas fa-bell"></i>
                    Configuration des Alertes
                </h3>
                <p class="text-muted">Paramètres des seuils, notifications et rétention des alertes</p>
                <div class="config-actions">
                    <button class="btn btn-success btn-sm" onclick="configManager.saveAlertsConfig()">
                        <i class="fas fa-save"></i> Sauvegarder
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="configManager.resetAlertsConfig()">
                        <i class="fas fa-undo"></i> Réinitialiser
                    </button>
                    <button class="btn btn-info btn-sm" onclick="configManager.testAlertsConfig()">
                        <i class="fas fa-flask"></i> Tester
                    </button>
                </div>
            </div>
            
            <!-- Navigation par onglets -->
            <ul class="nav nav-tabs" id="alertsConfigTabs" role="tablist">
                <li class="nav-item">
                    <a class="nav-link active" id="thresholds-tab" data-bs-toggle="tab" 
                       href="#thresholds" role="tab">
                        <i class="fas fa-chart-line me-1"></i>Seuils d'Alerte
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" id="notifications-tab" data-bs-toggle="tab" 
                       href="#notifications" role="tab">
                        <i class="fas fa-bell me-1"></i>Notifications
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" id="retention-tab" data-bs-toggle="tab" 
                       href="#retention" role="tab">
                        <i class="fas fa-database me-1"></i>Rétention
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" id="advanced-tab" data-bs-toggle="tab" 
                       href="#advanced" role="tab">
                        <i class="fas fa-cogs me-1"></i>Avancé
                    </a>
                </li>
            </ul>
            
            <!-- Contenu des onglets -->
            <div class="tab-content mt-3" id="alertsConfigTabContent">
                ${this.renderThresholdsTab()}
                ${this.renderNotificationsTab()}
                ${this.renderRetentionTab()}
                ${this.renderAdvancedTab()}
            </div>
            
            <div class="config-footer mt-3">
                <small class="text-muted">
                    <i class="fas fa-clock"></i>
                    Dernière modification: ${categoryData.last_updated ? 
                        new Date(categoryData.last_updated).toLocaleString() : 'Jamais'}
                </small>
            </div>
        `;
        
        configContainer.innerHTML = configHTML;
        this.attachAlertsFieldEvents();
        this.loadAlertsConfigData();
    }
    
    renderThresholdsTab() {
        return `
            <div class="tab-pane fade show active" id="thresholds" role="tabpanel">
                <h6><i class="fas fa-exclamation-triangle text-warning me-2"></i>Seuils d'Alerte NTP</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Décalage Temporel (Offset)</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Seuil Avertissement (ms)</label>
                                    <input type="number" class="form-control" id="offset-warning-threshold" 
                                           value="100" min="1" max="10000">
                                    <small class="text-muted">Déclenche une alerte d'avertissement</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Seuil Critique (ms)</label>
                                    <input type="number" class="form-control" id="offset-critical-threshold" 
                                           value="1000" min="1" max="10000">
                                    <small class="text-muted">Déclenche une alerte critique</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Latence Réseau</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Seuil Avertissement (ms)</label>
                                    <input type="number" class="form-control" id="latency-warning-threshold" 
                                           value="500" min="1" max="5000">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Seuil Critique (ms)</label>
                                    <input type="number" class="form-control" id="latency-critical-threshold" 
                                           value="2000" min="1" max="5000">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Stratum</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Stratum Maximum Autorisé</label>
                                    <select class="form-select" id="stratum-max-threshold">
                                        <option value="3">3 (Recommandé)</option>
                                        <option value="4">4</option>
                                        <option value="5">5</option>
                                        <option value="6">6</option>
                                    </select>
                                    <small class="text-muted">Alerte si stratum dépasse cette valeur</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Disponibilité Serveur</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Timeout Connexion (s)</label>
                                    <input type="number" class="form-control" id="connection-timeout" 
                                           value="30" min="5" max="300">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Échecs Consécutifs</label>
                                    <input type="number" class="form-control" id="max-consecutive-failures" 
                                           value="3" min="1" max="10">
                                    <small class="text-muted">Nombre d'échecs avant alerte</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderNotificationsTab() {
        return `
            <div class="tab-pane fade" id="notifications" role="tabpanel">
                <h6><i class="fas fa-bell text-info me-2"></i>Configuration des Notifications</h6>
                
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Canaux de Notification</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="email-notifications" checked>
                                    <label class="form-check-label" for="email-notifications">
                                        <i class="fas fa-envelope me-1"></i>Notifications Email
                                    </label>
                                </div>
                                <div class="mb-3 mt-2">
                                    <label class="form-label">Adresses Email (séparées par des virgules)</label>
                                    <textarea class="form-control" id="email-addresses" rows="3" 
                                              placeholder="admin@example.com, ops@example.com"></textarea>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="webhook-notifications">
                                    <label class="form-check-label" for="webhook-notifications">
                                        <i class="fas fa-link me-1"></i>Webhook
                                    </label>
                                </div>
                                <div class="mb-3 mt-2">
                                    <label class="form-label">URL Webhook</label>
                                    <input type="url" class="form-control" id="webhook-url" 
                                           placeholder="https://hooks.slack.com/...">
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <h6>Fréquence des Notifications</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Délai Minimum entre Alertes (min)</label>
                                    <input type="number" class="form-control" id="min-alert-interval" 
                                           value="15" min="1" max="1440">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="form-check form-switch mt-4">
                                    <input class="form-check-input" type="checkbox" id="escalation-enabled">
                                    <label class="form-check-label" for="escalation-enabled">
                                        Escalade Automatique
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Délai d'Escalade (h)</label>
                                    <input type="number" class="form-control" id="escalation-delay" 
                                           value="2" min="1" max="24">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderRetentionTab() {
        return `
            <div class="tab-pane fade" id="retention" role="tabpanel">
                <h6><i class="fas fa-database text-success me-2"></i>Politique de Rétention</h6>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Alertes</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Conserver les alertes résolues (jours)</label>
                                    <input type="number" class="form-control" id="resolved-alerts-retention" 
                                           value="30" min="1" max="365">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Conserver les alertes acquittées (jours)</label>
                                    <input type="number" class="form-control" id="acknowledged-alerts-retention" 
                                           value="7" min="1" max="90">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Logs NTP</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Conserver les logs détaillés (jours)</label>
                                    <input type="number" class="form-control" id="detailed-logs-retention" 
                                           value="7" min="1" max="30">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Conserver les logs agrégés (jours)</label>
                                    <input type="number" class="form-control" id="aggregated-logs-retention" 
                                           value="90" min="7" max="365">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Note:</strong> La suppression automatique s'effectue quotidiennement à 2h00 du matin.
                        Les données supprimées ne peuvent pas être récupérées.
                    </div>
                </div>
            </div>
        `;
    }
    
    renderAdvancedTab() {
        return `
            <div class="tab-pane fade" id="advanced" role="tabpanel">
                <h6><i class="fas fa-cogs text-secondary me-2"></i>Paramètres Avancés</h6>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Surveillance</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Intervalle de Vérification (s)</label>
                                    <input type="number" class="form-control" id="check-interval" 
                                           value="60" min="30" max="3600">
                                    <small class="text-muted">Fréquence des contrôles automatiques</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Timeout Requêtes NTP (s)</label>
                                    <input type="number" class="form-control" id="ntp-timeout" 
                                           value="10" min="1" max="60">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Sécurité & Audit</h6>
                            </div>
                            <div class="card-body">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="debug-mode">
                                    <label class="form-check-label" for="debug-mode">
                                        Mode Debug
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="require-auth-alerts" checked>
                                    <label class="form-check-label" for="require-auth-alerts">
                                        Authentification Requise pour les Alertes
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="audit-log" checked>
                                    <label class="form-check-label" for="audit-log">
                                        Log d'Audit
                                    </label>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Niveau de Log</label>
                                    <select class="form-select" id="log-level">
                                        <option value="DEBUG">DEBUG</option>
                                        <option value="INFO" selected>INFO</option>
                                        <option value="WARNING">WARNING</option>
                                        <option value="ERROR">ERROR</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderConfigFields(configs) {
        return configs.map(config => {
            const fieldId = `config-${config.key.replace(/\./g, '-')}`;
            const isReadOnly = !this.currentCategory.can_modify;
            
            return `
                <div class="config-field-group" data-key="${config.key}">
                    <label for="${fieldId}" class="form-label">
                        ${this.getConfigDisplayName(config.key)}
                        ${config.value_type === 'bool' ? '' : '<span class="text-danger">*</span>'}
                    </label>
                    
                    ${this.renderFieldInput(config, fieldId, isReadOnly)}
                    
                    ${config.description ? `
                        <div class="form-text">${config.description}</div>
                    ` : ''}
                    
                    <div class="field-validation-error" id="${fieldId}-error"></div>
                </div>
            `;
        }).join('');
    }
    
    renderFieldInput(config, fieldId, isReadOnly) {
        const commonAttrs = `
            id="${fieldId}"
            data-key="${config.key}"
            data-type="${config.value_type}"
            ${isReadOnly ? 'readonly disabled' : ''}
            class="form-control ${config.value_type === 'bool' ? 'form-check-input' : ''}"
        `;
        
        switch (config.value_type) {
            case 'bool':
                return `
                    <div class="form-check form-switch">
                        <input type="checkbox" ${commonAttrs} 
                               ${config.value ? 'checked' : ''}>
                        <label class="form-check-label" for="${fieldId}">
                            ${config.value ? 'Activé' : 'Désactivé'}
                        </label>
                    </div>
                `;
                
            case 'int':
                return `
                    <input type="number" ${commonAttrs} 
                           value="${config.value || 0}"
                           step="1">
                `;
                
            case 'float':
                return `
                    <input type="number" ${commonAttrs} 
                           value="${config.value || 0}"
                           step="0.1">
                `;
                
            case 'json':
                return `
                    <textarea ${commonAttrs} rows="4">${JSON.stringify(config.value, null, 2)}</textarea>
                `;
                
            default: // string
                return `
                    <input type="text" ${commonAttrs} 
                           value="${config.value || ''}"
                           placeholder="Entrez une valeur...">
                `;
        }
    }
    
    // ================== GESTION DES ÉVÉNEMENTS ==================
    
    setupEventListeners() {
        // Clic sur les catégories
        document.addEventListener('click', (e) => {
            const categoryItem = e.target.closest('.category-item');
            if (categoryItem) {
                const category = categoryItem.dataset.category;
                this.loadCategory(category);
            }
        });
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveCategory();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.resetCategory();
                        break;
                }
            }
        });
        
        // Avant fermeture de page
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty) {
                e.preventDefault();
                e.returnValue = 'Vous avez des modifications non sauvegardées.';
            }
        });
    }
    
    attachFieldEvents() {
        const fields = document.querySelectorAll('#config-content input, #config-content textarea, #config-content select');
        fields.forEach(field => {
            field.addEventListener('input', () => this.handleFieldChange(field));
            field.addEventListener('change', () => this.handleFieldChange(field));
        });
    }
    
    handleFieldChange(field) {
        this.validateField(field);
        this.markDirty();
        
        // Auto-save avec délai
        if (this.changeTimeout) {
            clearTimeout(this.changeTimeout);
        }
        this.changeTimeout = setTimeout(() => {
            this.autoSave();
        }, 3000); // 3 secondes
    }
    
    // ================== VALIDATION ==================
    
    setupValidation() {
        this.validationRules = {
            'ntp.query_interval': { min: 10, max: 3600, type: 'int' },
            'ntp.default_timeout': { min: 1, max: 60, type: 'int' },
            'ntp.max_offset_warning': { min: 0.1, max: 60.0, type: 'float' },
            'ntp.max_offset_critical': { min: 0.5, max: 300.0, type: 'float' },
            'alerts.email_enabled': { type: 'bool' },
            'alerts.webhook_enabled': { type: 'bool' },
            'alerts.retention_days': { min: 1, max: 365, type: 'int' },
            'monitoring.log_level': { 
                type: 'string', 
                options: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] 
            }
        };
    }
    
    setupAutoSave() {
        // Configuration de l'auto-save
        this.autoSaveEnabled = true;
        this.autoSaveDelay = 3000; // 3 secondes
        
        console.log('🔧 Auto-save configuré pour les changements de configuration');
    }
    
    validateField(field) {
        const key = field.dataset.key;
        const type = field.dataset.type;
        const value = this.getFieldValue(field);
        
        let isValid = true;
        let errorMessage = '';
        
        // Validation de type
        if (type === 'int') {
            if (!Number.isInteger(Number(value))) {
                isValid = false;
                errorMessage = 'Doit être un nombre entier';
            }
        } else if (type === 'float') {
            if (isNaN(Number(value))) {
                isValid = false;
                errorMessage = 'Doit être un nombre décimal';
            }
        } else if (type === 'json') {
            try {
                JSON.parse(value);
            } catch (e) {
                isValid = false;
                errorMessage = 'JSON invalide';
            }
        }
        
        // Validation de règles spécifiques
        if (isValid && this.validationRules[key]) {
            const rule = this.validationRules[key];
            const numValue = Number(value);
            
            if (rule.min !== undefined && numValue < rule.min) {
                isValid = false;
                errorMessage = rule.message;
            } else if (rule.max !== undefined && numValue > rule.max) {
                isValid = false;
                errorMessage = rule.message;
            }
        }
        
        if (isValid) {
            this.clearValidationError(field);
        } else {
            this.showValidationError(field, errorMessage);
        }
        
        return isValid;
    }
    
    validateAllFields() {
        const fields = document.querySelectorAll('#config-content input, #config-content textarea');
        let allValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                allValid = false;
            }
        });
        
        return allValid;
    }
    
    showValidationError(field, message) {
        const errorElement = document.getElementById(`${field.id}-error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        
        field.classList.add('is-invalid');
        this.validationErrors[field.dataset.key] = message;
    }
    
    clearValidationError(field) {
        const errorElement = document.getElementById(`${field.id}-error`);
        if (errorElement) {
            errorElement.style.display = 'none';
        }
        
        field.classList.remove('is-invalid');
        delete this.validationErrors[field.dataset.key];
    }
    
    // ================== SAUVEGARDE ==================
    
    async saveCategory() {
        if (!this.validateAllFields()) {
            this.showNotification('Veuillez corriger les erreurs avant de sauvegarder', 'error');
            return false;
        }
        
        try {
            const configData = this.collectConfigData();
            
            this.showLoadingSpinner(true);
            
            const response = await fetch('/api/config/bulk-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    configs: configData
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isDirty = false;
                this.showNotification('Configuration sauvegardée avec succès', 'success');
                
                // Recharger pour obtenir les dernières données
                await this.loadCategory(this.currentCategory.category);
                
                return true;
            } else {
                throw new Error(result.message || 'Erreur lors de la sauvegarde');
            }
            
        } catch (error) {
            console.error('Erreur sauvegarde:', error);
            this.showNotification(`Erreur de sauvegarde: ${error.message}`, 'error');
            return false;
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    async autoSave() {
        if (!this.isDirty || Object.keys(this.validationErrors).length > 0) {
            return;
        }
        
        const saved = await this.saveCategory();
        if (saved) {
            this.showNotification('Auto-sauvegarde effectuée', 'info', 2000);
        }
    }
    
    collectConfigData() {
        const fields = document.querySelectorAll('#config-content input, #config-content textarea');
        const configData = [];
        
        fields.forEach(field => {
            if (field.dataset.key) {
                configData.push({
                    key: field.dataset.key,
                    value: this.getFieldValue(field),
                    value_type: field.dataset.type
                });
            }
        });
        
        return configData;
    }
    
    getFieldValue(field) {
        if (field.type === 'checkbox') {
            return field.checked;
        } else if (field.dataset.type === 'int') {
            return parseInt(field.value) || 0;
        } else if (field.dataset.type === 'float') {
            return parseFloat(field.value) || 0.0;
        } else if (field.dataset.type === 'json') {
            try {
                return JSON.parse(field.value);
            } catch (e) {
                return field.value; // Retourner la chaîne en cas d'erreur
            }
        } else {
            return field.value;
        }
    }
    
    // ================== ACTIONS ==================
    
    async resetCategory() {
        if (!this.currentCategory || !this.currentCategory.category) {
            this.showNotification('Aucune catégorie sélectionnée', 'warning');
            return;
        }
        
        if (!await this.confirmAction('Êtes-vous sûr de vouloir réinitialiser cette catégorie ?')) {
            return;
        }
        
        await this.loadCategory(this.currentCategory.category);
        this.showNotification('Configuration réinitialisée', 'info');
    }
    
    async testConfiguration() {
        if (this.currentCategory.category === 'alerts') {
            await this.testAlertsConfiguration();
        } else if (this.currentCategory.category === 'ntp') {
            await this.testNTPConfiguration();
        } else {
            this.showNotification('Test non disponible pour cette catégorie', 'warning');
        }
    }
    
    async testAlertsConfiguration() {
        try {
            const response = await fetch('/api/config/alerts/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'email' // ou 'webhook'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Test réussi: ${result.message}`, 'success');
            } else {
                this.showNotification(`Test échoué: ${result.message}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de test: ${error.message}`, 'error');
        }
    }
    
    async testNTPConfiguration() {
        this.showNotification('Test de configuration NTP en cours...', 'info');
        
        try {
            const response = await fetch('/api/ntp/test-all', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                const successCount = result.results.filter(r => r.success).length;
                this.showNotification(
                    `Test terminé: ${successCount}/${result.results.length} serveurs OK`, 
                    'success'
                );
            } else {
                this.showNotification('Erreur lors du test NTP', 'error');
            }
            
        } catch (error) {
            this.showNotification(`Erreur de test: ${error.message}`, 'error');
        }
    }
    
    // ================== UTILITAIRES ==================
    
    markDirty() {
        this.isDirty = true;
        this.updateSaveButton();
    }
    
    updateSaveButton() {
        const saveButton = document.querySelector('.config-actions .btn-success');
        if (saveButton) {
            if (this.isDirty) {
                saveButton.innerHTML = '<i class="fas fa-save"></i> Sauvegarder *';
                saveButton.classList.add('pulse');
            } else {
                saveButton.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
                saveButton.classList.remove('pulse');
            }
        }
    }
    
    updateCategoriesMenu(activeCategory) {
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-category="${activeCategory}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
    
    getConfigDisplayName(key) {
        const displayNames = {
            'ntp.query_interval': 'Intervalle de requête (sec)',
            'ntp.default_timeout': 'Timeout par défaut (sec)',
            'ntp.max_offset_warning': 'Seuil d\'alerte (sec)',
            'ntp.max_offset_critical': 'Seuil critique (sec)',
            'ntp.retry_attempts': 'Tentatives de reconnexion',
            'ntp.enable_monitoring': 'Activer le monitoring',
            'alerts.retention_days': 'Rétention des alertes (jours)',
            'alerts.email_enabled': 'Notifications par email',
            'alerts.webhook_enabled': 'Webhooks activés',
            'system.timezone': 'Fuseau horaire',
            'monitoring.log_retention_days': 'Rétention des logs (jours)'
        };
        
        return displayNames[key] || key.split('.').pop().replace(/_/g, ' ');
    }
    
    async confirmUnsavedChanges() {
        return await this.confirmAction(
            'Vous avez des modifications non sauvegardées. Continuer quand même ?'
        );
    }
    
    async confirmAction(message) {
        return new Promise((resolve) => {
            if (window.confirm(message)) {
                resolve(true);
            } else {
                resolve(false);
            }
        });
    }
    
    showLoadingSpinner(show) {
        const spinner = document.getElementById('config-loading-spinner');
        if (spinner) {
            spinner.style.display = show ? 'block' : 'none';
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        if (window.notificationSystem) {
            window.notificationSystem.show(message, type, duration);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
    
    // ================== MÉTHODES SPÉCIFIQUES AUX ALERTES ==================
    
    attachAlertsFieldEvents() {
        // Événements pour les champs de configuration des alertes
        document.querySelectorAll('#thresholds input, #notifications input, #notifications textarea, #retention input, #advanced input, #advanced select').forEach(field => {
            field.addEventListener('input', () => {
                this.markDirty();
                this.validateAlertsField(field);
            });
            
            field.addEventListener('change', () => {
                this.markDirty();
                this.validateAlertsField(field);
            });
            
            // Validation en temps réel avec délai
            field.addEventListener('blur', () => {
                this.validateAlertsField(field);
            });
        });
        
        // Gestion des switches
        document.querySelectorAll('.form-check-input').forEach(switchInput => {
            switchInput.addEventListener('change', (e) => {
                const label = document.querySelector(`label[for="${e.target.id}"]`);
                if (label && e.target.type === 'checkbox') {
                    // Mettre à jour le texte pour les switches
                    const textSpan = label.querySelector('.switch-text');
                    if (textSpan) {
                        textSpan.textContent = e.target.checked ? 'Activé' : 'Désactivé';
                    }
                }
                this.markDirty();
            });
        });
        
        // Raccourcis clavier pour la configuration des alertes
        document.addEventListener('keydown', (e) => {
            // Seulement si le modal de configuration est ouvert
            if (document.getElementById('configModal') && document.getElementById('configModal').classList.contains('show')) {
                switch(e.key) {
                    case 's': // Sauvegarder
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            this.saveAlertsConfig();
                        }
                        break;
                    case 'r': // Réinitialiser
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            this.resetAlertsConfig();
                        }
                        break;
                    case 't': // Tester
                        if (e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            this.testAlertsConfig();
                        }
                        break;
                    case 'Escape': // Effacer les erreurs
                        if (!e.ctrlKey && !e.metaKey) {
                            document.querySelectorAll('.field-validation-error').forEach(error => {
                                error.style.display = 'none';
                            });
                            document.querySelectorAll('.is-invalid').forEach(field => {
                                field.classList.remove('is-invalid');
                            });
                        }
                        break;
                }
            }
        });
        
        // Navigation par onglets avec clavier
        document.addEventListener('keydown', (e) => {
            if (document.getElementById('configModal') && document.getElementById('configModal').classList.contains('show')) {
                if (e.altKey) {
                    switch(e.key) {
                        case '1': // Onglet Seuils
                            e.preventDefault();
                            document.getElementById('thresholds-tab').click();
                            break;
                        case '2': // Onglet Notifications
                            e.preventDefault();
                            document.getElementById('notifications-tab').click();
                            break;
                        case '3': // Onglet Rétention
                            e.preventDefault();
                            document.getElementById('retention-tab').click();
                            break;
                        case '4': // Onglet Avancé
                            e.preventDefault();
                            document.getElementById('advanced-tab').click();
                            break;
                    }
                }
            }
        });
    }
    
    async loadAlertsConfigData() {
        try {
            const response = await fetch('/api/config/alerts');
            if (!response.ok) throw new Error('Erreur chargement configuration alertes');
            
            const data = await response.json();
            if (data.success) {
                this.populateAlertsForm(data.config);
            }
            
        } catch (error) {
            console.error('Erreur chargement configuration alertes:', error);
            this.showNotification('Erreur de chargement de la configuration des alertes', 'warning');
        }
    }
    
    populateAlertsForm(config) {
        // Seuils
        this.setFieldValue('offset-warning-threshold', config.offset_warning_threshold || 100);
        this.setFieldValue('offset-critical-threshold', config.offset_critical_threshold || 1000);
        this.setFieldValue('latency-warning-threshold', config.latency_warning_threshold || 500);
        this.setFieldValue('latency-critical-threshold', config.latency_critical_threshold || 2000);
        this.setFieldValue('stratum-max-threshold', config.stratum_max_threshold || 3);
        this.setFieldValue('connection-timeout', config.connection_timeout || 30);
        this.setFieldValue('max-consecutive-failures', config.max_consecutive_failures || 3);
        
        // Notifications
        this.setCheckboxValue('email-notifications', config.email_notifications !== false);
        this.setFieldValue('email-addresses', config.email_addresses || '');
        this.setCheckboxValue('webhook-notifications', config.webhook_notifications || false);
        this.setFieldValue('webhook-url', config.webhook_url || '');
        this.setFieldValue('min-alert-interval', config.min_alert_interval || 15);
        this.setCheckboxValue('escalation-enabled', config.escalation_enabled || false);
        this.setFieldValue('escalation-delay', config.escalation_delay || 2);
        
        // Rétention
        this.setFieldValue('resolved-alerts-retention', config.resolved_alerts_retention || 30);
        this.setFieldValue('acknowledged-alerts-retention', config.acknowledged_alerts_retention || 7);
        this.setFieldValue('detailed-logs-retention', config.detailed_logs_retention || 7);
        this.setFieldValue('aggregated-logs-retention', config.aggregated_logs_retention || 90);
        
        // Avancé
        this.setFieldValue('check-interval', config.check_interval || 60);
        this.setFieldValue('ntp-timeout', config.ntp_timeout || 10);
        this.setCheckboxValue('debug-mode', config.debug_mode || false);
        this.setCheckboxValue('require-auth-alerts', config.require_auth_alerts !== false);
        this.setCheckboxValue('audit-log', config.audit_log !== false);
        this.setFieldValue('log-level', config.log_level || 'INFO');
    }
    
    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
        }
    }
    
    setCheckboxValue(fieldId, checked) {
        const field = document.getElementById(fieldId);
        if (field && field.type === 'checkbox') {
            field.checked = checked;
        }
    }
    
    async saveAlertsConfig() {
        try {
            // Validation des champs
            if (!this.validateAllAlertsFields()) {
                this.showNotification('Veuillez corriger les erreurs avant de sauvegarder', 'error');
                return;
            }
            
            const config = this.gatherAlertsConfigData();
            
            const response = await fetch('/api/config/alerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Configuration des alertes sauvegardée', 'success');
                this.isDirty = false;
                this.updateSaveButton();
            } else {
                throw new Error(result.error || 'Erreur de sauvegarde');
            }
            
        } catch (error) {
            console.error('Erreur sauvegarde configuration alertes:', error);
            this.showNotification(`Erreur de sauvegarde: ${error.message}`, 'error');
        }
    }
    
    gatherAlertsConfigData() {
        return {
            // Seuils
            offset_warning_threshold: parseInt(document.getElementById('offset-warning-threshold').value),
            offset_critical_threshold: parseInt(document.getElementById('offset-critical-threshold').value),
            latency_warning_threshold: parseInt(document.getElementById('latency-warning-threshold').value),
            latency_critical_threshold: parseInt(document.getElementById('latency-critical-threshold').value),
            stratum_max_threshold: parseInt(document.getElementById('stratum-max-threshold').value),
            connection_timeout: parseInt(document.getElementById('connection-timeout').value),
            max_consecutive_failures: parseInt(document.getElementById('max-consecutive-failures').value),
            
            // Notifications
            email_notifications: document.getElementById('email-notifications').checked,
            email_addresses: document.getElementById('email-addresses').value,
            webhook_notifications: document.getElementById('webhook-notifications').checked,
            webhook_url: document.getElementById('webhook-url').value,
            min_alert_interval: parseInt(document.getElementById('min-alert-interval').value),
            escalation_enabled: document.getElementById('escalation-enabled').checked,
            escalation_delay: parseInt(document.getElementById('escalation-delay').value),
            
            // Rétention
            resolved_alerts_retention: parseInt(document.getElementById('resolved-alerts-retention').value),
            acknowledged_alerts_retention: parseInt(document.getElementById('acknowledged-alerts-retention').value),
            detailed_logs_retention: parseInt(document.getElementById('detailed-logs-retention').value),
            aggregated_logs_retention: parseInt(document.getElementById('aggregated-logs-retention').value),
            
            // Avancé
            check_interval: parseInt(document.getElementById('check-interval').value),
            ntp_timeout: parseInt(document.getElementById('ntp-timeout').value),
            debug_mode: document.getElementById('debug-mode').checked,
            require_auth_alerts: document.getElementById('require-auth-alerts').checked,
            audit_log: document.getElementById('audit-log').checked,
            log_level: document.getElementById('log-level').value
        };
    }
    
    async resetAlertsConfig() {
        if (await this.confirmAction('Êtes-vous sûr de vouloir réinitialiser la configuration des alertes ?')) {
            this.populateAlertsForm({});
            this.showNotification('Configuration des alertes réinitialisée', 'info');
            this.markDirty();
        }
    }
    
    async testAlertsConfig() {
        try {
            const config = this.gatherAlertsConfigData();
            
            const response = await fetch('/api/config/alerts/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Test de configuration réussi', 'success');
                this.showTestResults(result.results);
            } else {
                this.showNotification(`Test échoué: ${result.message}`, 'error');
                this.showTestResults(result.results);
            }
            
        } catch (error) {
            console.error('Erreur test configuration alertes:', error);
            this.showNotification(`Erreur de test: ${error.message}`, 'error');
        }
    }
    
    showTestResults(results) {
        if (!results) return;
        
        let message = 'Résultats des tests:\n\n';
        
        Object.entries(results).forEach(([testType, result]) => {
            const status = result.success ? '✅' : '❌';
            message += `${status} ${testType}: ${result.message}\n`;
        });
        
        // Afficher dans une modal ou console pour l'instant
        console.log(message);
    }
    
    validateAlertsField(field) {
        const fieldId = field.id;
        let isValid = true;
        let errorMessage = '';
        
        // Validation selon le type de champ
        switch (fieldId) {
            case 'offset-warning-threshold':
            case 'offset-critical-threshold':
                const value = parseInt(field.value);
                if (isNaN(value) || value < 1 || value > 10000) {
                    isValid = false;
                    errorMessage = 'Valeur doit être entre 1 et 10000 ms';
                }
                break;
                
            case 'latency-warning-threshold':
            case 'latency-critical-threshold':
                const latency = parseInt(field.value);
                if (isNaN(latency) || latency < 1 || latency > 5000) {
                    isValid = false;
                    errorMessage = 'Valeur doit être entre 1 et 5000 ms';
                }
                break;
                
            case 'stratum-max-threshold':
                const stratum = parseInt(field.value);
                if (isNaN(stratum) || stratum < 1 || stratum > 15) {
                    isValid = false;
                    errorMessage = 'Stratum doit être entre 1 et 15';
                }
                break;
                
            case 'connection-timeout':
                const timeout = parseInt(field.value);
                if (isNaN(timeout) || timeout < 5 || timeout > 300) {
                    isValid = false;
                    errorMessage = 'Timeout doit être entre 5 et 300 secondes';
                }
                break;
                
            case 'max-consecutive-failures':
                const failures = parseInt(field.value);
                if (isNaN(failures) || failures < 1 || failures > 10) {
                    isValid = false;
                    errorMessage = 'Nombre d\'échecs doit être entre 1 et 10';
                }
                break;
                
            case 'email-addresses':
                if (field.value && !this.validateEmailAddresses(field.value)) {
                    isValid = false;
                    errorMessage = 'Format d\'adresses email invalide (ex: user@domain.com, user2@domain.com)';
                }
                break;
                
            case 'webhook-url':
                if (field.value && !this.validateURL(field.value)) {
                    isValid = false;
                    errorMessage = 'URL invalide (doit commencer par http:// ou https://)';
                }
                break;
                
            case 'min-alert-interval':
                const interval = parseInt(field.value);
                if (isNaN(interval) || interval < 1 || interval > 1440) {
                    isValid = false;
                    errorMessage = 'Intervalle doit être entre 1 et 1440 minutes';
                }
                break;
                
            case 'escalation-delay':
                const delay = parseInt(field.value);
                if (isNaN(delay) || delay < 1 || delay > 24) {
                    isValid = false;
                    errorMessage = 'Délai d\'escalade doit être entre 1 et 24 heures';
                }
                break;
                
            case 'resolved-alerts-retention':
            case 'acknowledged-alerts-retention':
            case 'detailed-logs-retention':
            case 'aggregated-logs-retention':
                const retention = parseInt(field.value);
                if (isNaN(retention) || retention < 1 || retention > 365) {
                    isValid = false;
                    errorMessage = 'Rétention doit être entre 1 et 365 jours';
                }
                break;
                
            case 'check-interval':
                const checkInterval = parseInt(field.value);
                if (isNaN(checkInterval) || checkInterval < 30 || checkInterval > 3600) {
                    isValid = false;
                    errorMessage = 'Intervalle de vérification doit être entre 30 et 3600 secondes';
                }
                break;
                
            case 'ntp-timeout':
                const ntpTimeout = parseInt(field.value);
                if (isNaN(ntpTimeout) || ntpTimeout < 1 || ntpTimeout > 60) {
                    isValid = false;
                    errorMessage = 'Timeout NTP doit être entre 1 et 60 secondes';
                }
                break;
        }
        
        // Afficher/masquer l'erreur
        const errorElement = document.getElementById(`${fieldId}-error`);
        if (errorElement) {
            if (isValid) {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
                field.classList.remove('is-invalid');
            } else {
                errorElement.textContent = errorMessage;
                errorElement.style.display = 'block';
                field.classList.add('is-invalid');
            }
        }
        
        return isValid;
    }
    
    validateAllAlertsFields() {
        const fields = document.querySelectorAll('#thresholds input, #notifications input, #notifications textarea, #retention input, #advanced input');
        let allValid = true;
        
        fields.forEach(field => {
            if (!this.validateAlertsField(field)) {
                allValid = false;
            }
        });
        
        return allValid;
    }
    
    validateEmailAddresses(emails) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const addresses = emails.split(',').map(email => email.trim());
        
        return addresses.every(email => email === '' || emailRegex.test(email));
    }
    
    validateURL(url) {
        try {
            new URL(url);
            return url.startsWith('http://') || url.startsWith('https://');
        } catch {
            return false;
        }
    }
    
    // Méthode pour ouvrir directement la configuration des alertes
    openAlertsConfig() {
        this.loadCategory('alerts');
    }
}

// Initialisation globale
let configManager;

// Fonction d'initialisation du ConfigManager
function initConfigManager() {
    if (!configManager && document.getElementById('config-categories-menu')) {
        console.log('🔧 Initialisation du ConfigManager');
        configManager = new ConfigManager();
        window.configManager = configManager;
    }
}

// Initialisation au chargement du DOM (pour les cas où le modal est déjà présent)
document.addEventListener('DOMContentLoaded', () => {
    initConfigManager();
});

// Initialisation quand le modal de configuration s'ouvre
document.addEventListener('shown.bs.modal', (event) => {
    if (event.target.id === 'configModal') {
        console.log('🔧 Modal de configuration ouvert, initialisation du ConfigManager');
        setTimeout(() => {
            initConfigManager();
        }, 100);
    }
});

// Export pour utilisation externe
window.ConfigManager = ConfigManager; 