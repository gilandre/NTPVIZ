/**
 * Gestionnaire de Configuration des Seuils d'Alertes
 * Interface pour modifier AlertThreshold
 */

class ThresholdConfigManager {
    constructor() {
        this.thresholds = [];
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Bouton de sauvegarde
        $(document).on('click', '#save-thresholds-btn', () => {
            this.saveThresholds();
        });
        
        // Bouton de réinitialisation
        $(document).on('click', '#reset-thresholds-btn', () => {
            this.loadThresholds();
        });
        
        // Validation en temps réel
        $(document).on('input', '.threshold-input', (e) => {
            this.validateThreshold($(e.target));
        });
    }
    
    async loadThresholds() {
        try {
            console.log('🔄 Chargement des seuils d'alertes...');
            
            const response = await fetch('/api/alerts/thresholds', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.thresholds = data.thresholds;
                this.renderThresholds();
                console.log('✅ Seuils chargés:', this.thresholds.length);
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erreur chargement seuils:', error);
            alert('Erreur lors du chargement des seuils: ' + error.message);
        }
    }
    
    renderThresholds() {
        const container = $('#thresholds-container');
        if (!container.length) return;
        
        let html = '';
        
        this.thresholds.forEach(threshold => {
            html += `
                <div class="card mb-3" data-threshold-id="${threshold.id}">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-cog me-2"></i>
                            ${threshold.metric_label} (${threshold.metric_name})
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Seuil d'Avertissement</label>
                                <div class="input-group">
                                    <input type="number" 
                                           class="form-control threshold-input" 
                                           data-threshold-id="${threshold.id}"
                                           data-field="warning_threshold"
                                           value="${threshold.warning_threshold}"
                                           min="1" step="0.1">
                                    <span class="input-group-text">${threshold.unit}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Seuil Critique</label>
                                <div class="input-group">
                                    <input type="number" 
                                           class="form-control threshold-input" 
                                           data-threshold-id="${threshold.id}"
                                           data-field="critical_threshold"
                                           value="${threshold.critical_threshold}"
                                           min="1" step="0.1">
                                    <span class="input-group-text">${threshold.unit}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Statut</label>
                                <div class="form-check form-switch">
                                    <input class="form-check-input threshold-input" 
                                           type="checkbox" 
                                           data-threshold-id="${threshold.id}"
                                           data-field="enabled"
                                           ${threshold.enabled ? 'checked' : ''}>
                                    <label class="form-check-label">
                                        ${threshold.enabled ? 'Activé' : 'Désactivé'}
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <small class="text-muted">
                                    ${threshold.description || 'Aucune description'}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.html(html);
    }
    
    validateThreshold(input) {
        const thresholdId = input.data('threshold-id');
        const field = input.data('field');
        const value = input.val();
        
        // Validation warning < critical
        if (field === 'warning_threshold' || field === 'critical_threshold') {
            const card = input.closest('.card');
            const warningInput = card.find('[data-field="warning_threshold"]');
            const criticalInput = card.find('[data-field="critical_threshold"]');
            
            const warningValue = parseFloat(warningInput.val());
            const criticalValue = parseFloat(criticalInput.val());
            
            if (warningValue >= criticalValue) {
                input.addClass('is-invalid');
                return false;
            } else {
                warningInput.removeClass('is-invalid');
                criticalInput.removeClass('is-invalid');
                return true;
            }
        }
        
        return true;
    }
    
    async saveThresholds() {
        try {
            console.log('💾 Sauvegarde des seuils...');
            
            const updates = [];
            
            // Collecter toutes les modifications
            $('.threshold-input').each((index, element) => {
                const input = $(element);
                const thresholdId = input.data('threshold-id');
                const field = input.data('field');
                let value = input.val();
                
                if (input.attr('type') === 'checkbox') {
                    value = input.is(':checked');
                }
                
                // Validation
                if (!this.validateThreshold(input)) {
                    throw new Error('Validation échouée: seuil d'avertissement >= seuil critique');
                }
                
                // Trouver ou créer l'update pour ce threshold
                let update = updates.find(u => u.id === thresholdId);
                if (!update) {
                    update = { id: thresholdId, data: {} };
                    updates.push(update);
                }
                
                update.data[field] = value;
            });
            
            // Sauvegarder chaque seuil
            for (const update of updates) {
                const response = await fetch(`/api/alerts/thresholds/${update.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(update.data)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP ${response.status}`);
                }
            }
            
            // Recharger les seuils
            await this.loadThresholds();
            
            // Notification de succès
            alert('Seuils sauvegardés avec succès');
            console.log('✅ Seuils sauvegardés');
            
        } catch (error) {
            console.error('❌ Erreur sauvegarde seuils:', error);
            alert('Erreur lors de la sauvegarde: ' + error.message);
        }
    }
}

// Initialisation globale
window.thresholdConfigManager = new ThresholdConfigManager();

// Auto-initialisation
$(document).ready(() => {
    if ($('#thresholds-container').length) {
        window.thresholdConfigManager.loadThresholds();
    }
});
