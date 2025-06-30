"""
Service NTP - Gestion des requêtes et surveillance des serveurs NTP
VERSION MYSQL - Utilise le Database Manager centralisé
"""
import ntplib
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from backend.database_manager import db_manager, get_db_session_with_context
from backend.models.ntp_server import NTPServer
from backend.models.ntp_log import NTPLog
from backend.models.system_config import SystemConfig
from backend.services.alert_service import alert_service

logger = logging.getLogger(__name__)

class NTPService:
    """Service de gestion NTP avec Database Manager MySQL"""
    
    def __init__(self):
        self.client = ntplib.NTPClient()
        self.logger = logger
    
    def query_server(self, server: NTPServer, timeout: float = None) -> Dict:
        """
        Interroger un serveur NTP
        
        Args:
            server: Serveur NTP à interroger
            timeout: Timeout en secondes
            
        Returns:
            Dictionnaire avec les résultats de la requête
        """
        if timeout is None:
            timeout = server.timeout or 10
            
        result = {
            'server_id': server.id,
            'server_name': server.name,
            'server_address': server.address,
            'timestamp': datetime.utcnow(),
            'success': False,
            'error': None,
            'offset': None,
            'delay': None,
            'stratum': None,
            'precision': None,
            'root_delay': None,
            'root_dispersion': None,
            'ref_id': None,
            'ref_timestamp': None,
            'orig_timestamp': None,
            'recv_timestamp': None,
            'tx_timestamp': None
        }
        
        # Nettoyer l'adresse IP pour éviter les caractères parasites
        clean_address = server.address.strip().replace('\r', '').replace('\n', '') if server.address else server.address
        
        try:
            self.logger.debug(f"Requête NTP vers {server.name} ({clean_address})")
            
            # Effectuer la requête NTP
            response = self.client.request(
                clean_address,
                port=server.port,
                timeout=timeout
            )
            
            # Extraire les données de la réponse
            result.update({
                'success': True,
                'offset': response.offset,
                'delay': response.delay,
                'stratum': response.stratum,
                'precision': response.precision,
                'root_delay': response.root_delay,
                'root_dispersion': response.root_dispersion,
                'ref_id': response.ref_id,
                'ref_timestamp': datetime.fromtimestamp(response.ref_time) if response.ref_time else None,
                'orig_timestamp': datetime.fromtimestamp(response.orig_time) if response.orig_time else None,
                'recv_timestamp': datetime.fromtimestamp(response.recv_time) if response.recv_time else None,
                'tx_timestamp': datetime.fromtimestamp(response.tx_time) if response.tx_time else None
            })
            
            # Vérifier les seuils et créer des alertes si nécessaire
            self._check_thresholds(server, result)
            
            # Mettre à jour le statut du serveur
            self._update_server_status(server, result)
            
            self.logger.debug(f"Requête NTP réussie: {server.name} - Offset: {response.offset:.3f}s")
            
        except socket.timeout:
            error_msg = f"Timeout lors de la requête vers {clean_address}"
            result['error'] = error_msg
            self.logger.warning(error_msg)
            
            # Créer une alerte de disponibilité
            alert_service.check_server_availability(server, False, error_msg)
            
        except socket.gaierror as e:
            error_msg = f"Erreur DNS pour {clean_address}: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg)
            
            # Créer une alerte de disponibilité
            alert_service.check_server_availability(server, False, error_msg)
            
        except Exception as e:
            error_msg = f"Erreur NTP pour {clean_address}: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg)
            
            # Créer une alerte de disponibilité
            alert_service.check_server_availability(server, False, error_msg)
        
        return result
    
    def _check_thresholds(self, server: NTPServer, result: Dict):
        """
        Vérifier les seuils et créer des alertes si nécessaire
        
        Args:
            server: Serveur NTP
            result: Résultat de la requête
        """
        try:
            if not result['success']:
                return
            
            # Utiliser le service d'alertes avec contexte MySQL
            alert_service.check_ntp_threshold(
                server=server,
                offset=result['offset'],
                delay=result['delay'],
                stratum=result['stratum']
            )
            
            # Si tout va bien, marquer le serveur comme disponible
            alert_service.check_server_availability(server, True)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des seuils: {e}")
    
    def _update_server_status(self, server: NTPServer, result: Dict):
        """
        Mettre à jour le statut du serveur avec Database Manager MySQL
        
        Args:
            server: Serveur NTP
            result: Résultat de la requête
        """
        try:
            # Utiliser le database manager avec contexte Flask
            with get_db_session_with_context() as session:
                # Récupérer le serveur dans cette session MySQL
                server_instance = session.get(NTPServer, server.id)
                if not server_instance:
                    return
                
                # Mettre à jour le statut et la dernière vérification
                server_instance.status = 'online' if result['success'] else 'offline'
                server_instance.last_check = result['timestamp']
                
                if result['success']:
                    server_instance.last_successful_check = result['timestamp']
                    server_instance.last_error = None
                else:
                    server_instance.last_error = result.get('error', 'Erreur inconnue')
                
                # La session sera automatiquement committée par le context manager
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour du statut: {e}")
    
    def query_all_servers(self, active_only: bool = True) -> List[Dict]:
        """
        Interroger tous les serveurs NTP
        
        Args:
            active_only: Interroger seulement les serveurs actifs
            
        Returns:
            Liste des résultats de requêtes
        """
        try:
            # Récupérer les serveurs avec Database Manager
            with get_db_session_with_context() as session:
                query = session.query(NTPServer)
                if active_only:
                    query = query.filter_by(is_active=True)
                
                servers = query.all()
            
            if not servers:
                self.logger.warning("Aucun serveur NTP configuré")
                return []
            
            self.logger.info(f"Interrogation de {len(servers)} serveurs NTP")
            
            results = []
            
            # Utiliser ThreadPoolExecutor pour les requêtes parallèles
            with ThreadPoolExecutor(max_workers=min(len(servers), 10)) as executor:
                # Soumettre toutes les requêtes
                future_to_server = {
                    executor.submit(self.query_server, server): server 
                    for server in servers
                }
                
                # Collecter les résultats
                for future in as_completed(future_to_server):
                    server = future_to_server[future]
                    try:
                        result = future.result(timeout=30)
                        results.append(result)
                        
                        # Enregistrer le log NTP
                        self._log_ntp_query(result)
                        
                    except Exception as e:
                        self.logger.error(f"Erreur requête serveur {server.name}: {e}")
                        # Créer un résultat d'erreur
                        error_result = {
                            'server_id': server.id,
                            'server_name': server.name,
                            'server_address': server.address,
                            'timestamp': datetime.utcnow(),
                            'success': False,
                            'error': str(e)
                        }
                        results.append(error_result)
                        self._log_ntp_query(error_result)
            
            self.logger.info(f"Requêtes NTP terminées: {len(results)} résultats")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'interrogation des serveurs: {e}")
            return []
    
    def _log_ntp_query(self, result: Dict):
        """
        Enregistrer un log NTP avec Database Manager MySQL
        
        Args:
            result: Résultat de la requête NTP
        """
        try:
            # Utiliser le database manager pour l'enregistrement
            with get_db_session_with_context() as session:
                log_entry = NTPLog(
                    server_id=result['server_id'],
                    timestamp=result['timestamp'],
                    success=result['success'],
                    offset=result.get('offset'),
                    delay=result.get('delay'),
                    stratum=result.get('stratum'),
                    precision=result.get('precision'),
                    root_delay=result.get('root_delay'),
                    root_dispersion=result.get('root_dispersion'),
                    error_message=result.get('error')
                )
                
                session.add(log_entry)
                # La session sera automatiquement committée
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du log: {e}")
    
    def get_server_statistics(self, server_id: int, hours: int = 24) -> Dict:
        """
        Obtenir les statistiques d'un serveur
        
        Args:
            server_id: ID du serveur
            hours: Nombre d'heures à analyser
            
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            server = NTPServer.query.get(server_id)
            if not server:
                return {}
            
            # Période d'analyse
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Requêtes dans la période
            logs = NTPLog.query.filter(
                NTPLog.server_id == server_id,
                NTPLog.timestamp >= since
            ).order_by(NTPLog.timestamp.desc()).all()
            
            if not logs:
                return {
                    'server_id': server_id,
                    'server_name': server.name,
                    'period_hours': hours,
                    'total_queries': 0,
                    'successful_queries': 0,
                    'failed_queries': 0,
                    'availability_percent': 0.0,
                    'avg_offset': None,
                    'avg_delay': None,
                    'min_offset': None,
                    'max_offset': None,
                    'last_update': None
                }
            
            # Calculer les statistiques
            successful_logs = [log for log in logs if log.success]
            failed_logs = [log for log in logs if not log.success]
            
            offsets = [log.offset for log in successful_logs if log.offset is not None]
            delays = [log.delay for log in successful_logs if log.delay is not None]
            
            stats = {
                'server_id': server_id,
                'server_name': server.name,
                'period_hours': hours,
                'total_queries': len(logs),
                'successful_queries': len(successful_logs),
                'failed_queries': len(failed_logs),
                'availability_percent': (len(successful_logs) / len(logs)) * 100 if logs else 0,
                'avg_offset': sum(offsets) / len(offsets) if offsets else None,
                'avg_delay': sum(delays) / len(delays) if delays else None,
                'min_offset': min(offsets) if offsets else None,
                'max_offset': max(offsets) if offsets else None,
                'last_update': logs[0].timestamp if logs else None
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return {}
    
    def get_global_statistics(self, hours: int = 24) -> Dict:
        """
        Obtenir les statistiques globales
        
        Args:
            hours: Nombre d'heures à analyser
            
        Returns:
            Dictionnaire avec les statistiques globales
        """
        try:
            # Période d'analyse
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Serveurs actifs
            active_servers = NTPServer.query.filter_by(is_active=True).all()
            
            # Logs dans la période
            total_logs = NTPLog.query.filter(NTPLog.timestamp >= since).count()
            successful_logs = NTPLog.query.filter(
                NTPLog.timestamp >= since,
                NTPLog.success == True
            ).count()
            
            # Serveurs en ligne
            online_servers = len([s for s in active_servers if s.status == 'online'])
            
            # Alertes actives
            from backend.models.alert import Alert
            active_alerts = Alert.query.filter_by(status='active').count()
            critical_alerts = Alert.query.filter_by(status='active', severity='critical').count()
            
            stats = {
                'period_hours': hours,
                'total_servers': len(active_servers),
                'online_servers': online_servers,
                'offline_servers': len(active_servers) - online_servers,
                'total_queries': total_logs,
                'successful_queries': successful_logs,
                'failed_queries': total_logs - successful_logs,
                'global_availability': (successful_logs / total_logs * 100) if total_logs > 0 else 0,
                'active_alerts': active_alerts,
                'critical_alerts': critical_alerts,
                'last_update': datetime.utcnow()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des statistiques globales: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Nettoyer les anciens logs
        
        Args:
            days: Nombre de jours de rétention
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_logs = NTPLog.query.filter(NTPLog.timestamp < cutoff_date).all()
            
            for log in old_logs:
                db_manager.delete(log)
            
            if old_logs:
                db_manager.commit()
                self.logger.info(f"Suppression de {len(old_logs)} logs anciens")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des logs: {e}")
            db_manager.rollback()
    
    def get_system_time(self):
        """Récupérer les informations de temps système"""
        import time
        import datetime
        
        try:
            now = datetime.datetime.now()
            utc_now = datetime.datetime.utcnow()
            
            # Déterminer le fuseau horaire
            local_offset = now - utc_now
            offset_seconds = int(local_offset.total_seconds())
            offset_hours = offset_seconds // 3600
            offset_minutes = (abs(offset_seconds) % 3600) // 60
            
            # Format de l'offset
            offset_sign = '+' if offset_seconds >= 0 else '-'
            offset_str = f"{offset_sign}{abs(offset_hours):02d}:{offset_minutes:02d}"
            
            # Vérifier l'heure d'été (DST)
            is_dst = time.daylight and time.localtime().tm_isdst
            
            return {
                'local_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'utc_time': utc_now.strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': time.tzname[is_dst] if time.tzname else 'UTC',
                'utc_offset': offset_str,
                'is_dst': is_dst,
                'timestamp': now.timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur récupération temps système: {e}")
            return {
                'local_time': '--',
                'utc_time': '--', 
                'timezone': 'Unknown',
                'utc_offset': '+00:00',
                'is_dst': False,
                'timestamp': 0
            }

    def _check_thresholds_safe(self, server: NTPServer, result: Dict):
        """
        Vérifier les seuils et créer des alertes
        """
        try:
            # Importer AlertService dans le contexte d'application
            from backend.services.alert_service import AlertService
            alert_service = AlertService()
            
            if not result['success']:
                # Serveur indisponible
                alert_service.check_server_availability(server, False, result.get('error'))
                return
            
            # Serveur disponible - vérifier les seuils NTP
            alert_service.check_ntp_threshold(
                server=server,
                offset=result.get('offset', 0),
                delay=result.get('delay', 0),
                stratum=result.get('stratum')
            )
            
            # Marquer le serveur comme disponible
            alert_service.check_server_availability(server, True)
                
        except Exception as e:
            self.logger.debug(f"Erreur vérification seuils: {e}")

# Instance globale du service
ntp_service = NTPService() 