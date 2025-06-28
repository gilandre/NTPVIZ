"""
Service NTP - Requêtes et monitoring des serveurs NTP
"""
import ntplib
import time
import socket
import pytz
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple
import logging
from backend.models.ntp_server import NTPServer
from backend.models.ntp_log import NTPLog
from backend.models.alert import Alert
from backend.app import db

logger = logging.getLogger(__name__)

class NTPService:
    """Service principal pour les requêtes NTP"""
    
    def __init__(self):
        self.client = ntplib.NTPClient()
    
    def query_server(self, server: NTPServer) -> Dict:
        """Effectuer une requête NTP vers un serveur"""
        try:
            logger.info(f"Querying NTP server {server.name} ({server.address})")
            
            # Heure locale avant la requête
            local_time_before = datetime.now()
            
            # Requête NTP
            response = self.client.request(server.address, port=server.port, timeout=server.timeout)
            
            # Heure locale après la requête
            local_time_after = datetime.now()
            
            # Calculer l'offset et la latence
            server_time = datetime.fromtimestamp(response.tx_time)
            local_time_avg = local_time_before + (local_time_after - local_time_before) / 2
            offset = (server_time - local_time_avg).total_seconds()
            latency = (local_time_after - local_time_before).total_seconds() * 1000  # en ms
            
            # Enregistrer le log
            ntp_log = NTPLog(
                server_id=server.id,
                timestamp=datetime.utcnow(),
                offset=offset,
                latency=latency,
                stratum=response.stratum,
                precision=response.precision,
                root_delay=response.root_delay,
                root_dispersion=response.root_dispersion,
                reference_id=response.ref_id,
                local_time=local_time_avg,
                server_time=server_time,
                status='success'
            )
            db.session.add(ntp_log)
            
            # Mettre à jour le serveur
            server.update_status(offset=offset, latency=latency, error=False)
            
            # Vérifier si une alerte doit être créée
            self._check_and_create_alerts(server, offset)
            
            db.session.commit()
            
            result = {
                'server_id': server.id,
                'server_name': server.name,
                'server_address': server.address,
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'local_time': local_time_avg.isoformat(),
                'server_time': server_time.isoformat(),
                'offset': offset,
                'offset_ms': offset * 1000,
                'latency': latency,
                'stratum': response.stratum,
                'precision': response.precision,
                'root_delay': response.root_delay,
                'root_dispersion': response.root_dispersion,
                'reference_id': response.ref_id,
                'status': server.status
            }
            
            logger.info(f"NTP query successful for {server.name}: offset={offset:.3f}s, latency={latency:.1f}ms")
            return result
            
        except ntplib.NTPException as e:
            logger.error(f"NTP error for {server.name}: {e}")
            return self._handle_error(server, f"NTP error: {e}")
            
        except socket.timeout:
            logger.error(f"Timeout querying {server.name}")
            return self._handle_error(server, "Timeout")
            
        except Exception as e:
            logger.error(f"Unexpected error querying {server.name}: {e}")
            return self._handle_error(server, f"Error: {e}")
    
    def _handle_error(self, server: NTPServer, error_message: str) -> Dict:
        """Gérer les erreurs de requête NTP"""
        # Enregistrer le log d'erreur
        ntp_log = NTPLog(
            server_id=server.id,
            timestamp=datetime.utcnow(),
            status='error',
            error_message=error_message,
            local_time=datetime.now()
        )
        db.session.add(ntp_log)
        
        # Mettre à jour le serveur
        server.update_status(error=True)
        
        # Créer une alerte si nécessaire
        if server.consecutive_errors >= 3:
            Alert.create_offline_alert(server)
        
        db.session.commit()
        
        return {
            'server_id': server.id,
            'server_name': server.name,
            'server_address': server.address,
            'success': False,
            'timestamp': datetime.utcnow().isoformat(),
            'error': error_message,
            'status': server.status,
            'consecutive_errors': server.consecutive_errors
        }
    
    def _check_and_create_alerts(self, server: NTPServer, offset: float):
        """Vérifier et créer des alertes selon l'offset"""
        abs_offset = abs(offset)
        
        if abs_offset >= server.max_offset:
            # Vérifier s'il y a déjà une alerte active pour ce serveur
            existing_alert = Alert.query.filter_by(
                server_id=server.id,
                alert_type='offset',
                status='active'
            ).first()
            
            if not existing_alert:
                Alert.create_offset_alert(server, offset)
                logger.warning(f"Offset alert created for {server.name}: {offset:.3f}s")
    
    def query_all_servers(self) -> List[Dict]:
        """Interroger tous les serveurs NTP actifs"""
        servers = NTPServer.query.filter_by(is_active=True).order_by(NTPServer.priority).all()
        results = []
        
        for server in servers:
            try:
                result = self.query_server(server)
                results.append(result)
            except Exception as e:
                logger.error(f"Error querying server {server.name}: {e}")
                results.append(self._handle_error(server, str(e)))
        
        return results
    
    def get_server_statistics(self, server_id: int, hours: int = 24) -> Optional[Dict]:
        """Récupérer les statistiques d'un serveur"""
        try:
            server = NTPServer.query.get(server_id)
            if not server:
                return None
            
            stats = NTPLog.get_server_stats(server_id, hours)
            if not stats:
                return None
            
            # Ajouter les informations du serveur
            stats.update({
                'server_id': server_id,
                'server_name': server.name,
                'server_address': server.address,
                'server_type': server.server_type,
                'current_status': server.status,
                'last_sync': server.last_sync.isoformat() if server.last_sync else None,
                'last_offset': server.last_offset,
                'last_latency': server.last_latency
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting server statistics for {server_id}: {e}")
            return None
    
    def test_connectivity(self, address: str, port: int = 123, timeout: int = 5) -> Dict:
        """Tester la connectivité vers un serveur NTP"""
        try:
            # Test de résolution DNS
            socket.gethostbyname(address)
            
            # Test de connexion UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            try:
                # Envoyer un paquet de test
                sock.connect((address, port))
                sock.close()
                
                return {
                    'reachable': True,
                    'dns_resolved': True,
                    'port_open': True,
                    'response_time': timeout  # Approximation
                }
                
            except socket.error:
                return {
                    'reachable': False,
                    'dns_resolved': True,
                    'port_open': False,
                    'error': 'Port unreachable'
                }
                
        except socket.gaierror:
            return {
                'reachable': False,
                'dns_resolved': False,
                'port_open': False,
                'error': 'DNS resolution failed'
            }
        except Exception as e:
            return {
                'reachable': False,
                'dns_resolved': False,
                'port_open': False,
                'error': str(e)
            }
    
    def get_system_time(self) -> Dict:
        """Récupérer les informations temporelles du système"""
        try:
            now_local = datetime.now()
            now_utc = datetime.utcnow()
            
            # Obtenir le timezone local
            import time
            is_dst = time.daylight and time.localtime().tm_isdst > 0
            utc_offset = -(time.altzone if is_dst else time.timezone)
            
            # Nom du timezone
            timezone_name = time.tzname[1] if is_dst else time.tzname[0]
            
            # Essayer d'obtenir le timezone avec pytz
            try:
                import subprocess
                result = subprocess.run(['timedatectl', 'show', '--property=Timezone', '--value'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    timezone_name = result.stdout.strip()
            except:
                pass
            
            return {
                'local_time': now_local.isoformat(),
                'utc_time': now_utc.isoformat(),
                'timezone': timezone_name,
                'utc_offset_seconds': utc_offset,
                'utc_offset_hours': utc_offset / 3600,
                'is_dst': is_dst,
                'timestamp': time.time(),
                'formatted_local': now_local.strftime('%Y-%m-%d %H:%M:%S'),
                'formatted_utc': now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
        except Exception as e:
            logger.error(f"Error getting system time: {e}")
            return {
                'local_time': datetime.now().isoformat(),
                'utc_time': datetime.utcnow().isoformat(),
                'timezone': 'Unknown',
                'error': str(e)
            }

# Instance globale du service
ntp_service = NTPService() 