/**
 * Gestionnaire de Configuration des Seuils d'Alertes
 * Interface pour modifier AlertThreshold
 */

class ThresholdConfigManager {
    constructor() {
        this.thresholds = [];
        // Filtre par défaut: serveurs locaux
        this.currentServerType = 'local';
        this.serverTypes = [];
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Bouton de sauvegarde
        $(document).on('click', '#save-thresholds-btn', () => {
            this.saveThresholdsBatch();
        });
        
        // Bouton de réinitialisation
        $(document).on('click', '#reset-thresholds-btn', () => {
            this.loadThresholds();
        });
        // Filtre type serveur (par id ou code)
        $(document).on('change', '#thresholds-type-filter', (e) => {
            const val = (e.target.value || '').trim();
            // Déterminer si c'est un id ou un code
            if (/^\d+$/.test(val)) {
                const it = this.serverTypes.find(x => String(x.id) === val);
                this.currentServerType = (it && it.code) ? it.code : 'all';
                this.currentServerTypeId = parseInt(val, 10);
            } else {
                this.currentServerType = val || 'all';
                this.currentServerTypeId = null;
            }
            this.renderThresholds();
        });
        // Bouton seuils par défaut
        $(document).on('click', '#defaults-thresholds-btn', () => {
            this.applyDefaultThresholds();
        });
        
        // Validation en temps réel
        $(document).on('input', '.threshold-input', (e) => {
            this.validateThreshold($(e.target));
        });
    }
    
