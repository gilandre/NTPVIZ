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
    """Obtenir les statistiques d'agrégation"""
    try:
        # Récupérer les paramètres de la requête
        interval = request.args.get('interval', '24hours')
        hours = int(request.args.get('hours', 24))
        
        # Obtenir les statistiques d'agrégation
        stats_data = aggregation_service.get_aggregation_stats(interval, hours)
        
        # Obtenir le statut du service
        status_data = aggregation_service.get_aggregation_status()
        
        # Gérer le cas où il n'y a pas de données
        if stats_data is None:
            stats_data = []
        
        # Gérer le cas où le statut est un dictionnaire avec une erreur
        if isinstance(status_data, dict) and 'error' in status_data:
            service_status = {
                'is_running': aggregation_service.is_running,
                'error': status_data['error']
            }
        else:
            service_status = status_data
        
        return jsonify({
            'success': True,
            'data': {
                'interval': interval,
                'hours': hours,
                'records_count': len(stats_data),
                'records': stats_data,
                'service_status': service_status,
                'service_running': aggregation_service.is_running
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération stats agrégation: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur récupération des statistiques: {str(e)}'
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
    """Obtenir la configuration d'agrégation"""
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
            'success': True,
            'data': {
                'intervals': config,
                'service_info': {
                    'description': 'Service d\'agrégation automatique des logs NTP',
                    'purpose': 'Optimisation des performances de la base de données',
                    'automation': 'Exécution automatique sans intervention humaine'
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur config agrégation: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur récupération de la configuration: {str(e)}'
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
