"""
Service NTP - Gestion des requtes et surveillance des serveurs NTP
"""
import ntplib
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from backend.database_manager import db
from backend.models.ntp_server import NTPServer
from backend.models.ntp_log import NTPLog
from backend.models.system_config import SystemConfig
from backend.services.alert_service import alert_service

logger = logging.getLogger(__name__)

class NTPService:
    """Service de gestion NTP"""
    
    def __init__(self):
        self.client = ntplib.NTPClient()
        self.logger = logger
        
    def query_server(self, server: NTPServer, timeout: float = None) -> Dict:
        """
        Interroger un serveur NTP
        
        Args:
            server: Serveur NTP  interroger
            timeout: Timeout en secondes
            
        Returns:
            Dictionnaire avec les rsultats de la requte
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
        
        try:
            self.logger.debug(f"Requte NTP vers {server.name} ({server.address})")
            
            # Effectuer la requte NTP
            response = self.client.request(
                server.address,
                port=server.port,
                timeout=timeout
            )
            
            # Extraire les donnes de la rponse
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
            
            # Vrifier les seuils et crer des alertes si ncessaire
            self._check_thresholds(server, result)
            
            # Mettre  jour le statut du serveur
            self._update_server_status(server, result)
            
            self.logger.debug(f"Requte NTP russie: {server.name} - Offset: {response.offset:.3f}s")
            
        except socket.timeout:
            error_msg = f"Timeout lors de la requte vers {server.address}"
            result['error'] = error_msg
            self.logger.warning(error_msg)
            
            # Crer une alerte de disponibilit
            alert_service.check_server_availability(server, False, error_msg)
            
        except socket.gaierror as e:
            error_msg = f"Erreur DNS pour {server.address}: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg)
            
            # Crer une alerte de disponibilit
            alert_service.check_server_availability(server, False, error_msg)
            
        except Exception as e:
            error_msg = f"Erreur NTP pour {server.address}: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg)
            
            # Crer une alerte de disponibilit
            alert_service.check_server_availability(server, False, error_msg)
        
        return result
    
    def _check_thresholds(self, server: NTPServer, result: Dict):
        """
        Vrifier les seuils et crer des alertes si ncessaire
        
        Args:
            server: Serveur NTP
            result: Rsultat de la requte
        """
        try:
            if not result['success']:
                return
            
            # Vrifier les seuils NTP via le service d'alertes
            alert_service.check_ntp_threshold(
                server=server,
                offset=result['offset'],
                delay=result['delay'],
                stratum=result['stratum']
            )
            
            # Si tout va bien, marquer le serveur comme disponible
            alert_service.check_server_availability(server, True)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vrification des seuils: {e}")
    
    def _update_server_status(self, server: NTPServer, result: Dict):
        """
        Mettre à jour le statut du serveur
        
        Args:
            server: Serveur NTP
            result: Résultat de la requête
        """
        try:
            if result['success']:
                # Utiliser la méthode update_status du modèle qui gère correctement les seuils
                server.update_status(
                    offset=result.get('offset'),
                    latency=result.get('delay'), 
                    stratum=result.get('stratum'),
                    error=False
                )
                # Les autres champs sont gérés par update_status
                server.last_sync = result['timestamp']
                if result.get('stratum') is not None:
                    server.last_stratum = result.get('stratum')
                db.session.commit()
            else:
                # Utiliser la méthode update_status pour les erreurs
                server.update_status(error=True)
                server.last_error = result['error']
                # update_status fait déjà le commit mais on le refait pour last_error
                db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour du statut: {e}")
            try:
                try:
                db.session.rollback()
            except:
                pass
            except:
                pass
    
    def query_all_servers(self, active_only: bool = True) -> List[Dict]:
        """
        Interroger tous les serveurs NTP
        
        Args:
            active_only: Interroger seulement les serveurs actifs
            
        Returns:
            Liste des rsultats de requtes
        """
        try:
            # Rcuprer les serveurs
            query = NTPServer.query
            if active_only:
                query = query.filter_by(is_active=True)
            
            servers = query.order_by(NTPServer.priority).all()
            
            if not servers:
                self.logger.warning("Aucun serveur NTP configur")
                return []
            
            self.logger.info(f"Interrogation de {len(servers)} serveurs NTP")
            
            results = []
            
            # Utiliser ThreadPoolExecutor pour les requtes parallles
            max_workers = min(len(servers), 10)  # Limiter  10 threads max
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Soumettre toutes les requtes
                future_to_server = {
                    executor.submit(self.query_server, server): server
                    for server in servers
                }
                
                # Collecter les rsultats
                for future in as_completed(future_to_server, timeout=30):
                    server = future_to_server[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Enregistrer le log NTP
                        self._log_ntp_query(result)
                        
                    except Exception as e:
                        self.logger.error(f"Erreur lors de la requte vers {server.name}: {e}")
                        
                        # Crer un rsultat d'erreur
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
            
            self.logger.info(f"Requtes NTP termines: {len(results)} rsultats")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'interrogation des serveurs: {e}")
            return []
    
    def _log_ntp_query(self, result: Dict):
        """
        Enregistrer un log de requte NTP
        
        Args:
            result: Rsultat de la requte
        """
        try:
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
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du log: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def get_server_statistics(self, server_id: int, hours: int = 24) -> Dict:
        """
        Obtenir les statistiques d'un serveur
        
        Args:
            server_id: ID du serveur
            hours: Nombre d'heures  analyser
            
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            server = NTPServer.query.get(server_id)
            if not server:
                return {}
            
            # Priode d'analyse
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Requtes dans la priode
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
            hours: Nombre d'heures  analyser
            
        Returns:
            Dictionnaire avec les statistiques globales
        """
        try:
            # Priode d'analyse
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Serveurs actifs
            active_servers = NTPServer.query.filter_by(is_active=True).all()
            
            # Logs dans la priode
            total_logs = NTPLog.query.filter(NTPLog.timestamp >= since).count()
            successful_logs = NTPLog.query.filter(
                NTPLog.timestamp >= since,
                NTPLog.success == True
            ).count()
            
            # Serveurs en ligne
            online_servers = len([s for s in active_servers if s.status == 'ok'])
            
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
            days: Nombre de jours de rtention
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_logs = NTPLog.query.filter(NTPLog.timestamp < cutoff_date).all()
            
            for log in old_logs:
                db.session.delete(log)
            
            if old_logs:
                db.session.commit()
                self.logger.info(f"Suppression de {len(old_logs)} logs anciens")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des logs: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def get_system_time(self):
        """Rcuprer les informations de temps systme"""
        import time
        import datetime
        
        try:
            now = datetime.datetime.now()
            utc_now = datetime.datetime.utcnow()
            
            # Dterminer le fuseau horaire
            local_offset = now - utc_now
            offset_seconds = int(local_offset.total_seconds())
            offset_hours = offset_seconds // 3600
            offset_minutes = (abs(offset_seconds) % 3600) // 60
            
            # Format de l'offset
            offset_sign = '+' if offset_seconds >= 0 else '-'
            offset_str = f"{offset_sign}{abs(offset_hours):02d}:{offset_minutes:02d}"
            
            # Vrifier l'heure d't (DST)
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
            self.logger.error(f"Erreur rcupration temps systme: {e}")
            return {
                'local_time': '--',
                'utc_time': '--', 
                'timezone': 'Unknown',
                'utc_offset': '+00:00',
                'is_dst': False,
                'timestamp': 0
            }

# Instance globale du service
ntp_service = NTPService() 