    async loadThresholds() {
        try {
            console.log('🔄 Chargement des seuils d\'alertes...');
            await this.loadServerTypes();
            
            const response = await fetch('/api/alerts/thresholds', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.thresholds = data.thresholds;
                this.populateTypeFilter();
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
        // Grouper par métrique puis par type serveur pour lisibilité
        const byMetric = {};
        // Filtrer par type courant (code). Les thresholds incluent server_type et server_type_id
        const items = (this.thresholds || []).filter(t => {
            if (this.currentServerTypeId) return String(t.server_type_id || '') === String(this.currentServerTypeId);
            return (t.server_type || '').toLowerCase() === (this.currentServerType || 'all');
        });
        // Si aucun seuil local n'est défini, fallback sur 'all'
        const source = items.length ? items : (this.thresholds || []).filter(t => t.server_type === 'all');
        source.forEach(t => {
            const key = t.metric_name;
            if (!byMetric[key]) byMetric[key] = [];
            byMetric[key].push(t);
        });
        const orderMetric = ['offset', 'latency', 'stratum'];
        const orderServerType = ['local', 'internet', 'pool', 'all'];
        let html = '';
        orderMetric.forEach(metric => {
            if (!byMetric[metric]) return;
            // Titre métrique
            const mlabel = byMetric[metric][0].metric_label || metric;
            html += `<h5 class="mt-3 mb-2"><i class="fas fa-cog me-2"></i>${mlabel}</h5>`;
            // Ordre par server_type
            const sorted = byMetric[metric].slice().sort((a,b) => orderServerType.indexOf(a.server_type) - orderServerType.indexOf(b.server_type));
            sorted.forEach(threshold => {
                const stLabel = threshold.server_type_label || threshold.server_type;
                html += `
                <div class="card mb-2" data-threshold-id="${threshold.id}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${stLabel}</h6>
                        <span class="badge bg-light text-dark">${threshold.metric_name}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Seuil d'Avertissement</label>
                                <div class="input-group">
                                    <input type="number" class="form-control threshold-input" data-threshold-id="${threshold.id}" data-field="warning_threshold" value="${threshold.warning_threshold}" min="1" step="0.1">
                                    <span class="input-group-text">${threshold.unit}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Seuil Critique</label>
                                <div class="input-group">
                                    <input type="number" class="form-control threshold-input" data-threshold-id="${threshold.id}" data-field="critical_threshold" value="${threshold.critical_threshold}" min="1" step="0.1">
                                    <span class="input-group-text">${threshold.unit}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Statut</label>
                                <div class="form-check form-switch">
                                    <input class="form-check-input threshold-input" type="checkbox" data-threshold-id="${threshold.id}" data-field="enabled" ${threshold.enabled ? 'checked' : ''}>
                                    <label class="form-check-label">${threshold.enabled ? 'Activé' : 'Désactivé'}</label>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12"><small class="text-muted">${threshold.description || 'Aucune description'}</small></div>
                        </div>
                    </div>
                </div>`;
            });
        });
        container.html(html);
    }

    async loadServerTypes() {
        try {
            const res = await fetch('/api/admin/server-types', { credentials: 'include' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            this.serverTypes = data.items || [];
        } catch (e) {
            console.warn('Chargement server-types échoué', e);
            this.serverTypes = [
                { id: 'local', code: 'local', label: 'Local' },
                { id: 'internet', code: 'internet', label: 'Internet' },
                { id: 'pool', code: 'pool', label: 'Pool public' },
                { id: 'all', code: 'all', label: 'Tous' }
            ];
        }
    }

    populateTypeFilter() {
        const sel = document.getElementById('thresholds-type-filter');
        if (!sel) return;
        sel.innerHTML = '';
        // Option "Tous les types"
        const optAll = document.createElement('option');
        optAll.value = '';
        optAll.textContent = 'Tous les types';
        sel.appendChild(optAll);
        this.serverTypes.forEach(t => {
            const opt = document.createElement('option');
            opt.value = String(t.id); // id numérique
            opt.textContent = t.label;
            opt.dataset.code = t.code;
            sel.appendChild(opt);
        });
        // Valeur par défaut -> local si présent
        const def = this.serverTypes.find(x => x.code === 'local') || this.serverTypes.find(x => x.code === 'all');
        if (def) {
            sel.value = String(def.id);
            // Synchroniser l'état interne avec la présélection
            const isNumeric = /^\d+$/.test(String(def.id));
            this.currentServerType = def.code || (isNumeric ? this.currentServerType : (String(def.id) || 'all'));
            this.currentServerTypeId = isNumeric ? parseInt(def.id, 10) : null;
        }
        // Rendu immédiat selon la présélection
        this.renderThresholds();
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
            const metricName = (card.find('.badge').last().text() || '').trim().toLowerCase();
            
            const warningValue = parseFloat(warningInput.val());
            const criticalValue = parseFloat(criticalInput.val());
            
            // Règles: offset/latency => warning < critical; availability => critical < warning
            const isAvailability = metricName === 'availability' || metricName === 'disponibilité';
            const ok = isAvailability ? (criticalValue < warningValue) : (warningValue < criticalValue);
            if (!ok) {
                input.addClass('is-invalid');
                return false;
            }
            warningInput.removeClass('is-invalid');
            criticalInput.removeClass('is-invalid');
            return true;
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
                    throw new Error('Validation échouée: règle de comparaison warning/critical incorrecte');
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
            // Synchroniser SystemConfig
            await this.syncSystemConfig();
            
            // Notification de succès
            this.setSyncIndicator('Seuils sauvegardés et synchronisés', true);
            console.log('✅ Seuils sauvegardés');
            
        } catch (error) {
            console.error('❌ Erreur sauvegarde seuils:', error);
            this.setSyncIndicator('Erreur lors de la sauvegarde: ' + error.message, false);
        }
    }

    async saveThresholdsBatch() {
        try {
            console.log('💾 Sauvegarde batch des seuils...');
            const items = [];
            const sel = document.getElementById('thresholds-type-filter');
            const serverTypeId = sel && /^\d+$/.test(sel.value) ? parseInt(sel.value, 10) : null;
            if (!serverTypeId) throw new Error('Type de serveurs non sélectionné');

            // Collecter par carte
            $('#thresholds-container .card').each((_, cardEl) => {
                const card = $(cardEl);
                const thresholdId = card.data('threshold-id');
                const warningInput = card.find('[data-field="warning_threshold"]');
                const criticalInput = card.find('[data-field="critical_threshold"]');
                const enabledInput = card.find('[data-field="enabled"]');
                const unit = (card.find('.input-group-text').first().text() || '').trim();
                const metricName = (card.find('.badge').last().text() || '').trim();
                const warn = parseFloat(warningInput.val());
                const crit = parseFloat(criticalInput.val());
                if (!(warn < crit)) throw new Error(`Validation échouée (${metricName}): warning < critical requis`);
                items.push({
                    id: thresholdId,
                    metric_name: (metricName || 'offset').toLowerCase(),
                    server_type_id: serverTypeId,
                    warning_threshold: warn,
                    critical_threshold: crit,
                    unit: unit || null,
                    enabled: !!enabledInput.is(':checked')
                });
            });

            const res = await fetch('/api/alerts/thresholds/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ items })
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success) throw new Error(data.error || `HTTP ${res.status}`);

            await this.loadThresholds();
            this.setSyncIndicator('Seuils sauvegardés', true);
        } catch (error) {
            console.error('❌ Erreur sauvegarde batch seuils:', error);
            this.setSyncIndicator('Erreur sauvegarde batch: ' + error.message, false);
        }
    }

    async applyDefaultThresholds() {
        try {
            const btn = $('#defaults-thresholds-btn').prop('disabled', true);
            const res = await fetch('/api/alerts/thresholds/reset-defaults', {
                method: 'POST',
                credentials: 'include'
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.error || `HTTP ${res.status}`);
            // Mettre à jour l'affichage
            this.thresholds = data.thresholds || [];
            this.renderThresholds();
            await this.syncSystemConfig();
            this.setSyncIndicator('Seuils par défaut appliqués et synchronisés', true);
        } catch (e) {
            console.error('Erreur défaut seuils:', e);
            this.setSyncIndicator('Erreur défaut seuils: ' + e.message, false);
        } finally {
            $('#defaults-thresholds-btn').prop('disabled', false);
        }
    }

    async syncSystemConfig() {
        try {
            const ind = $('#thresholds-sync-indicator');
            ind.text('Synchronisation…');
            const res = await fetch('/api/alerts/thresholds/sync', {
                method: 'POST',
                credentials: 'include'
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.error || `HTTP ${res.status}`);
            ind.text('Syncé SystemConfig');
        } catch (e) {
            $('#thresholds-sync-indicator').text('Sync échoué');
        }
    }

    setSyncIndicator(message, ok) {
        const ind = $('#thresholds-sync-indicator');
        ind.removeClass('text-success text-danger').addClass(ok ? 'text-success' : 'text-danger').text(message);
        setTimeout(() => ind.text(''), 5000);
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
