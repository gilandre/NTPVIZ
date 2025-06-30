"""
API d'agrgation des logs NTP - Monitoring et contrle
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from backend.services.aggregation_service import aggregation_service
from backend.models.ntp_log_aggregated import AggregationStatus
from backend.decorators import admin_required
import logging

aggregation_bp = Blueprint('aggregation', __name__)
logger = logging.getLogger(__name__)

@aggregation_bp.route('/stats', methods=['GET'])
@login_required
def get_aggregation_stats():
    """Obtenir les statistiques d'agrgation"""
    try:
        stats = aggregation_service.get_aggregation_stats()
        
        # Ajouter des mtriques supplmentaires
        total_aggregated = sum(stat.get('records_aggregated', 0) for stat in stats.values())
        total_purged = sum(stat.get('records_purged', 0) for stat in stats.values())
        
        # Calculer l'tat global
        global_status = 'active'
        last_errors = []
        
        for interval, stat in stats.items():
            if stat.get('status') == 'error':
                global_status = 'error'
                if stat.get('last_error'):
                    last_errors.append(f"{interval}: {stat['last_error']}")
            elif stat.get('status') == 'running':
                global_status = 'running'
        
        return jsonify({
            'status': 'success',
            'data': {
                'intervals': stats,
                'summary': {
                    'total_aggregated': total_aggregated,
                    'total_purged': total_purged,
                    'global_status': global_status,
                    'last_errors': last_errors,
                    'service_running': aggregation_service.is_running
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur rcupration stats agrgation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur rcupration des statistiques: {str(e)}'
        }), 500

@aggregation_bp.route('/force', methods=['POST'])
@login_required
@admin_required
def force_aggregation():
    """Forcer une agrgation immdiate"""
    try:
        data = request.get_json() or {}
        interval = data.get('interval')  # Optionnel : '15min', '30min', etc.
        
        if interval and interval not in aggregation_service.aggregation_intervals:
            return jsonify({
                'status': 'error',
                'message': f'Intervalle non support: {interval}'
            }), 400
        
        # Dmarrer l'agrgation
        result = aggregation_service.force_aggregation(interval)
        
        return jsonify({
            'status': 'success',
            'message': 'Agrgation force avec succs',
            'data': {
                'result': result,
                'forced_by': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur agrgation force: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur lors de l\'agrgation force: {str(e)}'
        }), 500

@aggregation_bp.route('/status', methods=['GET'])
@login_required
def get_service_status():
    """Obtenir le statut du service d'agrgation"""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'service_running': aggregation_service.is_running,
                'intervals_configured': list(aggregation_service.aggregation_intervals.keys()),
                'thread_alive': aggregation_service.aggregation_thread.is_alive() if aggregation_service.aggregation_thread else False
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur statut service agrgation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur rcupration du statut: {str(e)}'
        }), 500

@aggregation_bp.route('/config', methods=['GET'])
@login_required
@admin_required
def get_aggregation_config():
    """Obtenir la configuration d'agrgation"""
    try:
        config = {}
        
        for interval_name, settings in aggregation_service.aggregation_intervals.items():
            config[interval_name] = {
                'minutes': settings['minutes'],
                'retention_days': settings['retention_days'],
                'purge_threshold_hours': settings['purge_threshold_hours'],
                'human_readable': {
                    'interval': f"{settings['minutes']} minutes",
                    'retention': f"{settings['retention_days']} jours",
                    'purge_after': f"{settings['purge_threshold_hours']} heures"
                }
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'intervals': config,
                'service_info': {
                    'description': 'Service d\'agrgation automatique des logs NTP',
                    'purpose': 'Optimisation des performances de la base de donnes',
                    'automation': 'Excution automatique sans intervention humaine'
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur config agrgation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur rcupration de la configuration: {str(e)}'
        }), 500

@aggregation_bp.route('/health', methods=['GET'])
def health_check():
    """Vrification sant du service d'agrgation"""
    try:
        # Vrifications basiques
        checks = {
            'service_running': aggregation_service.is_running,
            'thread_healthy': False,
            'database_accessible': False,
            'recent_activity': False
        }
        
        # Vrifier le thread
        if aggregation_service.aggregation_thread:
            checks['thread_healthy'] = aggregation_service.aggregation_thread.is_alive()
        
        # Vrifier l'accs  la base de donnes
        try:
            statuses = AggregationStatus.query.limit(1).all()
            checks['database_accessible'] = True
            
            # Vrifier l'activit rcente (dernires 24h)
            if statuses:
                recent_activity = any(
                    status.last_aggregated_at and 
                    status.last_aggregated_at > datetime.utcnow() - timedelta(hours=24)
                    for status in statuses
                )
                checks['recent_activity'] = recent_activity
                
        except Exception:
            checks['database_accessible'] = False
        
        # Calculer l'tat global
        health_score = sum(checks.values()) / len(checks) * 100
        overall_health = 'healthy' if health_score >= 75 else 'degraded' if health_score >= 50 else 'unhealthy'
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_health': overall_health,
                'health_score': round(health_score, 1),
                'checks': checks,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur vrification sant agrgation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur vrification sant: {str(e)}'
        }), 500 
