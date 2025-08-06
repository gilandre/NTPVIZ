"""
Configuration centralisée des métriques d'alertes
Élimination des redondances et standardisation des unités
"""

# Configuration centralisée des métriques d'alertes
ALERT_METRICS = {
    'offset': {
        'label': 'Écart de synchronisation',
        'unit': 'ms',
        'default_warning': 1000,
        'default_critical': 5000,
        'description': 'Écart de synchronisation en millisecondes',
        'conversion_factor': 1000,  # secondes -> millisecondes
        'min_value': 0,
        'max_value': 60000,  # 60 secondes max
        'validation': lambda x: 0 <= abs(x) <= 60000
    },
    'latency': {
        'label': 'Délai de réponse',
        'unit': 'ms',
        'default_warning': 100,
        'default_critical': 500,
        'description': 'Délai de réponse en millisecondes',
        'conversion_factor': 1000,  # secondes -> millisecondes
        'min_value': 0,
        'max_value': 30000,  # 30 secondes max
        'validation': lambda x: 0 <= abs(x) <= 30000
    },
    'stratum': {
        'label': 'Précision (stratum)',
        'unit': 'level',
        'default_warning': 4,
        'default_critical': 8,
        'description': 'Niveau de précision du serveur',
        'conversion_factor': 1,  # pas de conversion
        'min_value': 0,
        'max_value': 16,
        'validation': lambda x: 0 <= int(x) <= 16
    },
    'availability': {
        'label': 'Disponibilité',
        'unit': '%',
        'default_warning': 95,
        'default_critical': 80,
        'description': 'Pourcentage de disponibilité',
        'conversion_factor': 1,  # pas de conversion
        'min_value': 0,
        'max_value': 100,
        'validation': lambda x: 0 <= float(x) <= 100
    },
    'internet': {
        'label': 'Connexion internet',
        'unit': 'bool',
        'default_warning': 0,
        'default_critical': 0,
        'description': 'État de la connexion internet',
        'conversion_factor': 1,  # pas de conversion
        'min_value': 0,
        'max_value': 1,
        'validation': lambda x: x in [0, 1, True, False]
    }
}

# Types de serveurs supportés
SERVER_TYPES = {
    'local': {
        'label': 'Serveurs locaux',
        'description': 'Serveurs NTP locaux',
        'default_metrics': ['offset', 'latency', 'stratum']
    },
    'pool': {
        'label': 'Pools NTP',
        'description': 'Pools de serveurs NTP',
        'default_metrics': ['offset', 'latency', 'stratum']
    },
    'internet': {
        'label': 'Serveurs internet',
        'description': 'Serveurs NTP internet',
        'default_metrics': ['offset', 'latency', 'stratum', 'availability']
    },
    'all': {
        'label': 'Tous les serveurs',
        'description': 'Tous les types de serveurs',
        'default_metrics': ['offset', 'latency', 'stratum', 'availability', 'internet']
    }
}

def get_metric_config(metric_name):
    """Récupérer la configuration d'une métrique"""
    return ALERT_METRICS.get(metric_name, {})

def get_server_type_config(server_type):
    """Récupérer la configuration d'un type de serveur"""
    return SERVER_TYPES.get(server_type, {})

def convert_to_standard_unit(value, metric_name):
    """Convertir une valeur vers l'unité standard"""
    metric_config = get_metric_config(metric_name)
    if not metric_config:
        return value
    
    conversion_factor = metric_config.get('conversion_factor', 1)
    unit = metric_config.get('unit', 'ms')
    
    # Conversion selon le type d'unité
    if unit == 'ms' and metric_name in ['offset', 'latency']:
        return abs(float(value) * conversion_factor)  # secondes -> millisecondes
    elif unit == 'level':
        return int(value)  # stratum
    elif unit == '%':
        return float(value)  # disponibilité
    elif unit == 'bool':
        return bool(value)  # internet
    else:
        return abs(float(value))

def validate_metric_value(value, metric_name):
    """Valider une valeur de métrique"""
    metric_config = get_metric_config(metric_name)
    if not metric_config:
        return True
    
    validation_func = metric_config.get('validation')
    if validation_func:
        try:
            return validation_func(value)
        except (ValueError, TypeError):
            return False
    
    return True

def get_default_thresholds(metric_name, server_type='all'):
    """Récupérer les seuils par défaut pour une métrique"""
    metric_config = get_metric_config(metric_name)
    if not metric_config:
        return None
    
    return {
        'metric_name': metric_name,
        'server_type': server_type,
        'warning_threshold': metric_config.get('default_warning', 0),
        'critical_threshold': metric_config.get('default_critical', 0),
        'unit': metric_config.get('unit', 'ms'),
        'enabled': True,
        'description': metric_config.get('description', '')
    }

def get_all_default_thresholds():
    """Récupérer tous les seuils par défaut"""
    thresholds = []
    
    for metric_name in ALERT_METRICS.keys():
        for server_type in SERVER_TYPES.keys():
            threshold = get_default_thresholds(metric_name, server_type)
            if threshold:
                thresholds.append(threshold)
    
    return thresholds

def format_alert_message(metric_name, value, severity, threshold):
    """Formater un message d'alerte"""
    metric_config = get_metric_config(metric_name)
    if not metric_config:
        return f"Seuil {severity}: {value}"
    
    unit = metric_config.get('unit', 'ms')
    label = metric_config.get('label', metric_name)
    
    if unit == 'ms':
        return f"{label} {severity}: {value:.2f}ms (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']}ms)"
    elif unit == 'level':
        return f"{label} {severity}: {value} (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']})"
    elif unit == '%':
        return f"{label} {severity}: {value:.1f}% (seuils: {threshold['warning_threshold']}/{threshold['critical_threshold']}%)"
    elif unit == 'bool':
        status = "Connecté" if value else "Déconnecté"
        return f"{label} {severity}: {status}"
    else:
        return f"{label} {severity}: {value}"

def get_metric_label(metric_name):
    """Récupérer le label d'une métrique"""
    metric_config = get_metric_config(metric_name)
    return metric_config.get('label', metric_name) if metric_config else metric_name

def get_server_type_label(server_type):
    """Récupérer le label d'un type de serveur"""
    server_config = get_server_type_config(server_type)
    return server_config.get('label', server_type) if server_config else server_type 