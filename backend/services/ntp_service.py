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

from backend.database_manager import DatabaseManager, get_db_session_with_context
from backend.database import NTPServer
from backend.database import NTPLog
from backend.database import SystemConfig
from backend.services.alert_service import alert_service
from backend.database_manager import get_db_session_with_context

# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()

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
        
        # Nettoyer et valider l'adresse
        if not server.address:
            result['error'] = "Adresse serveur manquante"
            return result
            
        clean_address = server.address.strip().replace('\r', '').replace('\n', '').replace('\t', '')
        
        # Validation supplémentaire de l'adresse
        if not clean_address or len(clean_address) < 3:
            result['error'] = f"Adresse serveur invalide: '{server.address}'"
            return result
        
        # Validation du port
        port = server.port if server.port and server.port > 0 else 123
        if port < 1 or port > 65535:
            port = 123
        
        try:
            self.logger.debug(f"Requête NTP vers {server.name} ({clean_address}:{port})")
            
            # Effectuer la requête NTP avec validation des paramètres
            response = self.client.request(
                clean_address,
                port=port,
                timeout=min(timeout, 30),  # Limiter le timeout à 30 secondes max
                version=3  # Utiliser NTP version 3 pour une meilleure compatibilité
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
            # S'assurer que le Database Manager est initialisé
            if not db_manager.initialized:
                db_manager.initialize()
            
            # Utiliser le database manager avec contexte Flask
            with get_db_session_with_context() as session:
                # Récupérer le serveur dans cette session MySQL
                server_instance = session.get(NTPServer, server.id)
                if not server_instance:
                    return
                
                # Mettre à jour le statut et la dernière vérification
                server_instance.status = 'ok' if result['success'] else 'offline'
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
        Interroger tous les serveurs NTP avec gestion correcte des sessions
        
        Args:
            active_only: Interroger seulement les serveurs actifs
            
        Returns:
            Liste des résultats de requêtes
        """
        try:
            # S'assurer que le Database Manager est initialisé
            if not db_manager.initialized:
                db_manager.initialize()
            
            # Récupérer les données des serveurs (pas les objets SQLAlchemy)
            servers_data = []
            with get_db_session_with_context() as session:
                query = session.query(NTPServer)
                if active_only:
                    query = query.filter(
                        NTPServer.is_active == True,
                        NTPServer.deleted_at.is_(None)
                    )
                else:
                    # Même sans active_only, exclure les serveurs supprimés
                    query = query.filter(NTPServer.deleted_at.is_(None))
                
                servers = query.all()
                
                # Convertir les objets en dictionnaires pour éviter les problèmes de session
                for server in servers:
                    servers_data.append({
                        'id': server.id,
                        'name': server.name,
                        'address': server.address,
                        'port': server.port,
                        'timeout': server.timeout,
                        'max_offset': None
                    })
            
            if not servers_data:
                self.logger.warning("Aucun serveur NTP configuré")
                return []
            
            self.logger.info(f"Interrogation de {len(servers_data)} serveurs NTP")
            
            results = []
            
            # Requêtes séquentielles pour éviter les problèmes de concurrence
            for server_data in servers_data:
                try:
                    result = self._query_server_from_data(server_data)
                    results.append(result)
                    
                    # Mettre à jour le serveur en base
                    self._update_server_status_safe(result)
                    
                    # Enregistrer le log NTP
                    self._log_ntp_query(result)
                    
                except Exception as e:
                    self.logger.error(f"Erreur requête serveur {server_data['name']}: {e}")
                    # Créer un résultat d'erreur
                    error_result = {
                        'server_id': server_data['id'],
                        'server_name': server_data['name'],
                        'server_address': server_data['address'],
                        'timestamp': datetime.utcnow(),
                        'success': False,
                        'error': str(e)
                    }
                    results.append(error_result)
                    self._update_server_status_safe(error_result)
                    self._log_ntp_query(error_result)
            
            self.logger.info(f"Requêtes NTP terminées: {len(results)} résultats")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'interrogation des serveurs: {e}")
            return []
    
    def query_server_from_data(self, server_data: Dict, timeout: float = None) -> Dict:
        """
        Interroger un serveur NTP en utilisant des données de serveur (pas d'objet SQLAlchemy)
        
        Args:
            server_data: Dictionnaire avec les données du serveur
            timeout: Timeout personnalisé
            
        Returns:
            Dictionnaire avec le résultat de la requête
        """
        start_time = datetime.utcnow()
        server_address = server_data['address']
        server_port = server_data.get('port', 123)
        server_timeout = timeout or server_data.get('timeout', 5.0)
        
        result = {
            'server_id': server_data['id'],
            'server_name': server_data['name'],
            'server_address': server_address,
            'timestamp': start_time,
            'success': False,
            'error': None
        }
        
        try:
            client = ntplib.NTPClient()
            response = client.request(server_address, port=server_port, timeout=server_timeout)
            
            # Calculer les métriques
            result.update({
                'success': True,
                'offset': response.offset,
                'delay': response.delay,
                'latency': response.delay,  # Alias pour compatibilité
                'stratum': response.stratum,
                'precision': response.precision,
                'root_delay': response.root_delay,
                'root_dispersion': response.root_dispersion,
                'ref_id': response.ref_id,
                'response_time': (datetime.utcnow() - start_time).total_seconds()
            })
            
            self.logger.debug(f"✅ {server_data['name']}: offset={response.offset:.4f}s, delay={response.delay:.4f}s")
            
        except ntplib.NTPException as e:
            result['error'] = f"Erreur NTP: {e}"
            self.logger.warning(f"❌ {server_data['name']}: {result['error']}")
        except Exception as e:
            result['error'] = f"Erreur réseau: {e}"
            self.logger.warning(f"❌ {server_data['name']}: {result['error']}")
        
        return result
    
    def _update_server_status_safe(self, result: Dict):
        """
        Mettre à jour le statut d'un serveur avec une nouvelle session
        """
        try:
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == result['server_id']).first()
                if server:
                    server.status = 'ok' if result['success'] else 'offline'
                    server.last_sync = result['timestamp']
                    server.last_offset = result.get('offset')
                    server.last_latency = result.get('latency')
                    server.last_stratum = result.get('stratum')
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statut: {e}")
    
    def get_server_statistics(self, server_id: int, hours: int = 24) -> Dict:
        """
        Obtenir des statistiques pour un serveur
        
        Args:
            server_id: ID du serveur
            hours: Nombre d'heures à analyser
            
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == server_id).first()
                if not server:
                    return {}
                
                # Période d'analyse
                since = datetime.utcnow() - timedelta(hours=hours)
                
                # Requêtes dans la période
                logs = session.query(NTPLog).filter(
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
                successful_logs = [log for log in logs if log.status == 'success']
                failed_logs = [log for log in logs if log.status != 'success']
                
                offsets = [log.offset for log in successful_logs if log.offset is not None]
                delays = [log.latency for log in successful_logs if log.latency is not None]
                
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
            
            with get_db_session_with_context() as session:
                # Serveurs actifs
                active_servers = session.query(NTPServer).filter_by(is_active=True).all()
                
                # Logs dans la période
                total_logs = session.query(NTPLog).filter(NTPLog.timestamp >= since).count()
                successful_logs = session.query(NTPLog).filter(
                    NTPLog.timestamp >= since,
                    NTPLog.status == 'success'
                ).count()
                
                # Serveurs en ligne
                online_servers = len([s for s in active_servers if s.status == 'ok'])
                
                # Alertes actives
                from backend.database import Alert
                active_alerts = session.query(Alert).filter_by(status='active').count()
                critical_alerts = session.query(Alert).filter_by(status='active', severity='critical').count()
                
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
            
            with get_db_session_with_context() as session:
                old_logs = session.query(NTPLog).filter(NTPLog.timestamp < cutoff_date).all()
                
                for log in old_logs:
                    session.delete(log)
                
                if old_logs:
                    session.commit()
                    self.logger.info(f"Suppression de {len(old_logs)} logs anciens")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des logs: {e}")
    
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

    def _log_ntp_query(self, result: Dict):
        """Enregistrer le résultat d'une requête NTP en base de données"""
        try:
            with get_db_session_with_context() as session:
                # Créer un log NTP - PARAMÈTRES COMPATIBLES UNIQUEMENT
                log_entry = NTPLog(
                    server_id=result['server_id'],
                    timestamp=result['timestamp'],
                    status='success' if result['success'] else 'error',
                    offset=result.get('offset'),
                    delay=result.get('delay'),
                    latency=result.get('latency', result.get('delay')),
                    stratum=result.get('stratum'),
                    response_time=result.get('response_time'),
                    error_message=result.get('error') if not result['success'] else None
                )
                session.add(log_entry)
                session.commit()
                
                self.logger.debug(f"Log NTP enregistré pour serveur {result['server_id']}")
                
        except Exception as e:
            self.logger.error(f"Erreur enregistrement log NTP: {e}")

    def _query_server_from_data(self, server_data: Dict, timeout: float = None) -> Dict:
        """
        Interroger un serveur NTP en utilisant des données de serveur (pas d'objet SQLAlchemy)
        CORRECTION: Inclut maintenant la vérification des seuils d'alertes
        """
        start_time = datetime.utcnow()
        server_address = server_data['address']
        server_port = server_data.get('port', 123)
        server_timeout = timeout or server_data.get('timeout', 5.0)
        
        result = {
            'server_id': server_data['id'],
            'server_name': server_data['name'],
            'server_address': server_address,
            'timestamp': start_time,
            'success': False,
            'error': None
        }
        
        try:
            client = ntplib.NTPClient()
            response = client.request(server_address, port=server_port, timeout=server_timeout)
            
            result.update({
                'success': True,
                'offset': response.offset,
                'delay': response.delay,
                'latency': response.delay,
                'stratum': response.stratum,
                'precision': response.precision,
                'root_delay': response.root_delay,
                'root_dispersion': response.root_dispersion,
                'ref_id': response.ref_id,
                'response_time': (datetime.utcnow() - start_time).total_seconds()
            })
            
            # CORRECTION CRITIQUE: Vérifier les seuils d'alertes pour ce serveur
            self._check_thresholds_from_data(server_data, result)
            
        except ntplib.NTPException as e:
            result['error'] = f"Erreur NTP: {e}"
            # Créer une alerte de disponibilité pour erreur NTP
            self._check_availability_from_data(server_data, False, result['error'])
        except Exception as e:
            result['error'] = f"Erreur réseau: {e}"
            # Créer une alerte de disponibilité pour erreur réseau
            self._check_availability_from_data(server_data, False, result['error'])
        
        return result

    def _check_thresholds_from_data(self, server_data: Dict, result: Dict):
        """
        Vérifier les seuils et créer des alertes à partir des données de serveur
        NOUVELLE MÉTHODE: Permet la vérification des seuils pour tous les serveurs
        
        Args:
            server_data: Données du serveur (dictionnaire)
            result: Résultat de la requête NTP
        """
        try:
            if not result['success']:
                return
            
            # Récupérer l'objet serveur pour la vérification des seuils
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == server_data['id']).first()
                
                if server:
                    # Utiliser le service d'alertes pour vérifier les seuils
                    alert_service.check_ntp_threshold(
                        server=server,
                        offset=result.get('offset', 0),
                        delay=result.get('delay', 0),
                        stratum=result.get('stratum')
                    )
                    
                    # Marquer le serveur comme disponible
                    alert_service.check_server_availability(server, True)
                else:
                    self.logger.warning(f"Serveur {server_data['id']} non trouvé pour vérification seuils")
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification seuils serveur {server_data['name']}: {e}")

    def _check_availability_from_data(self, server_data: Dict, is_available: bool, error_message: str = None):
        """
        Vérifier la disponibilité d'un serveur à partir des données de serveur
        NOUVELLE MÉTHODE: Permet la vérification de disponibilité pour tous les serveurs
        
        Args:
            server_data: Données du serveur (dictionnaire)
            is_available: Serveur disponible ou non
            error_message: Message d'erreur si indisponible
        """
        try:
            # Récupérer l'objet serveur pour la vérification de disponibilité
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == server_data['id']).first()
                
                if server:
                    # Utiliser le service d'alertes pour vérifier la disponibilité
                    alert_service.check_server_availability(server, is_available, error_message)
                else:
                    self.logger.warning(f"Serveur {server_data['id']} non trouvé pour vérification disponibilité")
                    
        except Exception as e:
            self.logger.error(f"Erreur vérification disponibilité serveur {server_data['name']}: {e}")

    def _update_server_status_safe(self, result: Dict):
        """
        Mettre à jour le statut d'un serveur avec une nouvelle session
        """
        try:
            with get_db_session_with_context() as session:
                server = session.query(NTPServer).filter(NTPServer.id == result['server_id']).first()
                if server:
                    server.status = 'ok' if result['success'] else 'offline'
                    server.last_sync = result['timestamp']
                    server.last_offset = result.get('offset')
                    server.last_latency = result.get('latency')
                    server.last_stratum = result.get('stratum')
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statut: {e}")

    def test_connectivity(self, address: str, port: int = 123, timeout: float = 5.0) -> Dict:
        """
        Tester la connectivité vers un serveur NTP
        
        Args:
            address: Adresse du serveur
            port: Port du serveur (défaut: 123)
            timeout: Timeout en secondes (défaut: 5.0)
            
        Returns:
            Dictionnaire avec les résultats du test
        """
        result = {
            'address': address,
            'port': port,
            'timeout': timeout,
            'reachable': False,
            'error': None,
            'response_time': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Test de connectivité réseau de base
            start_time = datetime.utcnow()
            
            # Créer un socket pour tester la connectivité
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Essayer de se connecter
            sock.connect((address, port))
            sock.close()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            result.update({
                'reachable': True,
                'response_time': response_time
            })
            
            self.logger.debug(f"Connectivité OK vers {address}:{port} en {response_time:.3f}s")
            
        except socket.timeout:
            result['error'] = f"Timeout lors de la connexion à {address}:{port}"
            self.logger.warning(result['error'])
            
        except socket.gaierror as e:
            result['error'] = f"Erreur DNS pour {address}: {str(e)}"
            self.logger.error(result['error'])
            
        except ConnectionRefusedError:
            result['error'] = f"Connexion refusée par {address}:{port}"
            self.logger.warning(result['error'])
            
        except Exception as e:
            result['error'] = f"Erreur de connectivité vers {address}:{port}: {str(e)}"
            self.logger.error(result['error'])
        
        return result

# Instance globale du service
ntp_service = NTPService() 