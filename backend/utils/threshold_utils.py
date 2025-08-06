
"""
Fonctions utilitaires pour la gestion des seuils
"""
from backend.config.alert_metrics import ALERT_METRICS
from backend.services.threshold_manager import threshold_manager

def get_threshold_value(metric_name, server_type='all', threshold_type='warning'):
    """Récupérer une valeur de seuil depuis la configuration"""
    try:
        threshold = threshold_manager.get_threshold(metric_name, server_type)
        if threshold:
            return threshold.get(f'{threshold_type}_threshold', 0)
        else:
            # Fallback vers la configuration par défaut
            metric_config = ALERT_METRICS.get(metric_name, {})
            return metric_config.get(f'default_{threshold_type}', 0)
    except Exception as e:
        print(f"Erreur récupération seuil {metric_name}: {e}")
        return 0

def get_min_threshold(metric_name):
    """Récupérer le seuil minimum pour une métrique"""
    metric_config = ALERT_METRICS.get(metric_name, {})
    return metric_config.get('min_value', 0)

def get_max_threshold(metric_name):
    """Récupérer le seuil maximum pour une métrique"""
    metric_config = ALERT_METRICS.get(metric_name, {})
    return metric_config.get('max_value', 1000)

def validate_threshold_value(metric_name, value):
    """Valider une valeur de seuil"""
    metric_config = ALERT_METRICS.get(metric_name, {})
    min_val = metric_config.get('min_value', 0)
    max_val = metric_config.get('max_value', 1000)
    
    return min_val <= value <= max_val

def format_threshold_message(metric_name, value, severity):
    """Formater un message de seuil"""
    metric_config = ALERT_METRICS.get(metric_name, {})
    unit = metric_config.get('unit', 'ms')
    label = metric_config.get('label', metric_name)
    
    return f"{label} {severity}: {value:.2f}{unit}"
