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
import threading

# SUPPRIMÉ: Import Flask-SQLAlchemy circulaire
from backend.database import NTPServer
from backend.database import NTPLog
from backend.database import SystemConfig
from backend.services.alert_service import alert_service

logger = logging.getLogger(__name__)

class NTPService:
    """Service de gestion NTP"""
    
    def __init__(self):
        self.client = ntplib.NTPClient()
        self.logger = logger
        self._monitoring_active = False
        self._monitoring_thread = None
        
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
            
            # Mettre  jour le statut du serveur (avec contexte d'application)
            try:
                from flask import current_app
                with current_app.app_context():
                    self._update_server_status(server, result)
                    self._check_thresholds_safe(server, result)
            except RuntimeError:
                # Pas de contexte d'application, on continue sans mise  jour
                self.logger.debug("Pas de contexte d'application pour la mise  jour")
            
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
    
    def _check_thresholds_safe(self, server: NTPServer, result: Dict):
        """
        Vrifier les seuils de manire scurise
        """
        try:
            if not result['success']:
                return
                
            # Vrifications basiques sans service d'alerte complexe
            if result['offset'] and abs(result['offset']) > (server.max_offset or 1.0):
                self.logger.warning(f"Offset lev pour {server.name}: {result['offset']:.3f}s")
                
        except Exception as e:
            self.logger.debug(f"Erreur vrification seuils: {e}")
    
    def _update_server_status(self, server: NTPServer, result: Dict):
        """
        Mettre  jour le statut du serveur
        """
        try:
            if result['success']:
                server.status = 'online'
                server.last_sync = result['timestamp']
                server.last_offset = result['offset']
                server.last_latency = result['delay']
                server.consecutive_errors = 0
                server.last_error = None
            else:
                server.status = 'offline'
                server.last_error = result['error']
                server.consecutive_errors += 1
            
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise  jour du statut: {e}")
            db.session.rollback()
    
    def query_all_servers(self, active_only: bool = True) -> List[Dict]:
        """
        Interroger tous les serveurs NTP
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
            max_workers = min(len(servers), 10)
            
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
        """
        try:
            # Vrifier si on a un contexte d'application
            from flask import current_app
            with current_app.app_context():
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
                
        except RuntimeError:
            # Pas de contexte d'application
            self.logger.debug("Pas de contexte d'application pour le logging")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du log: {e}")
            try:
                db.session.rollback()
            except:
                pass

    def start_continuous_monitoring(self, interval_seconds: int = 300):
        """
        Dmarrer le monitoring continu des serveurs NTP
        
        Args:
            interval_seconds: Intervalle entre les synchronisations (dfaut: 5 minutes)
        """
        if self._monitoring_active:
            self.logger.info("Monitoring NTP dj actif")
            return
            
        self._monitoring_active = True
        
        def monitoring_worker():
            self.logger.info(f"Dmarrage du monitoring NTP continu (intervalle: {interval_seconds}s)")
            
            while self._monitoring_active:
                try:
                    # Importer l'application et crer le contexte
                    from backend.app import create_app
                    app = create_app()
                    
                    with app.app_context():
                        results = self.query_all_servers()
                        successful = len([r for r in results if r.get('success', False)])
                        self.logger.info(f"Monitoring NTP: {successful}/{len(results)} serveurs synchroniss")
                    
                    # Attendre l'intervalle
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    self.logger.error(f"Erreur monitoring NTP: {e}")
                    time.sleep(30)  # Attendre 30s en cas d'erreur
            
            self.logger.info("Arrt du monitoring NTP continu") 
        
        self._monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self._monitoring_thread.start()
        
    def stop_continuous_monitoring(self):
        """Arrter le monitoring continu"""
        if self._monitoring_active:
            self._monitoring_active = False
            self.logger.info("Arrt du monitoring NTP demand")

    def get_server_statistics(self, server_id: int, hours: int = 24) -> Dict:
        """
        Obtenir les statistiques d'un serveur
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

    def get_system_time(self):
        """Obtenir l'heure systme"""
        try:
            now = datetime.utcnow()
            return {
                'utc_time': now.isoformat(),
                'local_time': now.isoformat(),
                'timezone': 'UTC',
                'timestamp': now.timestamp()
            }
        except Exception as e:
            self.logger.error(f"Erreur rcupration heure systme: {e}")
            return {
                'error': str(e),
                'utc_time': datetime.utcnow().isoformat(),
                'local_time': datetime.utcnow().isoformat(),
                'timezone': 'UTC',
                'timestamp': datetime.utcnow().timestamp()
            }

# Instance globale
ntp_service = NTPService() 
