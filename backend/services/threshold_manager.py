"""
Service ThresholdManager - Gestion centralisée des seuils d'alertes
Source unique de vérité pour tous les seuils NTPVIZ
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import and_

from backend.database_manager import get_db_session_with_context
from backend.models.alert_threshold import AlertThreshold
from backend.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

class ThresholdManager:
    """Gestionnaire centralisé des seuils d'alertes"""
    
    def __init__(self):
        self.logger = logger
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 300  # 5 minutes
    
    def get_threshold(self, metric_name: str, server_type: str = 'all') -> Optional[Dict[str, Any]]:
        """
        Récupérer un seuil spécifique
        
        Args:
            metric_name: Nom de la métrique ('offset', 'latency', 'stratum')
            server_type: Type de serveur ('local', 'pool', 'all')
            
        Returns:
            Dictionnaire avec les données du seuil ou None si non trouvé
        """
        try:
            with get_db_session_with_context() as session:
                # Chercher d'abord un seuil spécifique au type de serveur
                threshold = session.query(AlertThreshold).filter(
                    and_(
                        AlertThreshold.metric_name == metric_name,
                        AlertThreshold.server_type == server_type,
                        AlertThreshold.enabled == True
                    )
                ).first()
                
                # Si pas trouvé, chercher un seuil global
                if not threshold:
                    threshold = session.query(AlertThreshold).filter(
                        and_(
                            AlertThreshold.metric_name == metric_name,
                            AlertThreshold.server_type == 'all',
                            AlertThreshold.enabled == True
                        )
                    ).first()
                
                if threshold:
                    # Retourner un dictionnaire pour éviter les problèmes de session
                    return {
                        'id': threshold.id,
                        'metric_name': threshold.metric_name,
                        'server_type': threshold.server_type,
                        'warning_threshold': threshold.warning_threshold,
                        'critical_threshold': threshold.critical_threshold,
                        'unit': threshold.unit,
                        'enabled': threshold.enabled,
                        'description': threshold.description
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur récupération seuil {metric_name}: {e}")
            return None
    
    def get_all_thresholds(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Récupérer tous les seuils avec cache
        
        Args:
            force_refresh: Forcer le rafraîchissement du cache
            
        Returns:
            Liste des seuils actifs
        """
        # Vérifier le cache
        if (not force_refresh and self._cache_timestamp and 
            (datetime.utcnow() - self._cache_timestamp).seconds < self._cache_duration):
            return list(self._cache.values())
        
        try:
            with get_db_session_with_context() as session:
                thresholds = session.query(AlertThreshold).filter_by(enabled=True).all()
                
                # Convertir en dictionnaires pour éviter les problèmes de session
                threshold_dicts = []
                for threshold in thresholds:
                    threshold_dict = {
                        'id': threshold.id,
                        'metric_name': threshold.metric_name,
                        'server_type': threshold.server_type,
                        'warning_threshold': threshold.warning_threshold,
                        'critical_threshold': threshold.critical_threshold,
                        'unit': threshold.unit,
                        'enabled': threshold.enabled,
                        'description': threshold.description
                    }
                    threshold_dicts.append(threshold_dict)
                
                # Mettre à jour le cache
                self._cache = {t['metric_name']: t for t in threshold_dicts}
                self._cache_timestamp = datetime.utcnow()
                
                return threshold_dicts
                
        except Exception as e:
            self.logger.error(f"Erreur récupération tous les seuils: {e}")
            return []
    
    def check_threshold(self, metric_name: str, value: float, server_type: str = 'all') -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Vérifier si une valeur dépasse les seuils
        
        Args:
            metric_name: Nom de la métrique
            value: Valeur à vérifier
            server_type: Type de serveur
            
        Returns:
            Tuple (severity, threshold_dict) où severity est 'ok', 'warning', 'critical'
        """
        threshold_dict = self.get_threshold(metric_name, server_type)
        
        if not threshold_dict:
            return 'ok', None
        
        # Conversion d'unités si nécessaire
        converted_value = self._convert_value(metric_name, value, threshold_dict['unit'])
        
        # Vérification du seuil
        result = self._check_threshold_value(threshold_dict, converted_value)
        
        return result, threshold_dict
    
    def _check_threshold_value(self, threshold_dict: Dict[str, Any], value: float) -> str:
        """
        Vérifier si une valeur dépasse les seuils
        
        Args:
            threshold_dict: Dictionnaire du seuil
            value: Valeur à vérifier
            
        Returns:
            'ok', 'warning', 'critical'
        """
        metric_name = threshold_dict['metric_name']
        warning_threshold = threshold_dict['warning_threshold']
        critical_threshold = threshold_dict['critical_threshold']
        
        if value is None:
            return 'ok'
            
        if metric_name == 'stratum':
            # Pour le stratum, plus c'est élevé, plus c'est mauvais
            if value >= critical_threshold:
                return 'critical'
            elif value >= warning_threshold:
                return 'warning'
        elif metric_name in ['availability']:
            # Pour la disponibilité, moins c'est élevé, plus c'est mauvais
            if value <= critical_threshold:
                return 'critical'
            elif value <= warning_threshold:
                return 'warning'
        else:
            # Pour les autres métriques (offset, latency, etc.), plus c'est élevé, plus c'est mauvais
            if abs(value) >= critical_threshold:
                return 'critical'
            elif abs(value) >= warning_threshold:
                return 'warning'
                
        return 'ok'
    
    def _convert_value(self, metric_name: str, value: float, target_unit: str) -> float:
        """
        Convertir une valeur vers l'unité cible
        
        Args:
            metric_name: Nom de la métrique
            value: Valeur à convertir
            target_unit: Unité cible
            
        Returns:
            Valeur convertie
        """
        if metric_name in ['offset', 'latency']:
            # Les valeurs NTP sont en secondes, convertir en millisecondes si nécessaire
            if target_unit == 'ms':
                return abs(value * 1000)
            elif target_unit == 's':
                return abs(value)
        
        return value
    
    def update_threshold(self, metric_name: str, warning_threshold: float, 
                        critical_threshold: float, unit: str, server_type: str = 'all',
                        description: str = None) -> bool:
        """
        Mettre à jour ou créer un seuil
        
        Args:
            metric_name: Nom de la métrique
            warning_threshold: Seuil d'avertissement
            critical_threshold: Seuil critique
            unit: Unité de mesure
            server_type: Type de serveur
            description: Description du seuil
            
        Returns:
            True si succès, False sinon
        """
        try:
            with get_db_session_with_context() as session:
                # Chercher le seuil existant
                threshold = session.query(AlertThreshold).filter(
                    and_(
                        AlertThreshold.metric_name == metric_name,
                        AlertThreshold.server_type == server_type
                    )
                ).first()
                
                if threshold:
                    # Mise à jour
                    threshold.warning_threshold = warning_threshold
                    threshold.critical_threshold = critical_threshold
                    threshold.unit = unit
                    threshold.updated_at = datetime.utcnow()
                    if description:
                        threshold.description = description
                    
                    self.logger.info(f"Seuil {metric_name} mis à jour: {warning_threshold}/{critical_threshold} {unit}")
                else:
                    # Création
                    threshold = AlertThreshold(
                        metric_name=metric_name,
                        warning_threshold=warning_threshold,
                        critical_threshold=critical_threshold,
                        unit=unit,
                        server_type=server_type,
                        enabled=True,
                        description=description or f"Seuil {metric_name} pour {server_type}"
                    )
                    session.add(threshold)
                    
                    self.logger.info(f"Seuil {metric_name} créé: {warning_threshold}/{critical_threshold} {unit}")
                
                # Synchroniser avec SystemConfig
                self._sync_with_systemconfig(session, metric_name, warning_threshold, critical_threshold)
                
                session.commit()
                
                # Invalider le cache
                self._cache = {}
                self._cache_timestamp = None
                
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur mise à jour seuil {metric_name}: {e}")
            return False
    
    def _sync_with_systemconfig(self, session, metric_name: str, warning_threshold: float, critical_threshold: float):
        """
        Synchroniser avec SystemConfig
        
        Args:
            session: Session de base de données
            metric_name: Nom de la métrique
            warning_threshold: Seuil d'avertissement
            critical_threshold: Seuil critique
        """
        try:
            # Mapping des métriques vers les clés SystemConfig
            config_mapping = {
                'offset': {
                    'warning': 'alerts.offset_warning_threshold',
                    'critical': 'alerts.offset_critical_threshold'
                },
                'latency': {
                    'warning': 'alerts.latency_warning_threshold',
                    'critical': 'alerts.latency_critical_threshold'
                },
                'stratum': {
                    'warning': 'alerts.stratum_max_threshold',
                    'critical': 'alerts.stratum_critical_threshold'
                }
            }
            
            if metric_name in config_mapping:
                mapping = config_mapping[metric_name]
                
                # Conversion d'unités pour SystemConfig
                if metric_name in ['offset', 'latency']:
                    # SystemConfig stocke en millisecondes
                    warning_val = warning_threshold
                    critical_val = critical_threshold
                else:
                    warning_val = warning_threshold
                    critical_val = critical_threshold
                
                # Mettre à jour les clés SystemConfig
                for level, key in mapping.items():
                    config = session.query(SystemConfig).filter_by(key_name=key).first()
                    if config:
                        if level == 'warning':
                            config.value = str(warning_val)
                        else:
                            config.value = str(critical_val)
                        config.updated_at = datetime.utcnow()
                        
                        self.logger.debug(f"SystemConfig {key} synchronisé: {config.value}")
                
        except Exception as e:
            self.logger.error(f"Erreur synchronisation SystemConfig: {e}")
    
    def get_threshold_summary(self) -> Dict[str, Any]:
        """
        Récupérer un résumé de tous les seuils
        
        Returns:
            Dictionnaire avec le résumé des seuils
        """
        thresholds = self.get_all_thresholds()
        
        summary = {
            'total_thresholds': len(thresholds),
            'metrics': {},
            'last_update': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }
        
        for threshold in thresholds:
            if threshold['metric_name'] not in summary['metrics']:
                summary['metrics'][threshold['metric_name']] = []
            
            summary['metrics'][threshold['metric_name']].append({
                'server_type': threshold['server_type'],
                'warning': threshold['warning_threshold'],
                'critical': threshold['critical_threshold'],
                'unit': threshold['unit'],
                'enabled': threshold['enabled'],
                'description': threshold['description']
            })
        
        return summary
    
    def validate_thresholds(self) -> Dict[str, Any]:
        """
        Valider la cohérence des seuils
        
        Returns:
            Dictionnaire avec les résultats de validation
        """
        thresholds = self.get_all_thresholds()
        
        validation = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        for threshold in thresholds:
            # Vérifier que warning < critical
            if threshold['warning_threshold'] >= threshold['critical_threshold']:
                validation['valid'] = False
                validation['issues'].append(
                    f"Seuil {threshold['metric_name']} ({threshold['server_type']}): "
                    f"warning ({threshold['warning_threshold']}) >= critical ({threshold['critical_threshold']})"
                )
            
            # Vérifier les valeurs raisonnables
            if threshold['metric_name'] in ['offset', 'latency']:
                if threshold['warning_threshold'] < 1:
                    validation['warnings'].append(
                        f"Seuil {threshold['metric_name']} warning très bas: {threshold['warning_threshold']}ms"
                    )
                if threshold['critical_threshold'] > 10000:
                    validation['warnings'].append(
                        f"Seuil {threshold['metric_name']} critical très élevé: {threshold['critical_threshold']}ms"
                    )
            
            elif threshold['metric_name'] == 'stratum':
                if threshold['warning_threshold'] < 1:
                    validation['warnings'].append(
                        f"Seuil stratum warning très bas: {threshold['warning_threshold']}"
                    )
                if threshold['critical_threshold'] > 16:
                    validation['warnings'].append(
                        f"Seuil stratum critical très élevé: {threshold['critical_threshold']}"
                    )
        
        return validation

# Instance globale
threshold_manager = ThresholdManager() 