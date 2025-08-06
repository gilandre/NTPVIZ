#!/usr/bin/env python3
"""
Script de migration pour éliminer les redondances de paramétrage des alertes
Standardisation des unités et centralisation des seuils
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database_manager import get_db_session_with_context
from backend.models.alert_threshold import AlertThreshold
from backend.models.system_config import SystemConfig
from backend.models.ntp_server import NTPServer
from backend.config.alert_metrics import get_all_default_thresholds, ALERT_METRICS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_alert_thresholds():
    """Migration des seuils d'alertes - Élimination des redondances"""
    
    logger.info("🚀 Début de la migration des seuils d'alertes...")
    
    try:
        with get_db_session_with_context() as session:
            
            # Phase 1: Supprimer les configurations redondantes de system_config
            logger.info("📋 Phase 1: Suppression des configurations redondantes...")
            redundant_configs = [
                'ntp.max_offset_warning',
                'ntp.max_offset_critical',
                'alerts.offset_threshold',
                'alerts.latency_threshold'
            ]
            
            for config_key in redundant_configs:
                config = session.query(SystemConfig).filter_by(key_name=config_key).first()
                if config:
                    logger.info(f"🗑️ Suppression de la configuration redondante: {config_key}")
                    session.delete(config)
            
            # Phase 2: Standardiser les unités dans alert_thresholds
            logger.info("📋 Phase 2: Standardisation des unités...")
            thresholds = session.query(AlertThreshold).all()
            
            for threshold in thresholds:
                metric_config = ALERT_METRICS.get(threshold.metric_name, {})
                if metric_config:
                    # Mettre à jour l'unité
                    new_unit = metric_config.get('unit', 'ms')
                    if threshold.unit != new_unit:
                        logger.info(f"🔄 Mise à jour unité {threshold.metric_name}: {threshold.unit} -> {new_unit}")
                        threshold.unit = new_unit
                    
                    # Convertir les valeurs si nécessaire
                    if threshold.metric_name in ['offset', 'latency'] and threshold.unit == 'ms':
                        # Les valeurs sont déjà en ms dans alert_thresholds
                        pass
                    elif threshold.metric_name == 'stratum':
                        # Vérifier que les valeurs sont des entiers
                        threshold.warning_threshold = int(threshold.warning_threshold)
                        threshold.critical_threshold = int(threshold.critical_threshold)
            
            # Phase 3: Créer les seuils par défaut manquants
            logger.info("📋 Phase 3: Création des seuils par défaut...")
            default_thresholds = get_all_default_thresholds()
            
            for threshold_data in default_thresholds:
                existing = session.query(AlertThreshold).filter_by(
                    metric_name=threshold_data['metric_name'],
                    server_type=threshold_data['server_type']
                ).first()
                
                if not existing:
                    logger.info(f"➕ Création du seuil par défaut: {threshold_data['metric_name']} ({threshold_data['server_type']})")
                    new_threshold = AlertThreshold(**threshold_data)
                    session.add(new_threshold)
            
            # Phase 4: Vérifier la cohérence des données
            logger.info("📋 Phase 4: Vérification de la cohérence...")
            
            # Compter les seuils par métrique
            for metric_name in ALERT_METRICS.keys():
                count = session.query(AlertThreshold).filter_by(metric_name=metric_name).count()
                logger.info(f"📊 Métrique {metric_name}: {count} seuils configurés")
            
            # Compter les seuils par type de serveur
            for server_type in ['local', 'pool', 'internet', 'all']:
                count = session.query(AlertThreshold).filter_by(server_type=server_type).count()
                logger.info(f"📊 Type serveur {server_type}: {count} seuils configurés")
            
            session.commit()
            logger.info("✅ Migration terminée avec succès!")
            
            # Phase 5: Rapport final
            logger.info("📋 Phase 5: Rapport final...")
            total_thresholds = session.query(AlertThreshold).count()
            active_thresholds = session.query(AlertThreshold).filter_by(enabled=True).count()
            
            logger.info(f"📊 Total des seuils: {total_thresholds}")
            logger.info(f"📊 Seuils actifs: {active_thresholds}")
            logger.info(f"📊 Seuils inactifs: {total_thresholds - active_thresholds}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        return False

def verify_migration():
    """Vérifier que la migration s'est bien passée"""
    
    logger.info("🔍 Vérification de la migration...")
    
    try:
        with get_db_session_with_context() as session:
            
            # Vérifier que les configurations redondantes ont été supprimées
            redundant_configs = [
                'ntp.max_offset_warning',
                'ntp.max_offset_critical'
            ]
            
            for config_key in redundant_configs:
                config = session.query(SystemConfig).filter_by(key_name=config_key).first()
                if config:
                    logger.warning(f"⚠️ Configuration redondante encore présente: {config_key}")
                else:
                    logger.info(f"✅ Configuration redondante supprimée: {config_key}")
            
            # Vérifier que tous les seuils ont les bonnes unités
            thresholds = session.query(AlertThreshold).all()
            for threshold in thresholds:
                metric_config = ALERT_METRICS.get(threshold.metric_name, {})
                expected_unit = metric_config.get('unit', 'ms')
                
                if threshold.unit != expected_unit:
                    logger.warning(f"⚠️ Unité incorrecte pour {threshold.metric_name}: {threshold.unit} (attendu: {expected_unit})")
                else:
                    logger.info(f"✅ Unité correcte pour {threshold.metric_name}: {threshold.unit}")
            
            # Vérifier que tous les seuils par défaut existent
            default_thresholds = get_all_default_thresholds()
            missing_thresholds = []
            
            for threshold_data in default_thresholds:
                existing = session.query(AlertThreshold).filter_by(
                    metric_name=threshold_data['metric_name'],
                    server_type=threshold_data['server_type']
                ).first()
                
                if not existing:
                    missing_thresholds.append(f"{threshold_data['metric_name']} ({threshold_data['server_type']})")
            
            if missing_thresholds:
                logger.warning(f"⚠️ Seuils par défaut manquants: {', '.join(missing_thresholds)}")
            else:
                logger.info("✅ Tous les seuils par défaut sont présents")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

def cleanup_old_references():
    """Nettoyer les références aux anciens champs dans le code"""
    
    logger.info("🧹 Nettoyage des références obsolètes...")
    
    # Liste des fichiers à vérifier et corriger
    files_to_check = [
        'backend/models/ntp_server.py',
        'backend/services/alert_service.py',
        'backend/api/admin.py',
        'backend/api/ntp.py'
    ]
    
    # Patterns à rechercher et remplacer
    replacements = [
        # Remplacer les références aux champs supprimés
        ('server.max_offset', 'threshold_manager.get_threshold("offset", server_type)'),
        ('server.critical_offset', 'threshold_manager.get_threshold("offset", server_type)'),
        
        # Remplacer les références aux configurations supprimées
        ('SystemConfig.get_config("ntp.max_offset_warning")', 'threshold_manager.get_threshold("offset", "all")'),
        ('SystemConfig.get_config("ntp.max_offset_critical")', 'threshold_manager.get_threshold("offset", "all")'),
        
        # Standardiser les unités dans les messages
        ('secondes', 'millisecondes'),
        ('(s)', '(ms)')
    ]
    
    logger.info("📝 Fichiers à vérifier manuellement:")
    for file_path in files_to_check:
        logger.info(f"   - {file_path}")
    
    logger.info("🔄 Patterns à remplacer:")
    for old_pattern, new_pattern in replacements:
        logger.info(f"   - '{old_pattern}' -> '{new_pattern}'")
    
    return True

if __name__ == "__main__":
    logger.info("🔧 Script de migration des seuils d'alertes")
    logger.info("=" * 50)
    
    # Exécuter la migration
    if migrate_alert_thresholds():
        logger.info("✅ Migration réussie!")
        
        # Vérifier la migration
        if verify_migration():
            logger.info("✅ Vérification réussie!")
            
            # Nettoyer les références
            if cleanup_old_references():
                logger.info("✅ Nettoyage des références terminé!")
                logger.info("🎉 Migration complète terminée avec succès!")
            else:
                logger.error("❌ Erreur lors du nettoyage des références")
        else:
            logger.error("❌ Erreur lors de la vérification")
    else:
        logger.error("❌ Erreur lors de la migration")
    
    logger.info("=" * 50) 