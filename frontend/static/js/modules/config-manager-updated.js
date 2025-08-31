/**
 * Configuration Manager - VERSION MISE À JOUR
 * Gestion avancée de la configuration système avec nouvelle API des seuils
 * NTP Monitor Enterprise
 */

class ConfigManagerUpdated {
    constructor() {
        this.categories = {};
        this.currentCategory = null;
        this.isDirty = false;
        this.changeTimeout = null;
        this.validationErrors = {};
        this.thresholds = {};  // Nouveau: stockage des seuils
        this.serverTypes = []; // Référentiel types serveurs pour l'onglet Seuils
        
        this.init();
    }
    
    async init() {
        await this.loadCategories();
        await this.loadThresholds();
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
            
            const data = await response.json();
            
            // Gérer le nouveau format de réponse API
            if (data.success && data.data) {
                this.categories = data.data;
                try {
                    const apiList = Object.entries(this.categories || {}).map(([key, cat]) => ({
                        key,
                        name: cat.name,
                        display_name: cat.display_name,
                        count: cat.count,
                        public_count: cat.public_count
                    }));
                    console.log('📥 Catégories reçues (API):', apiList);
                    if (console.table) console.table(apiList);
                } catch (e) { /* noop */ }
            } else {
                // Fallback pour l'ancien format
                this.categories = data;
                try { console.log('📥 Catégories (format ancien):', this.categories); } catch (e) { /* noop */ }
            }
            
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
    
    async loadThresholds() {
        // Charger les seuils depuis l'API - Pas de valeurs en dur
        try {
            console.log('🔄 Chargement des seuils depuis l\'API...');
            this.thresholds = await this.getThresholdsFromAPI();
            
            if (Object.keys(this.thresholds).length === 0) {
                console.warn('⚠️ Aucun seuil récupéré depuis l\'API');
                this.showNotification('Aucun seuil configuré trouvé', 'warning');
            } else {
                console.log(`✅ ${Object.keys(this.thresholds).length} métriques chargées`);
                this.showNotification('Seuils chargés avec succès', 'success');
            }
            
        } catch (error) {
            console.error('❌ Erreur lors du chargement des seuils:', error);
            this.showNotification(`Erreur chargement seuils: ${error.message}`, 'error');
            this.thresholds = {};
        }
    }
    
    organizeThresholds(thresholdsData) {
        // Organiser les seuils par métrique et type de serveur
        const organized = {};
        
        thresholdsData.forEach(threshold => {
            if (!organized[threshold.metric_name]) {
                organized[threshold.metric_name] = {};
            }
            organized[threshold.metric_name][threshold.server_type] = threshold;
        });
        
        return organized;
    }
    
    async getThresholdsFromAPI() {
        // Récupérer les seuils depuis l'API - Pas de valeurs en dur
        try {
            const response = await fetch('/api/alerts/thresholds');
            if (!response.ok) {
                throw new Error(`Erreur API: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Erreur lors de la récupération des seuils');
            }
            
            return this.organizeThresholds(data.thresholds);
            
        } catch (error) {
            console.error('Erreur récupération seuils depuis API:', error);
            // Retourner un objet vide plutôt que des valeurs en dur
            return {};
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
            // Conserver directement l'objet catégorie (pas l'enveloppe)
            this.currentCategory = categoryData.data || categoryData;
            
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
        
        try {
            const rendered = Object.entries(this.categories || {}).map(([key, category]) => ({
                key,
                display_name: category.display_name
            }));
            console.log(`🧭 Rendu menu latéral: ${rendered.length} éléments`, rendered.map(r => r.display_name || r.key));
            if (console.table) console.table(rendered);
        } catch (e) { /* noop */ }

        // Construction DOM pour garantir l'affichage correct des accents (textContent + décodage entités)
        menuContainer.innerHTML = '';
        Object.entries(this.categories || {}).forEach(([key, category]) => {
            const item = document.createElement('div');
            item.className = 'category-item';
            item.dataset.category = key;

            const header = document.createElement('div');
            header.className = 'category-header';

            const iconEl = document.createElement('i');
            iconEl.className = `${category.icon || 'fas fa-cog'} me-2`;

            const nameSpan = document.createElement('span');
            nameSpan.className = 'category-name';
            nameSpan.textContent = this.decodeHtmlEntities(category.display_name || key); // accents préservés

            header.appendChild(iconEl);
            header.appendChild(nameSpan);
            item.appendChild(header);
            menuContainer.appendChild(item);
        });
    }

    // Décoder les entités HTML en texte (ex: &eacute; -> é)
    decodeHtmlEntities(str) {
        try {
            if (typeof str !== 'string') return str;
            const txt = document.createElement('textarea');
            txt.innerHTML = str;
            return txt.value;
        } catch (e) {
            return str;
        }
    }
    
    updateCategoriesMenu(selectedCategory) {
        // Mettre à jour l'état visuel du menu des catégories
        const categoryItems = document.querySelectorAll('.category-item');
        
        categoryItems.forEach(item => {
            const category = item.dataset.category;
            if (category === selectedCategory) {
                item.classList.add('active');
                item.classList.add('selected');
            } else {
                item.classList.remove('active');
                item.classList.remove('selected');
            }
        });
        
        // Mettre à jour le titre de la catégorie sélectionnée
        const categoryTitle = document.getElementById('config-category-title');
        if (categoryTitle && this.categories[selectedCategory]) {
            categoryTitle.textContent = this.categories[selectedCategory].display_name;
        }
    }
    
    renderCategoryConfig(categoryData) {
        const configContainer = document.getElementById('config-content');
        if (!configContainer) return;
        
        // Gestion du nouveau format de réponse API
        const actualData = categoryData.data || categoryData;
        
        // Gestion spéciale pour la catégorie alertes
        if (actualData.category === 'alerts') {
            this.renderAlertsConfig(actualData);
            return;
        }
        
        const configHTML = `
            <div class="config-category-header">
                <h3>
                    <i class="${this.categories[actualData.category]?.icon || 'fas fa-cog'}"></i>
                    ${actualData.display_name}
                </h3>
                <p class="text-muted">${actualData.description}</p>
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
                ${this.renderConfigFields(actualData.configs || [])}
            </div>
            
            <div class="config-footer">
                <small class="text-muted">
                    <i class="fas fa-clock"></i>
                    Dernière modification: ${actualData.last_updated ? 
                        new Date(actualData.last_updated).toLocaleString() : 'Jamais'}
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
                <p class="text-muted">Seuils, notifications, rétention et options avancées</p>
                <div class="config-actions">
                    <button class="btn btn-success btn-sm" onclick="configManager.saveUnifiedAlertsConfig()">
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
            
            <div class="config-form">
                <ul class="nav nav-tabs" id="alertsConfigTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <a class="nav-link active" id="unified-thresholds-tab" data-bs-toggle="tab"
                           href="#unified-thresholds" role="tab">
                            <i class="fas fa-chart-line me-1"></i>Seuils d'Alerte
                        </a>
                    </li>
                    <li class="nav-item" role="presentation">
                        <a class="nav-link" id="notifications-tab" data-bs-toggle="tab"
                           href="#notifications" role="tab">
                            <i class="fas fa-bell me-1"></i>Notifications
                        </a>
                    </li>
                    <li class="nav-item" role="presentation">
                        <a class="nav-link" id="retention-tab" data-bs-toggle="tab"
                           href="#retention" role="tab">
                            <i class="fas fa-archive me-1"></i>Rétention
                        </a>
                    </li>
                    <li class="nav-item" role="presentation">
                        <a class="nav-link" id="advanced-tab" data-bs-toggle="tab"
                           href="#advanced" role="tab">
                            <i class="fas fa-cogs me-1"></i>Avancé
                        </a>
                    </li>
                </ul>
                
                <div class="tab-content mt-3" id="alertsConfigTabContent">
                    ${this.renderUnifiedThresholdsTab()}
                    ${this.renderNotificationsTab()}
                    ${this.renderRetentionTab()}
                    ${this.renderAdvancedTab()}
                </div>
            </div>
        `;
        
        configContainer.innerHTML = configHTML;
        this.attachUnifiedAlertsFieldEvents();
        (async () => {
            try {
                await this.loadAndPopulateServerTypes();
                await this.populateUnifiedThresholdsForm();
            } catch (e) {
                console.error('Erreur préparation onglet Seuils:', e);
            }
        })();
        this.populateAllTabs();
    }
    
    renderUnifiedThresholdsTab() {
        return `
            <div class="tab-pane fade show active" id="unified-thresholds" role="tabpanel">
                <h6><i class="fas fa-exclamation-triangle text-warning me-2"></i>Configuration des Alertes NTP</h6>
                <p class="text-muted mb-3">Configurez les seuils d'alerte par type de serveur</p>
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-server me-2"></i>Type de Serveur</label>
                    <select class="form-select" id="server-type-selector"></select>
                    <small class="text-muted">Par défaut: Serveurs locaux (fallback Tous)</small>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0"><i class="fas fa-clock text-primary me-2"></i>Écart de Synchronisation (offset)</h6>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="use-threshold-conditions" checked>
                                    <label class="form-check-label" for="use-threshold-conditions"><small>Activer</small></label>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Seuil Avertissement (ms)</label>
                                    <input type="number" class="form-control" id="offset-warning-threshold" placeholder="">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Seuil Critique (ms)</label>
                                    <input type="number" class="form-control" id="offset-critical-threshold" placeholder="">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0"><i class="fas fa-tachometer-alt text-info me-2"></i>Latence (latency)</h6>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="use-latency-conditions" checked>
                                    <label class="form-check-label" for="use-latency-conditions"><small>Activer</small></label>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Seuil Avertissement (ms)</label>
                                    <input type="number" class="form-control" id="latency-warning-threshold" placeholder="">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Seuil Critique (ms)</label>
                                    <input type="number" class="form-control" id="latency-critical-threshold" placeholder="">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0"><i class="fas fa-layer-group text-success me-2"></i>Précision (stratum)</h6>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="use-stratum-conditions" checked>
                                    <label class="form-check-label" for="use-stratum-conditions"><small>Activer</small></label>
                                </div>
                            </div>
                            <div class="card-body">
                                <label class="form-label">Stratum maximum</label>
                                <select class="form-select" id="stratum-max-threshold">
                                    ${Array.from({length:16}, (_,i)=>`<option value="${i+1}">${i+1}</option>`).join('')}
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0"><i class="fas fa-percentage text-warning me-2"></i>Disponibilité (availability)</h6>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="use-availability-conditions" checked>
                                    <label class="form-check-label" for="use-availability-conditions"><small>Activer</small></label>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Seuil Avertissement (%)</label>
                                    <input type="number" class="form-control" id="availability-warning-threshold" min="0" max="100">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Seuil Critique (%)</label>
                                    <input type="number" class="form-control" id="availability-critical-threshold" min="0" max="100">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="d-flex justify-content-end">
                    <button type="button" class="btn btn-success" id="save-thresholds-unified-btn">
                        <i class="fas fa-save me-2"></i>Enregistrer les seuils
                    </button>
                </div>
            </div>
        `;
    }
    
    renderNotificationsTab() {
        return `
            <div class="tab-pane fade" id="notifications" role="tabpanel">
                <h6><i class="fas fa-bell text-info me-2"></i>Configuration des Notifications</h6>
                <p class="text-muted mb-3">Paramètres pour les notifications d'alertes</p>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Notifications par Email</h6>
                            </div>
                            <div class="card-body">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="email-enabled">
                                    <label class="form-check-label" for="email-enabled">
                                        Activer les notifications par email
                                    </label>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Adresses Email</label>
                                    <textarea class="form-control" id="email-addresses" rows="3"
                                              placeholder="admin@example.com, support@example.com"></textarea>
                                    <small class="text-muted">Une adresse par ligne</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Délai Minimum entre Alertes (min)</label>
                                    <input type="number" class="form-control" id="min-alert-interval"
                                           placeholder="15" min="1" max="1440">
                                    <small class="text-muted">Évite le spam d'alertes</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Webhooks</h6>
                            </div>
                            <div class="card-body">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="webhook-enabled">
                                    <label class="form-check-label" for="webhook-enabled">
                                        Activer les webhooks
                                    </label>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">URL Webhook</label>
                                    <input type="url" class="form-control" id="webhook-url"
                                           placeholder="https://hooks.slack.com/services/...">
                                    <small class="text-muted">URL pour recevoir les alertes</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Secret (optionnel)</label>
                                    <input type="password" class="form-control" id="webhook-secret"
                                           placeholder="Secret pour signature">
                                    <small class="text-muted">Secret pour sécuriser les webhooks</small>
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
                <h6><i class="fas fa-archive text-warning me-2"></i>Gestion de la Rétention</h6>
                <p class="text-muted mb-3">Paramètres de conservation des alertes</p>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Alertes</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Conserver les alertes résolues (jours)</label>
                                    <input type="number" class="form-control" id="resolved-alerts-retention"
                                           placeholder="30" min="1" max="365">
                                    <small class="text-muted">Durée de conservation des alertes résolues</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Conserver les alertes acquittées (jours)</label>
                                    <input type="number" class="form-control" id="acknowledged-alerts-retention"
                                           placeholder="7" min="1" max="365">
                                    <small class="text-muted">Durée de conservation des alertes acquittées</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Logs</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Conserver les logs NTP (jours)</label>
                                    <input type="number" class="form-control" id="ntp-logs-retention"
                                           placeholder="30" min="1" max="365">
                                    <small class="text-muted">Durée de conservation des logs de requêtes NTP</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Conserver les logs d'audit (jours)</label>
                                    <input type="number" class="form-control" id="audit-logs-retention"
                                           placeholder="90" min="1" max="365">
                                    <small class="text-muted">Durée de conservation des logs d'audit</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderAdvancedTab() {
        return `
            <div class="tab-pane fade" id="advanced" role="tabpanel">
                <h6><i class="fas fa-cogs text-secondary me-2"></i>Paramètres Avancés</h6>
                <p class="text-muted mb-3">Configuration avancée du système d'alertes</p>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Sécurité</h6>
                            </div>
                            <div class="card-body">
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="require-auth-alerts" checked>
                                    <label class="form-check-label" for="require-auth-alerts">
                                        Authentification Requise pour les Alertes
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="encrypt-alerts">
                                    <label class="form-check-label" for="encrypt-alerts">
                                        Chiffrer les Données Sensibles
                                    </label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="log-alert-access">
                                    <label class="form-check-label" for="log-alert-access">
                                        Logger l'Accès aux Alertes
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Performance</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Intervalle de Vérification (secondes)</label>
                                    <input type="number" class="form-control" id="check-interval"
                                           placeholder="60" min="10" max="3600">
                                    <small class="text-muted">Fréquence de vérification des seuils</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Timeout des Requêtes (secondes)</label>
                                    <input type="number" class="form-control" id="request-timeout"
                                           placeholder="10" min="1" max="60">
                                    <small class="text-muted">Timeout pour les requêtes NTP</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ================== MÉTHODES SPÉCIFIQUES AUX SEUILS ==================
    
    populateThresholdsForm() {
        // Remplir le formulaire avec les seuils actuels depuis l'API
        const selectedServerType = document.querySelector('input[name="server-type"]:checked')?.value || 'all';
        
        console.log(`🔄 Remplissage formulaire pour type serveur: ${selectedServerType}`);
        console.log('📊 Seuils disponibles:', this.thresholds);
        
        // Récupérer les seuils pour le type de serveur sélectionné
        const offsetThresholds = this.thresholds.offset?.[selectedServerType] || this.thresholds.offset?.all;
        const latencyThresholds = this.thresholds.latency?.[selectedServerType] || this.thresholds.latency?.all;
        const stratumThresholds = this.thresholds.stratum?.[selectedServerType] || this.thresholds.stratum?.all;
        const availabilityThresholds = this.thresholds.availability?.[selectedServerType] || this.thresholds.availability?.all;
        
        // Remplir les champs seulement si les données sont disponibles
        if (offsetThresholds) {
            console.log('✅ Remplissage offset:', offsetThresholds);
            this.setFieldValue('offset-warning-threshold', offsetThresholds.warning_threshold);
            this.setFieldValue('offset-critical-threshold', offsetThresholds.critical_threshold);
        } else {
            console.warn('⚠️ Pas de seuils offset disponibles');
            this.setFieldValue('offset-warning-threshold', '');
            this.setFieldValue('offset-critical-threshold', '');
        }
        
        if (latencyThresholds) {
            console.log('✅ Remplissage latency:', latencyThresholds);
            this.setFieldValue('latency-warning-threshold', latencyThresholds.warning_threshold);
            this.setFieldValue('latency-critical-threshold', latencyThresholds.critical_threshold);
        } else {
            console.warn('⚠️ Pas de seuils latency disponibles');
            this.setFieldValue('latency-warning-threshold', '');
            this.setFieldValue('latency-critical-threshold', '');
        }
        
        if (stratumThresholds) {
            console.log('✅ Remplissage stratum:', stratumThresholds);
            this.setFieldValue('stratum-max-threshold', stratumThresholds.critical_threshold);
        } else {
            console.warn('⚠️ Pas de seuils stratum disponibles');
            this.setFieldValue('stratum-max-threshold', '');
        }
        
        if (availabilityThresholds) {
            console.log('✅ Remplissage availability:', availabilityThresholds);
            this.setFieldValue('availability-warning-threshold', availabilityThresholds.warning_threshold);
            this.setFieldValue('availability-critical-threshold', availabilityThresholds.critical_threshold);
        } else {
            console.warn('⚠️ Pas de seuils availability disponibles');
            this.setFieldValue('availability-warning-threshold', '');
            this.setFieldValue('availability-critical-threshold', '');
        }
    }
    
    async saveThresholds() {
        try {
            console.log('💾 Sauvegarde des seuils...');
            
            // Récupérer le type de serveur sélectionné (code + id)
            const serverTypeSelector = document.getElementById('server-type-selector');
            const selectedCode = serverTypeSelector ? serverTypeSelector.value : null;
            const selectedOption = serverTypeSelector ? serverTypeSelector.selectedOptions[0] : null;
            const selectedId = selectedOption && selectedOption.dataset && selectedOption.dataset.id ? parseInt(selectedOption.dataset.id, 10) : null;
            if (!selectedId || Number.isNaN(selectedId)) {
                throw new Error('Type de serveurs invalide ou non sélectionné');
            }
            console.log(`🎯 Sauvegarde des seuils pour: code=${selectedCode}, id=${selectedId}`);
            
            // Lire et ajuster les valeurs du formulaire selon les règles métier
            const readNum = (id) => {
                const el = document.getElementById(id);
                const raw = el ? parseFloat(el.value) : NaN;
                return Number.isFinite(raw) ? raw : NaN;
            };

            // offset (ms): warning < critical (ajustement si nécessaire)
            let offsetWarn = readNum('offset-warning-threshold');
            let offsetCrit = readNum('offset-critical-threshold');
            if (!Number.isFinite(offsetWarn) || !Number.isFinite(offsetCrit)) {
                throw new Error('Valeurs offset invalides');
            }
            if (!(offsetWarn < offsetCrit)) {
                offsetCrit = offsetWarn + 1;
                const ocEl = document.getElementById('offset-critical-threshold');
                if (ocEl) ocEl.value = String(offsetCrit);
                this.showNotification('Offset: ajustement automatique (warning < critical).', 'info');
            }

            // latency (ms): warning < critical (ajustement si nécessaire)
            let latWarn = readNum('latency-warning-threshold');
            let latCrit = readNum('latency-critical-threshold');
            if (!Number.isFinite(latWarn) || !Number.isFinite(latCrit)) {
                throw new Error('Valeurs latency invalides');
            }
            if (!(latWarn < latCrit)) {
                latCrit = latWarn + 1;
                const lcEl = document.getElementById('latency-critical-threshold');
                if (lcEl) lcEl.value = String(latCrit);
                this.showNotification('Latence: ajustement automatique (warning < critical).', 'info');
            }

            // availability (%): critical < warning, bornage [0,100], ajustement si égalité
            let availWarn = readNum('availability-warning-threshold');
            let availCrit = readNum('availability-critical-threshold');
            if (!Number.isFinite(availWarn) || !Number.isFinite(availCrit)) {
                throw new Error('Valeurs disponibilité invalides');
            }
            availWarn = Math.max(0, Math.min(100, availWarn));
            availCrit = Math.max(0, Math.min(100, availCrit));
            if (Math.abs(availWarn - availCrit) < 1e-9) {
                availCrit = Math.min(100, availCrit + 1);
                availWarn = Math.max(0, availWarn - 1);
            }
            if (!(availCrit < availWarn)) {
                this.showNotification('Disponibilité: le seuil Critique doit être < Avertissement (%).', 'error');
                throw new Error('Pour availability: critical < warning requis');
            }
            const awEl = document.getElementById('availability-warning-threshold');
            const acEl = document.getElementById('availability-critical-threshold');
            if (awEl) awEl.value = String(availWarn);
            if (acEl) acEl.value = String(availCrit);

            // stratum: seulement critical (1..16), warning fixé à 1
            let stratCrit = document.getElementById('stratum-max-threshold') ? parseInt(document.getElementById('stratum-max-threshold').value, 10) : NaN;
            if (!Number.isFinite(stratCrit)) stratCrit = 0;
            stratCrit = Math.max(1, Math.min(16, stratCrit || 0));
            const scEl = document.getElementById('stratum-max-threshold');
            if (scEl) scEl.value = String(stratCrit);

            // Construire items pour l'API batch
            const items = [];
            items.push({ metric_name: 'offset', server_type_id: selectedId, warning_threshold: offsetWarn, critical_threshold: offsetCrit, enabled: true });
            items.push({ metric_name: 'latency', server_type_id: selectedId, warning_threshold: latWarn, critical_threshold: latCrit, enabled: true });
            items.push({ metric_name: 'availability', server_type_id: selectedId, warning_threshold: availWarn, critical_threshold: availCrit, enabled: true });
            items.push({ metric_name: 'stratum', server_type_id: selectedId, warning_threshold: 1, critical_threshold: stratCrit, enabled: true });
            
            const response = await fetch('/api/alerts/thresholds/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ items })
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            console.log('✅ Seuils sauvegardés (batch)');
            
        } catch (error) {
            console.error('Erreur sauvegarde seuils:', error);
            throw error; // Remonter l'erreur pour la gestion dans saveUnifiedAlertsConfig
        }
    }

    // ================== TYPES SERVEURS (ONGLET SEUILS) ==================
    async loadServerTypesList() {
        try {
            const res = await fetch('/api/admin/server-types', { credentials: 'include' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json().catch(() => ({}));
            this.serverTypes = Array.isArray(data.items) ? data.items : [];
            return this.serverTypes;
        } catch (e) {
            console.error('❌ Chargement server-types échoué:', e);
            this.serverTypes = [];
            return this.serverTypes;
        }
    }

    populateServerTypeSelector() {
        const sel = document.getElementById('server-type-selector');
        if (!sel) return null;
        sel.innerHTML = '';

        this.serverTypes.forEach(t => {
            const opt = document.createElement('option');
            opt.value = String(t.code || '');
            opt.textContent = t.label || t.code || `Type ${t.id}`;
            if (t.id != null) opt.dataset.id = String(t.id);
            sel.appendChild(opt);
        });

        // Préselection: local -> all -> première option
        let preferred = this.serverTypes.find(x => x.code === 'local')
            || this.serverTypes.find(x => x.code === 'all')
            || this.serverTypes[0];
        if (preferred) sel.value = String(preferred.code || '');
        return sel.value;
    }

    async loadAndPopulateServerTypes() {
        await this.loadServerTypesList();
        const code = this.populateServerTypeSelector();
        if (code) {
            await this.loadThresholdsForServerType(code);
            this.updateServerTypeIndicator(code);
        }
    }
    
    async saveUnifiedAlertsConfig() {
        // Sauvegarder la configuration des alertes (unifiée)
        try {
            console.log('💾 Sauvegarde de la configuration des alertes (unifiée)...');
            
            // Afficher l'état de chargement
            this.updateSaveButtonState(true);
            this.showNotification('Sauvegarde en cours...', 'info', 2000);
            
            // Récupérer les données des seuils
            await this.saveThresholds();
            
            // Récupérer les conditions d'alerte + notifications
            const unifiedAlertConditions = {
                use_threshold_conditions: document.getElementById('use-threshold-conditions')?.checked || false,
                use_latency_conditions: document.getElementById('use-latency-conditions')?.checked || false,
                use_availability_conditions: document.getElementById('use-availability-conditions')?.checked || false,
                use_stratum_conditions: document.getElementById('use-stratum-conditions')?.checked || false,
                
                // Seuils de conditions
                threshold_warning: parseFloat(document.getElementById('threshold-warning-threshold')?.value) || 0,
                threshold_critical: parseFloat(document.getElementById('threshold-critical-threshold')?.value) || 0,
                latency_warning: parseFloat(document.getElementById('latency-warning-threshold')?.value) || 0,
                latency_critical: parseFloat(document.getElementById('latency-critical-threshold')?.value) || 0,
                availability_warning: parseFloat(document.getElementById('availability-warning-threshold')?.value) || 0,
                availability_critical: parseFloat(document.getElementById('availability-critical-threshold')?.value) || 0,
                stratum_max: parseInt(document.getElementById('stratum-max-threshold')?.value) || 0,

                // Notifications / Webhook
                email_notifications: document.getElementById('email-enabled')?.checked || false,
                email_addresses: document.getElementById('email-addresses')?.value || '',
                min_alert_interval: parseInt(document.getElementById('min-alert-interval')?.value) || 0,
                webhook_notifications: document.getElementById('webhook-enabled')?.checked || false,
                webhook_url: document.getElementById('webhook-url')?.value || '',
                webhook_secret: document.getElementById('webhook-secret')?.value || ''
            };
            
            // Sauvegarder les conditions via l'API
            const response = await fetch('/api/config/alerts/conditions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(unifiedAlertConditions)
            });
            
            if (!response.ok) {
                throw new Error(`Erreur sauvegarde conditions unifiées: ${response.statusText}`);
            }
            
            // Afficher le succès
            this.updateSaveButtonState(false, true);
            this.showNotification('Configuration des alertes sauvegardée avec succès ! Les données ont été enregistrées en base.', 'success', 5000);
            this.isDirty = false;
            
            // Mettre à jour l'état du bouton
            this.updateSaveButton();
            
        } catch (error) {
            console.error('❌ Erreur sauvegarde configuration alertes unifiées:', error);
            
            // Afficher l'erreur
            this.updateSaveButtonState(false);
            this.showNotification(`Erreur lors de la sauvegarde : ${error.message}`, 'error', 8000);
        }
    }
    
    async resetAlertsConfig() {
        try {
            console.log('🔄 Réinitialisation de la configuration des alertes...');
            
            // Demander confirmation
            if (!confirm('Êtes-vous sûr de vouloir réinitialiser la configuration des alertes ? Cette action ne peut pas être annulée.')) {
                return;
            }
            
            // Afficher l'état de chargement
            this.showNotification('Réinitialisation en cours...', 'info', 2000);
            
            // Réinitialiser les valeurs par défaut
            const defaultValues = {
                'offset-warning-threshold': 1000,
                'offset-critical-threshold': 5000,
                'latency-warning-threshold': 200,
                'latency-critical-threshold': 800,
                'stratum-max-threshold': 15,
                'availability-warning-threshold': 98,
                'availability-critical-threshold': 90,
                'use-threshold-conditions': true,
                'use-latency-conditions': true,
                'use-availability-conditions': true,
                'use-stratum-conditions': true
            };
            
            // Appliquer les valeurs par défaut
            for (const [fieldId, value] of Object.entries(defaultValues)) {
                const field = document.getElementById(fieldId);
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value;
                    } else {
                        field.value = value;
                    }
                }
            }
            
            // Marquer comme modifié pour forcer la sauvegarde
            this.isDirty = true;
            this.updateSaveButton();
            
            this.showNotification('Configuration réinitialisée avec succès ! N\'oubliez pas de sauvegarder.', 'success', 5000);
            
        } catch (error) {
            console.error('❌ Erreur réinitialisation:', error);
            this.showNotification(`Erreur lors de la réinitialisation : ${error.message}`, 'error', 8000);
        }
    }
    
    async testAlertsConfig() {
        try {
            console.log('🧪 Test de la configuration des alertes...');
            
            // Afficher l'état de chargement
            this.showNotification('Test de la configuration en cours...', 'info', 2000);
            
            // Récupérer les valeurs actuelles
            const testConfig = {
                thresholds: {
                    offset: {
                        warning: parseFloat(document.getElementById('offset-warning-threshold')?.value) || 0,
                        critical: parseFloat(document.getElementById('offset-critical-threshold')?.value) || 0
                    },
                    latency: {
                        warning: parseFloat(document.getElementById('latency-warning-threshold')?.value) || 0,
                        critical: parseFloat(document.getElementById('latency-critical-threshold')?.value) || 0
                    },
                    stratum: {
                        max: parseInt(document.getElementById('stratum-max-threshold')?.value) || 0
                    },
                    availability: {
                        warning: parseFloat(document.getElementById('availability-warning-threshold')?.value) || 0,
                        critical: parseFloat(document.getElementById('availability-critical-threshold')?.value) || 0
                    }
                },
                conditions: {
                    use_threshold: document.getElementById('use-threshold-conditions')?.checked || false,
                    use_latency: document.getElementById('use-latency-conditions')?.checked || false,
                    use_availability: document.getElementById('use-availability-conditions')?.checked || false,
                    use_stratum: document.getElementById('use-stratum-conditions')?.checked || false
                }
            };
            
            // Simuler un test (ici on pourrait appeler une API de test)
            await new Promise(resolve => setTimeout(resolve, 1500)); // Simulation d'un test
            
            // Générer un rapport de test
            const testReport = this.generateTestReport(testConfig);
            
            // Afficher le résultat
            if (testReport.success) {
                this.showNotification(`Test réussi ! ${testReport.message}`, 'success', 5000);
            } else {
                this.showNotification(`Test échoué : ${testReport.message}`, 'error', 8000);
            }
            
        } catch (error) {
            console.error('❌ Erreur test configuration:', error);
            this.showNotification(`Erreur lors du test : ${error.message}`, 'error', 8000);
        }
    }
    
    generateTestReport(config) {
        // Simuler une validation de la configuration
        const issues = [];
        
        // Vérifier les seuils
        if (config.thresholds.offset.warning >= config.thresholds.offset.critical) {
            issues.push('Le seuil d\'avertissement offset doit être inférieur au seuil critique');
        }
        
        if (config.thresholds.latency.warning >= config.thresholds.latency.critical) {
            issues.push('Le seuil d\'avertissement latence doit être inférieur au seuil critique');
        }
        
        if (config.thresholds.availability.warning <= config.thresholds.availability.critical) {
            issues.push('Le seuil d\'avertissement disponibilité doit être supérieur au seuil critique');
        }
        
        if (config.thresholds.stratum.max < 1 || config.thresholds.stratum.max > 16) {
            issues.push('Le stratum maximum doit être entre 1 et 16');
        }
        
        // Vérifier qu'au moins une condition est activée
        const activeConditions = Object.values(config.conditions).filter(Boolean).length;
        if (activeConditions === 0) {
            issues.push('Au moins un type d\'alerte doit être activé');
        }
        
        return {
            success: issues.length === 0,
            message: issues.length === 0 
                ? 'Configuration valide et prête à être utilisée'
                : `Problèmes détectés : ${issues.join(', ')}`,
            issues: issues
        };
    }
    
    // ================== MÉTHODES UTILITAIRES ==================
    
    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value || '';
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        // Créer une notification visuelle
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            <strong>${type === 'error' ? 'Erreur' : type === 'success' ? 'Succès' : 'Information'}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-suppression après durée
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
        
        // Log pour debug
        console.log(`${type.toUpperCase()}: ${message}`);
    }
    
    showLoadingSpinner(show) {
        const spinner = document.getElementById('config-loading-spinner');
        if (spinner) {
            spinner.style.display = show ? 'flex' : 'none';
        }
    }
    
    updateSaveButtonState(isLoading = false, isSuccess = false) {
        const saveButton = document.querySelector('button[onclick*="saveUnifiedAlertsConfig"]');
        if (saveButton) {
            if (isLoading) {
                saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sauvegarde...';
                saveButton.disabled = true;
                saveButton.className = 'btn btn-warning btn-sm';
            } else if (isSuccess) {
                saveButton.innerHTML = '<i class="fas fa-check"></i> Sauvegardé ✓';
                saveButton.disabled = false;
                saveButton.className = 'btn btn-success btn-sm';
                
                // Remettre l'état normal après 3 secondes
                setTimeout(() => {
                    saveButton.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
                    saveButton.className = 'btn btn-success btn-sm';
                    this.updateSaveButton();
                }, 3000);
            } else {
                saveButton.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
                saveButton.disabled = false;
                saveButton.className = 'btn btn-success btn-sm';
            }
        }
    }
    
    async confirmUnsavedChanges() {
        return confirm('Vous avez des modifications non sauvegardées. Continuer ?');
    }
    
    attachAlertsFieldEvents() {
        // Attacher les événements pour les champs d'alerte
        const alertFields = [
            'use-threshold-conditions',
            'use-latency-conditions',
            'use-availability-conditions',
            'use-stratum-conditions',
            'threshold-warning',
            'threshold-critical',
            'latency-warning',
            'latency-critical',
            'availability-warning',
            'availability-critical',
            'stratum-max'
        ];
        
        alertFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('change', () => {
                    this.markDirty();
                });
                
                field.addEventListener('input', () => {
                    this.markDirty();
                });
            }
        });
        
        // Événements pour les checkboxes
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.markDirty();
            });
        });
    }

    attachUnifiedAlertsFieldEvents() {
        // Événements pour les champs de seuils
        const thresholdFields = [
            'offset-warning-threshold', 'offset-critical-threshold',
            'latency-warning-threshold', 'latency-critical-threshold',
            'availability-warning-threshold', 'availability-critical-threshold',
            'stratum-max-threshold'
        ];
        
        thresholdFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('input', () => {
                    this.markDirty();
                });
            }
        });
        
        // Événements pour les switches d'activation
        const switchFields = [
            'use-threshold-conditions', 'use-latency-conditions',
            'use-availability-conditions', 'use-stratum-conditions'
        ];
        
        switchFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('change', () => {
                    this.markDirty();
                });
            }
        });
        
        // Événement pour le sélecteur de type de serveur
        const serverTypeSelector = document.getElementById('server-type-selector');
        if (serverTypeSelector) {
            serverTypeSelector.addEventListener('change', (e) => {
                const selectedServerType = e.target.value;
                console.log(`🔄 Changement de type de serveur: ${selectedServerType}`);
                
                // Afficher l'indicateur de type sélectionné
                this.updateServerTypeIndicator(selectedServerType);
                
                // Charger les seuils pour ce type
                this.loadThresholdsForServerType(selectedServerType);
            });
        }

        // Bouton sauvegarder seuils (batch)
        const saveBtn = document.getElementById('save-thresholds-unified-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                try {
                    await this.saveThresholds();
                    this.showNotification('Seuils enregistrés', 'success');
                } catch (e) {
                    this.showNotification('Erreur enregistrement seuils: ' + e.message, 'error');
                }
            });
        }
    }
    
    updateServerTypeIndicator(serverType) {
        const indicator = document.getElementById('server-type-indicator');
        const selectedTypeSpan = document.getElementById('selected-server-type');
        
        if (indicator && selectedTypeSpan) {
            const typeLabels = {
                'all': 'Tous les serveurs',
                'local': 'Serveurs locaux',
                'pool': 'Pools NTP',
                'internet': 'Serveurs internet'
            };
            
            selectedTypeSpan.textContent = typeLabels[serverType] || serverType;
            indicator.style.display = 'block';
            
            console.log(`📋 Indicateur mis à jour pour: ${typeLabels[serverType]}`);
        }
    }
    
    async loadThresholdsForServerType(serverType) {
        try {
            console.log(`📊 Chargement des seuils pour le type de serveur: ${serverType}`);
            
            // Récupérer les seuils depuis l'API
            const response = await fetch('/api/alerts/thresholds');
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Erreur inconnue');
            }
            
            console.log(`📋 Total des seuils récupérés: ${data.thresholds.length}`);
            
            // Filtrer les seuils pour le type de serveur sélectionné
            const serverTypeThresholds = data.thresholds.filter(
                threshold => (threshold.server_type || '').toLowerCase() === String(serverType).toLowerCase()
            );
            
            console.log(`✅ ${serverTypeThresholds.length} seuils trouvés pour ${serverType}:`, serverTypeThresholds);
            
            // Récupérer les seuils "tous les serveurs" pour le fallback
            const allThresholds = data.thresholds.filter(
                threshold => threshold.server_type === 'all'
            );
            
            console.log(`📋 ${allThresholds.length} seuils 'tous les serveurs' disponibles:`, allThresholds);
            
            // Organiser les seuils par métrique avec fallback
            const organizedThresholds = {};
            
            // Métriques attendues
            const expectedMetrics = ['offset', 'latency', 'stratum', 'availability'];
            
            for (const metric of expectedMetrics) {
                // Chercher d'abord un seuil spécifique au type
                const specificThreshold = serverTypeThresholds.find(t => t.metric_name === metric);
                
                if (specificThreshold) {
                    console.log(`✅ Seuil spécifique trouvé pour ${metric}:`, specificThreshold);
                    organizedThresholds[metric] = {
                        [serverType]: {
                            warning_threshold: specificThreshold.warning_threshold,
                            critical_threshold: specificThreshold.critical_threshold,
                            unit: specificThreshold.unit,
                            enabled: specificThreshold.enabled
                        }
                    };
                } else {
                    // Chercher un seuil "tous les serveurs" comme fallback
                    const allThreshold = allThresholds.find(t => t.metric_name === metric);
                    
                    if (allThreshold) {
                        console.log(`🔄 Utilisation du seuil 'tous les serveurs' pour ${metric}:`, allThreshold);
                        organizedThresholds[metric] = {
                            'all': {
                                warning_threshold: allThreshold.warning_threshold,
                                critical_threshold: allThreshold.critical_threshold,
                                unit: allThreshold.unit,
                                enabled: allThreshold.enabled
                            }
                        };
                    } else {
                        console.log(`⚠️ Aucun seuil trouvé pour ${metric} (ni spécifique, ni fallback)`);
                        // Ne pas ajouter à organizedThresholds pour laisser le champ vide
                    }
                }
            }
            
            console.log('📋 Seuils organisés avec fallback:', organizedThresholds);
            
            // Remplir les champs avec les seuils correspondants
            this.populateThresholdFields(organizedThresholds);
            
        } catch (error) {
            console.error(`❌ Erreur chargement seuils pour ${serverType}:`, error);
            this.showNotification(`Erreur chargement seuils: ${error.message}`, 'error');
        }
    }
    
    populateThresholdFields(thresholds) {
        console.log('🔧 Remplissage des champs avec les seuils:', thresholds);
        
        // Détecter si l'objet est organisé par type (ex: { offset: { local: {...} } })
        const isOrganizedData = thresholds.offset 
            && typeof thresholds.offset === 'object' 
            && !('warning_threshold' in thresholds.offset);
        
        if (isOrganizedData) {
            // Données organisées depuis l'API
            console.log('📊 Utilisation des données organisées depuis l\'API');
            
            // Remplir les champs offset
            if (thresholds.offset) {
                const offsetThresholds = Object.values(thresholds.offset)[0];
                console.log('📊 Seuils offset trouvés:', offsetThresholds);
                this.setFieldValue('offset-warning-threshold', offsetThresholds.warning_threshold);
                this.setFieldValue('offset-critical-threshold', offsetThresholds.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil offset trouvé');
                this.setFieldValue('offset-warning-threshold', '');
                this.setFieldValue('offset-critical-threshold', '');
            }
            
            // Remplir les champs latency
            if (thresholds.latency) {
                const latencyThresholds = Object.values(thresholds.latency)[0];
                console.log('📊 Seuils latency trouvés:', latencyThresholds);
                this.setFieldValue('latency-warning-threshold', latencyThresholds.warning_threshold);
                this.setFieldValue('latency-critical-threshold', latencyThresholds.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil latency trouvé');
                this.setFieldValue('latency-warning-threshold', '');
                this.setFieldValue('latency-critical-threshold', '');
            }
            
            // Remplir les champs availability
            if (thresholds.availability) {
                const availabilityThresholds = Object.values(thresholds.availability)[0];
                console.log('📊 Seuils availability trouvés:', availabilityThresholds);
                this.setFieldValue('availability-warning-threshold', availabilityThresholds.warning_threshold);
                this.setFieldValue('availability-critical-threshold', availabilityThresholds.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil availability trouvé');
                this.setFieldValue('availability-warning-threshold', '');
                this.setFieldValue('availability-critical-threshold', '');
            }
            
            // Remplir les champs stratum
            if (thresholds.stratum) {
                const stratumThresholds = Object.values(thresholds.stratum)[0];
                console.log('📊 Seuils stratum trouvés:', stratumThresholds);
                this.setFieldValue('stratum-max-threshold', stratumThresholds.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil stratum trouvé');
                this.setFieldValue('stratum-max-threshold', '');
            }
        } else {
            // Valeurs par défaut (ne devrait plus arriver avec la nouvelle logique)
            console.log('📊 Utilisation des valeurs par défaut');
            
            // Remplir les champs offset
            if (thresholds.offset) {
                console.log('📊 Seuils offset par défaut:', thresholds.offset);
                this.setFieldValue('offset-warning-threshold', thresholds.offset.warning_threshold);
                this.setFieldValue('offset-critical-threshold', thresholds.offset.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil offset par défaut');
                this.setFieldValue('offset-warning-threshold', '');
                this.setFieldValue('offset-critical-threshold', '');
            }
            
            // Remplir les champs latency
            if (thresholds.latency) {
                console.log('📊 Seuils latency par défaut:', thresholds.latency);
                this.setFieldValue('latency-warning-threshold', thresholds.latency.warning_threshold);
                this.setFieldValue('latency-critical-threshold', thresholds.latency.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil latency par défaut');
                this.setFieldValue('latency-warning-threshold', '');
                this.setFieldValue('latency-critical-threshold', '');
            }
            
            // Remplir les champs availability
            if (thresholds.availability) {
                console.log('📊 Seuils availability par défaut:', thresholds.availability);
                this.setFieldValue('availability-warning-threshold', thresholds.availability.warning_threshold);
                this.setFieldValue('availability-critical-threshold', thresholds.availability.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil availability par défaut');
                this.setFieldValue('availability-warning-threshold', '');
                this.setFieldValue('availability-critical-threshold', '');
            }
            
            // Remplir les champs stratum
            if (thresholds.stratum) {
                console.log('📊 Seuils stratum par défaut:', thresholds.stratum);
                this.setFieldValue('stratum-max-threshold', thresholds.stratum.critical_threshold);
            } else {
                console.log('⚠️ Aucun seuil stratum par défaut');
                this.setFieldValue('stratum-max-threshold', '');
            }
        }
        
        console.log('✅ Champs de seuils remplis avec les données du type de serveur');
    }
    
    getStratumWarningThreshold() {
        // Retourner la valeur de warning pour stratum (généralement 0 car stratum n'a pas de warning)
        // Stratum n'a généralement pas de seuil d'avertissement, seulement un seuil critique
        // Cette valeur peut être configurée via l'API si nécessaire
        return 0;
    }
    
    setupEventListeners() {
        // Événements pour les catégories
        document.addEventListener('click', (e) => {
            if (e.target.closest('.category-item')) {
                const category = e.target.closest('.category-item').dataset.category;
                this.loadCategory(category);
            }
        });
        
        // Événements pour les seuils
        document.addEventListener('change', (e) => {
            if (e.target.name === 'server-type') {
                this.populateThresholdsForm();
            }
        });
        
        // Événements pour les champs de seuils
        document.addEventListener('input', (e) => {
            if (e.target.id && e.target.id.includes('-threshold')) {
                this.markDirty();
            }
        });
    }
    
    markDirty() {
        this.isDirty = true;
        this.updateSaveButton();
    }
    
    updateSaveButton() {
        const saveButton = document.querySelector('button[onclick*="saveUnifiedAlertsConfig"]');
        if (saveButton) {
            saveButton.disabled = !this.isDirty;
            saveButton.innerHTML = this.isDirty ? 
                '<i class="fas fa-save"></i> Sauvegarder *' : 
                '<i class="fas fa-save"></i> Sauvegarder';
        }
    }
    
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

    async populateUnifiedThresholdsForm() {
        try {
            console.log('📊 Remplissage du formulaire de seuils unifiés...');
            
            // Attendre que le DOM soit prêt
            await this.waitForElement('#server-type-selector');
            // Si la liste est vide, (re)charger les types serveurs et peupler
            if (!this.serverTypes || this.serverTypes.length === 0) {
                await this.loadAndPopulateServerTypes();
            }
            
            // Charger les conditions d'alerte
            console.log('🔄 Chargement des conditions d\'alerte...');
            const conditions = await this.loadAlertConditions();
            console.log('📋 Conditions d\'alerte chargées:', conditions);
            
            // Remplir les champs de conditions d'alerte
            if (conditions) {
                this.populateAlertConditions(conditions);
            }
            
            // Charger les seuils pour le type de serveur sélectionné par défaut
            const serverTypeSelector = document.getElementById('server-type-selector');
            const selectedServerType = serverTypeSelector ? serverTypeSelector.value : 'all';
            
            console.log(`🎯 Chargement des seuils pour le type de serveur: ${selectedServerType}`);
            await this.loadThresholdsForServerType(selectedServerType);
            
            // Afficher l'indicateur de type sélectionné
            this.updateServerTypeIndicator(selectedServerType);
            
            console.log('✅ Formulaire de seuils unifiés rempli avec succès');
            
        } catch (error) {
            console.error('❌ Erreur remplissage formulaire seuils unifiés:', error);
            this.showNotification(`Erreur chargement seuils: ${error.message}`, 'error');
        }
    }
    
    async populateAllTabs() {
        // Remplir les onglets (sans l'onglet Seuils, géré sur page dédiée)
        try {
            console.log('📊 Remplissage des onglets Notifications/Rétention/Avancé...');
            await this.populateNotificationsTab();
            await this.populateRetentionTab();
            await this.populateAdvancedTab();
            console.log('✅ Onglets remplis');
        } catch (error) {
            console.error('❌ Erreur remplissage onglets:', error);
            this.showNotification(`Erreur chargement onglets: ${error.message}`, 'error');
        }
    }
    
    async populateNotificationsTab() {
        // Remplir l'onglet notifications avec les données de la base
        try {
            console.log('🔔 Remplissage de l\'onglet notifications...');
            
            const conditions = await this.loadAlertConditions();
            if (conditions) {
                // Remplir les champs de notifications
                const notificationMappings = {
                    'email_notifications': 'email-enabled',
                    'email_addresses': 'email-addresses',
                    'min_alert_interval': 'min-alert-interval',
                    'webhook_notifications': 'webhook-enabled',
                    'webhook_url': 'webhook-url',
                    'webhook_secret': 'webhook-secret'
                };
                
                for (const [conditionKey, fieldId] of Object.entries(notificationMappings)) {
                    const value = conditions[conditionKey];
                    if (value !== undefined) {
                        const element = document.getElementById(fieldId);
                        if (element) {
                            if (element.type === 'checkbox') {
                                element.checked = Boolean(value);
                            } else {
                                element.value = value;
                            }
                            console.log(`✅ Notification ${fieldId} rempli avec ${value}`);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Erreur remplissage notifications:', error);
        }
    }
    
    async populateRetentionTab() {
        // Remplir l'onglet rétention avec les données de la base
        try {
            console.log('📦 Remplissage de l\'onglet rétention...');
            
            const conditions = await this.loadAlertConditions();
            if (conditions) {
                // Remplir les champs de rétention
                const retentionMappings = {
                    'resolved_alerts_retention': 'resolved-alerts-retention',
                    'acknowledged_alerts_retention': 'acknowledged-alerts-retention',
                    'detailed_logs_retention': 'detailed-logs-retention',
                    'aggregated_logs_retention': 'aggregated-logs-retention'
                };
                
                for (const [conditionKey, fieldId] of Object.entries(retentionMappings)) {
                    const value = conditions[conditionKey];
                    if (value !== undefined) {
                        const element = document.getElementById(fieldId);
                        if (element) {
                            element.value = value;
                            console.log(`✅ Rétention ${fieldId} rempli avec ${value}`);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Erreur remplissage rétention:', error);
        }
    }
    
    async populateAdvancedTab() {
        // Remplir l'onglet avancé avec les données de la base
        try {
            console.log('⚙️ Remplissage de l\'onglet avancé...');
            
            const conditions = await this.loadAlertConditions();
            if (conditions) {
                // Remplir les champs avancés
                const advancedMappings = {
                    'debug_mode': 'debug-mode',
                    'log_level': 'log-level',
                    'check_interval': 'check-interval',
                    'connection_timeout': 'connection-timeout',
                    'ntp_timeout': 'ntp-timeout',
                    'max_consecutive_failures': 'max-consecutive-failures',
                    'escalation_enabled': 'escalation-enabled',
                    'escalation_delay': 'escalation-delay'
                };
                
                for (const [conditionKey, fieldId] of Object.entries(advancedMappings)) {
                    const value = conditions[conditionKey];
                    if (value !== undefined) {
                        const element = document.getElementById(fieldId);
                        if (element) {
                            if (element.type === 'checkbox') {
                                element.checked = Boolean(value);
                            } else {
                                element.value = value;
                            }
                            console.log(`✅ Avancé ${fieldId} rempli avec ${value}`);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Erreur remplissage avancé:', error);
        }
    }
    
    async waitForElement(selector, timeout = 5000) {
        // Attendre qu'un élément soit présent dans le DOM
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const element = document.querySelector(selector);
            if (element) {
                return element;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        throw new Error(`Élément ${selector} non trouvé après ${timeout}ms`);
    }
    
    populateAlertConditions(conditions) {
        // Remplir les champs de conditions d'alerte
        console.log('🔧 Remplissage des conditions d\'alerte:', conditions);
        
        // Remplir les champs de conditions
        const fieldMappings = {
            'use_threshold_conditions': 'use-threshold-conditions',
            'use_latency_conditions': 'use-latency-conditions',
            'use_availability_conditions': 'use-availability-conditions',
            'use_stratum_conditions': 'use-stratum-conditions',
            'offset_warning_threshold': 'offset-warning-threshold',
            'offset_critical_threshold': 'offset-critical-threshold',
            'latency_warning_threshold': 'latency-warning-threshold',
            'latency_critical_threshold': 'latency-critical-threshold',
            'availability_warning_threshold': 'availability-warning-threshold',
            'availability_critical_threshold': 'availability-critical-threshold',
            'stratum_max_threshold': 'stratum-max-threshold'
        };
        
        for (const [conditionKey, fieldId] of Object.entries(fieldMappings)) {
            const value = conditions[conditionKey];
            if (value !== undefined) {
                const element = document.getElementById(fieldId);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = Boolean(value);
                    } else {
                        element.value = value;
                    }
                    console.log(`✅ Rempli ${fieldId} avec ${value}`);
                } else {
                    console.log(`⚠️ Élément ${fieldId} non trouvé`);
                }
            }
        }
    }
    
    async loadAlertConditions() {
        try {
            const response = await fetch('/api/config/alerts/conditions');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    return data.conditions;
                }
            }
            return null;
        } catch (error) {
            console.error('❌ Erreur chargement conditions:', error);
            return null;
        }
    }

    renderConfigFields(configs) {
        return configs.map(config => {
            const fieldId = `config-${config.key.replace(/\./g, '-')}`;
            const isReadOnly = !this.currentCategory?.can_modify;
            
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
    
    getConfigDisplayName(key) {
        // Mapper les clés vers des noms d'affichage conviviaux
        const displayNames = {
            'system.app_name': 'Nom de l\'application',
            'system.version': 'Version',
            'system.timezone': 'Fuseau horaire',
            'ntp.query_interval': 'Intervalle de requête NTP',
            'ntp.default_timeout': 'Timeout par défaut NTP',
            'alerts.retention_days': 'Durée de conservation des alertes',
            'alerts.email_enabled': 'Notifications par email',
            'alerts.webhook_enabled': 'Webhooks',
            'network.max_connections': 'Connexions maximales',
            'network.connection_timeout': 'Timeout de connexion',
            'monitoring.log_retention_days': 'Conservation des logs',
            'monitoring.stats_interval': 'Intervalle des statistiques'
        };
        
        return displayNames[key] || key.replace(/\./g, ' ').replace(/\b\w/g, l => l.toUpperCase());
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
        if (isValid && this.validationRules && this.validationRules[key]) {
            const rule = this.validationRules[key];
            const numValue = Number(value);
            
            if (rule.min !== undefined && numValue < rule.min) {
                isValid = false;
                errorMessage = rule.message || `Valeur minimum: ${rule.min}`;
            } else if (rule.max !== undefined && numValue > rule.max) {
                isValid = false;
                errorMessage = rule.message || `Valeur maximum: ${rule.max}`;
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
        this.clearValidationError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
    
    clearValidationError(field) {
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    async autoSave() {
        if (!this.autoSaveEnabled) return;
        
        try {
            console.log('💾 Auto-save en cours...');
            await this.saveCategory();
            this.showNotification('Configuration sauvegardée automatiquement', 'success', 2000);
        } catch (error) {
            console.error('Erreur auto-save:', error);
        }
    }
    
    async saveCategory() {
        if (!this.currentCategory) return;
        
        try {
            this.showLoadingSpinner(true);
            
            const configData = this.collectConfigData();
            if (!configData || Object.keys(configData).length === 0) {
                throw new Error('Aucune donnée à sauvegarder');
            }
            
            const categoryKey = this.currentCategory.category || this.currentCategory.data?.category;
            if (!categoryKey) throw new Error('Catégorie inconnue');
            const response = await fetch(`/api/config/category/${categoryKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(configData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erreur sauvegarde');
            }
            
            const result = await response.json();
            if (result.success) {
                this.showNotification('Configuration sauvegardée avec succès', 'success');
                this.isDirty = false;
                this.updateSaveButton();
            } else {
                throw new Error(result.error || 'Erreur sauvegarde');
            }
            
        } catch (error) {
            console.error('Erreur sauvegarde catégorie:', error);
            this.showNotification(`Erreur sauvegarde: ${error.message}`, 'error');
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    collectConfigData() {
        const configData = {};
        const fields = document.querySelectorAll('#config-content input, #config-content textarea, #config-content select');
        
        fields.forEach(field => {
            const key = field.dataset.key;
            if (key) {
                configData[key] = this.getFieldValue(field);
            }
        });
        
        return configData;
    }
    
    getFieldValue(field) {
        if (field.type === 'checkbox') {
            return field.checked;
        } else if (field.type === 'number') {
            return field.value === '' ? null : Number(field.value);
        } else {
            return field.value;
        }
    }
    
    async resetCategory() {
        if (!this.currentCategory) return;
        
        const confirmed = await this.confirmAction('Êtes-vous sûr de vouloir réinitialiser cette catégorie ?');
        if (!confirmed) return;
        
        try {
            this.showLoadingSpinner(true);
            await this.loadCategory(this.currentCategory.category);
            this.showNotification('Catégorie réinitialisée', 'info');
        } catch (error) {
            console.error('Erreur réinitialisation:', error);
            this.showNotification(`Erreur réinitialisation: ${error.message}`, 'error');
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    async testConfiguration() {
        if (!this.currentCategory) return;
        
        try {
            this.showLoadingSpinner(true);
            
            const response = await fetch(`/api/config/test/${this.currentCategory.category}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.collectConfigData())
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erreur test');
            }
            
            const result = await response.json();
            this.showTestResults(result);
            
        } catch (error) {
            console.error('Erreur test configuration:', error);
            this.showNotification(`Erreur test: ${error.message}`, 'error');
        } finally {
            this.showLoadingSpinner(false);
        }
    }
    
    showTestResults(results) {
        const resultsHTML = `
            <div class="alert alert-info">
                <h6><i class="fas fa-flask me-2"></i>Résultats du Test</h6>
                <pre class="mb-0">${JSON.stringify(results, null, 2)}</pre>
            </div>
        `;
        
        const configContainer = document.getElementById('config-content');
        if (configContainer) {
            const existingResults = configContainer.querySelector('.alert-info');
            if (existingResults) {
                existingResults.remove();
            }
            configContainer.insertAdjacentHTML('afterbegin', resultsHTML);
        }
    }
    
    async confirmAction(message) {
        return new Promise((resolve) => {
            if (confirm(message)) {
                resolve(true);
            } else {
                resolve(false);
            }
        });
    }
}

// Initialisation
function initConfigManagerUpdated() {
    window.configManager = new ConfigManagerUpdated();
}

// Auto-initialisation
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('configModal')) {
        initConfigManagerUpdated();
        try {
            const saveAllBtn = document.getElementById('config-save-all');
            if (saveAllBtn) {
                saveAllBtn.addEventListener('click', async () => {
                    try {
                        // Sauvegarder la catégorie courante si disponible
                        if (window.configManager && window.configManager.currentCategory) {
                            await window.configManager.saveCategory();
                        }
                        // Sauvegarder les seuils si onglet alertes visible
                        const tabPane = document.getElementById('unified-thresholds');
                        if (tabPane && tabPane.classList.contains('show')) {
                            await window.configManager.saveThresholds();
                        }
                        window.configManager.showNotification('Toutes les sections visibles ont été sauvegardées', 'success');
                    } catch (e) {
                        window.configManager.showNotification('Erreur lors de la sauvegarde globale: ' + e.message, 'error');
                    }
                });
            }
        } catch (e) { /* noop */ }
    }
}); 