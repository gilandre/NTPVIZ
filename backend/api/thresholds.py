"""
API pour la gestion unifiée des seuils d'alertes
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime

from backend.database_manager import get_db_session_with_context
from backend.services.threshold_manager import threshold_manager
from backend.decorators import config_required
from backend.models.alert_threshold import AlertThreshold

thresholds_bp = Blueprint('thresholds', __name__)

@thresholds_bp.route('/thresholds', methods=['GET'])
@login_required
def get_thresholds():
    """Récupérer tous les seuils d'alertes"""
    try:
        thresholds = threshold_manager.get_all_thresholds()
        
        # Les seuils sont déjà des dictionnaires, pas besoin de conversion
        result = []
        for threshold in thresholds:
            result.append({
                'id': threshold['id'],
                'metric_name': threshold['metric_name'],
                'server_type': threshold['server_type'],
                'warning_threshold': threshold['warning_threshold'],
                'critical_threshold': threshold['critical_threshold'],
                'unit': threshold['unit'],
                'enabled': threshold['enabled'],
                'description': threshold['description'],
                # Libellés facultatifs si fournis par le manager
                'metric_label': threshold.get('metric_label', threshold['metric_name']),
                'server_type_label': threshold.get('server_type_label', threshold['server_type'])
            })
        
        return jsonify({
            'success': True,
            'thresholds': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur récupération seuils: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/<metric_name>', methods=['GET'])
@login_required
def get_threshold(metric_name):
    """Récupérer un seuil spécifique"""
    try:
        server_type = request.args.get('server_type', 'all')
        threshold = threshold_manager.get_threshold(metric_name, server_type)
        
        if not threshold:
            return jsonify({
                'success': False,
                'error': f'Seuil non trouvé pour {metric_name} ({server_type})'
            }), 404
        
        return jsonify({
            'success': True,
            'threshold': {
                'id': threshold['id'],
                'metric_name': threshold['metric_name'],
                'server_type': threshold['server_type'],
                'warning_threshold': threshold['warning_threshold'],
                'critical_threshold': threshold['critical_threshold'],
                'unit': threshold['unit'],
                'enabled': threshold['enabled'],
                'description': threshold['description']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur récupération seuil: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds', methods=['POST'])
@login_required
@config_required
def create_threshold():
    """Créer un nouveau seuil"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
        
        # Validation des données
        required_fields = ['metric_name', 'warning_threshold', 'critical_threshold', 'unit']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Validation des valeurs
        # Pour les métriques de pourcentage (comme availability), warning > critical est logique
        if data['unit'] == '%':
            # Pour les pourcentages, warning doit être supérieur à critical
            if data['warning_threshold'] <= data['critical_threshold']:
                return jsonify({
                    'success': False,
                    'error': 'Pour les pourcentages, le seuil d\'avertissement doit être supérieur au seuil critique'
                }), 400
        elif data['unit'] == 'bool':
            # Pour les métriques booléennes, warning et critical peuvent être égaux
            # Pas de validation spéciale nécessaire
            pass
        else:
            # Pour les autres métriques, warning doit être inférieur à critical
            if data['warning_threshold'] >= data['critical_threshold']:
                return jsonify({
                    'success': False,
                    'error': 'Le seuil d\'avertissement doit être inférieur au seuil critique'
                }), 400
        
        # Créer le seuil
        success = threshold_manager.update_threshold(
            metric_name=data['metric_name'],
            warning_threshold=float(data['warning_threshold']),
            critical_threshold=float(data['critical_threshold']),
            unit=data['unit'],
            server_type=data.get('server_type', 'all'),
            description=data.get('description')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Seuil {data["metric_name"]} créé avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la création du seuil'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur création seuil: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/<int:threshold_id>', methods=['PUT'])
@login_required
@config_required
def update_threshold(threshold_id):
    """Mettre à jour un seuil existant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
        
        with get_db_session_with_context() as session:
            threshold = session.query(AlertThreshold).filter_by(id=threshold_id).first()
            if not threshold:
                return jsonify({
                    'success': False,
                    'error': 'Seuil non trouvé'
                }), 404
            
            # Mise à jour des champs
            if 'warning_threshold' in data:
                threshold.warning_threshold = float(data['warning_threshold'])
            if 'critical_threshold' in data:
                threshold.critical_threshold = float(data['critical_threshold'])
            if 'unit' in data:
                threshold.unit = data['unit']
            if 'enabled' in data:
                threshold.enabled = bool(data['enabled'])
            if 'description' in data:
                threshold.description = data['description']
            
            threshold.updated_at = datetime.utcnow()
            
            # Validation
            # Pour les métriques de pourcentage (comme availability), warning > critical est logique
            if threshold.unit == '%':
                # Pour les pourcentages, warning doit être supérieur à critical
                if threshold.warning_threshold <= threshold.critical_threshold:
                    return jsonify({
                        'success': False,
                        'error': 'Pour les pourcentages, le seuil d\'avertissement doit être supérieur au seuil critique'
                    }), 400
            elif threshold.unit == 'bool':
                # Pour les métriques booléennes, warning et critical peuvent être égaux
                # Pas de validation spéciale nécessaire
                pass
            else:
                # Pour les autres métriques, warning doit être inférieur à critical
                if threshold.warning_threshold >= threshold.critical_threshold:
                    return jsonify({
                        'success': False,
                        'error': 'Le seuil d\'avertissement doit être inférieur au seuil critique'
                    }), 400
            
            # Synchroniser avec SystemConfig
            threshold_manager._sync_with_systemconfig(
                session, str(threshold.metric_name), 
                float(threshold.warning_threshold), float(threshold.critical_threshold)
            )
            
            session.commit()
            
            # Invalider le cache
            threshold_manager._cache = {}
            threshold_manager._cache_timestamp = None
            
            return jsonify({
                'success': True,
                'message': f'Seuil {threshold.metric_name} mis à jour avec succès'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur mise à jour seuil: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/<int:threshold_id>', methods=['DELETE'])
@login_required
@config_required
def delete_threshold(threshold_id):
    """Supprimer un seuil"""
    try:
        with get_db_session_with_context() as session:
            threshold = session.query(AlertThreshold).filter_by(id=threshold_id).first()
            if not threshold:
                return jsonify({
                    'success': False,
                    'error': 'Seuil non trouvé'
                }), 404
            
            metric_name = threshold.metric_name
            session.delete(threshold)
            session.commit()
            
            # Invalider le cache
            threshold_manager._cache = {}
            threshold_manager._cache_timestamp = None
            
            return jsonify({
                'success': True,
                'message': f'Seuil {metric_name} supprimé avec succès'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur suppression seuil: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/summary', methods=['GET'])
@login_required
def get_threshold_summary():
    """Récupérer un résumé des seuils"""
    try:
        summary = threshold_manager.get_threshold_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur récupération résumé: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/validate', methods=['GET'])
@login_required
def validate_thresholds():
    """Valider la cohérence des seuils"""
    try:
        validation = threshold_manager.validate_thresholds()
        return jsonify({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur validation seuils: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/test', methods=['POST'])
@login_required
def test_threshold():
    """Tester un seuil avec une valeur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
        
        metric_name = data.get('metric_name')
        value = data.get('value')
        server_type = data.get('server_type', 'all')
        
        if not metric_name or value is None:
            return jsonify({
                'success': False,
                'error': 'metric_name et value sont requis'
            }), 400
        
        severity, threshold = threshold_manager.check_threshold(metric_name, float(value), server_type)
        
        return jsonify({
            'success': True,
            'result': {
                'metric_name': metric_name,
                'value': value,
                'server_type': server_type,
                'severity': severity,
                'threshold': {
                    'warning': threshold['warning_threshold'] if threshold else None,
                    'critical': threshold['critical_threshold'] if threshold else None,
                    'unit': threshold['unit'] if threshold else None
                } if threshold else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur test seuil: {str(e)}'
        }), 500

@thresholds_bp.route('/thresholds/sync', methods=['POST'])
@login_required
@config_required
def sync_thresholds():
    """Synchroniser tous les seuils avec SystemConfig"""
    try:
        with get_db_session_with_context() as session:
            thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
            
            synced_count = 0
            for threshold in thresholds:
                threshold_manager._sync_with_systemconfig(
                    session, str(threshold.metric_name),
                    float(threshold.warning_threshold), float(threshold.critical_threshold)
                )
                synced_count += 1
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'{synced_count} seuils synchronisés avec SystemConfig'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur synchronisation: {str(e)}'
        }), 500 

@thresholds_bp.route('/thresholds/reset-defaults', methods=['POST'])
@login_required
@config_required
def reset_default_thresholds():
    """Réinitialiser/Créer les seuils par défaut puis renvoyer la liste à jour."""
    try:
        with get_db_session_with_context() as session:
            threshold_manager._create_default_thresholds_internal(session)
            session.commit()
        # Forcer rafraîchissement et normalisation/harmonisation
        threshold_manager.normalize_and_harmonize(harmonize=True)
        thresholds = threshold_manager.get_all_thresholds(force_refresh=True)
        return jsonify({
            'success': True,
            'message': 'Seuils par défaut appliqués',
            'thresholds': thresholds,
            'total': len(thresholds)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur réinitialisation seuils: {str(e)}'
        }), 500