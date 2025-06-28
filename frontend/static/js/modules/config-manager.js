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
            if (!response.ok) throw new Error('Erreur chargement catégories');
            
            this.categories = await response.json();
            this.renderCategoriesMenu();
            
            // Charger la première catégorie par défaut
            const firstCategory = Object.keys(this.categories)[0];
            if (firstCategory) {
                await this.loadCategory(firstCategory);
            }
            
        } catch (error) {
            console.error('Erreur lors du chargement des catégories:', error);
            this.showNotification('Erreur de chargement des catégories', 'error');
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
        // Navigation entre catégories
        document.addEventListener('click', (e) => {
            if (e.target.closest('.category-item')) {
                const categoryElement = e.target.closest('.category-item');
                const categoryName = categoryElement.dataset.category;
                this.loadCategory(categoryName);
            }
        });
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveCategory();
            }
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.resetCategory();
            }
        });
        
        // Gestion de la fermeture
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty) {
                e.preventDefault();
                e.returnValue = 'Des modifications non sauvegardées seront perdues.';
            }
        });
    }
    
    attachFieldEvents() {
        const configFields = document.querySelectorAll('#config-content input, #config-content textarea, #config-content select');
        
        configFields.forEach(field => {
            field.addEventListener('input', (e) => {
                this.handleFieldChange(e.target);
            });
            
            field.addEventListener('blur', (e) => {
                this.validateField(e.target);
            });
        });
    }
    
    handleFieldChange(field) {
        this.markDirty();
        this.clearValidationError(field);
        
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
            'ntp.query_interval': {
                min: 10,
                max: 3600,
                message: 'Doit être entre 10 et 3600 secondes'
            },
            'ntp.default_timeout': {
                min: 1,
                max: 60,
                message: 'Doit être entre 1 et 60 secondes'
            },
            'ntp.max_offset_warning': {
                min: 0.1,
                max: 60.0,
                message: 'Doit être entre 0.1 et 60 secondes'
            },
            'ntp.max_offset_critical': {
                min: 0.5,
                max: 300.0,
                message: 'Doit être entre 0.5 et 300 secondes'
            }
        };
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
        // Utiliser le système de notifications global
        if (window.showNotification) {
            window.showNotification(message, type, duration);
        } else {
            // Fallback simple
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Initialisation globale
let configManager;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('config-categories-menu')) {
        configManager = new ConfigManager();
    }
});

// Export pour utilisation externe
window.ConfigManager = ConfigManager; 