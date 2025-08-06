"""
Service Client Monitor - Monitoring des clients NTP connectés
VERSION CORRIGÉE - Gestion robuste des erreurs psutil
"""
import psutil
import subprocess
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class ClientMonitorService:
    """Service de monitoring des clients NTP - VERSION ROBUSTE"""
    
    def __init__(self):
        self.ntp_port = 123
        self.connection_history = defaultdict(list)
    
    def get_active_connections(self) -> List[Dict]:
        """Récupérer les connexions NTP actives - GESTION ROBUSTE"""
        connections = []
        
        try:
            # Récupérer les connexions réseau sur le port 123 avec gestion d'erreur robuste
            try:
                net_connections = psutil.net_connections(kind='udp')
            except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess) as e:
                logger.debug(f"Erreur psutil.net_connections (accès refusé): {e}")
                return []
            except Exception as e:
                logger.debug(f"Erreur inattendue psutil.net_connections: {e}")
                return []
            
            for conn in net_connections:
                try:
                    # Vérifier que la connexion a des attributs valides
                    if not hasattr(conn, 'laddr') or not conn.laddr:
                        continue
                        
                    if conn.laddr.port == self.ntp_port:
                        if hasattr(conn, 'raddr') and conn.raddr:  # Connexion établie
                            # Gestion sécurisée du PID
                            pid = None
                            try:
                                if hasattr(conn, 'pid') and conn.pid is not None:
                                    # Vérifier que le processus existe encore
                                    process = psutil.Process(conn.pid)
                                    # Test simple pour vérifier l'accessibilité
                                    _ = process.name()
                                    pid = conn.pid
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                # Processus n'existe plus, inaccessible ou zombie
                                pid = None
                            except Exception:
                                # Toute autre erreur
                                pid = None
                            
                            connection_info = {
                                'client_ip': conn.raddr.ip,
                                'client_port': conn.raddr.port,
                                'server_ip': conn.laddr.ip,
                                'server_port': conn.laddr.port,
                                'status': getattr(conn, 'status', 'ESTABLISHED'),
                                'pid': pid,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            connections.append(connection_info)
                            
                            # Ajouter à l'historique
                            self.connection_history[conn.raddr.ip].append(datetime.utcnow())
                            
                except (AttributeError, TypeError, ValueError) as e:
                    # Ignorer les connexions avec des attributs invalides
                    logger.debug(f"Connexion invalide ignorée: {e}")
                    continue
                except Exception as e:
                    # Capturer toute autre erreur inattendue
                    logger.debug(f"Erreur lors du traitement d'une connexion: {e}")
                    continue
            
            return connections
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des connexions: {e}")
            return []
    
    def get_ntpq_peers(self) -> List[Dict]:
        """Récupérer les informations via ntpq -p"""
        try:
            # Exécuter ntpq -p pour obtenir les pairs
            result = subprocess.run(['ntpq', '-p'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.debug(f"ntpq -p a échoué: {result.stderr}")
                return []
            
            peers = []
            lines = result.stdout.strip().split('\n')
            
            # Ignorer les 2 premières lignes (headers)
            for line in lines[2:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        try:
                            peer_info = {
                                'remote': parts[0].lstrip('*+-x#o'),
                                'refid': parts[1],
                                'stratum': int(parts[2]) if parts[2].isdigit() else 0,
                                'type': parts[3],
                                'when': parts[4],
                                'poll': parts[5],
                                'reach': parts[6],
                                'delay': float(parts[7]) if parts[7] != '-' else 0,
                                'offset': float(parts[8]) if parts[8] != '-' else 0,
                                'jitter': float(parts[9]) if len(parts) > 9 and parts[9] != '-' else 0,
                                'status': line[0] if line[0] in '*+-x#o' else ' '
                            }
                            peers.append(peer_info)
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Erreur parsing ligne ntpq: {line} - {e}")
                            continue
            
            return peers
            
        except subprocess.TimeoutExpired:
            logger.debug("Timeout lors de l'exécution de ntpq")
            return []
        except FileNotFoundError:
            logger.debug("Commande ntpq non disponible sur ce système")
            return []
        except Exception as e:
            logger.debug(f"Erreur lors de l'exécution de ntpq: {e}")
            return []
    
    def get_ntpq_associations(self) -> List[Dict]:
        """Récupérer les associations NTP via ntpq -as - DÉSACTIVÉ (non supporté)"""
        # Cette commande n'est pas supportée sur toutes les versions de ntpq
        # Retourner une liste vide pour éviter les erreurs
        logger.debug("ntpq -as désactivé (non supporté sur toutes les versions)")
        return []
    
    def get_ntp_statistics(self) -> Dict:
        """Récupérer les statistiques du service NTP - Compatible Windows/Linux"""
        try:
            import platform
            system = platform.system().lower()
            
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'service_status': 'unknown',
                'stratum': 0,
                'precision': 0,
                'rootdelay': 0,
                'rootdispersion': 0,
                'peer': '',
                'refid': '',
                'reftime': '',
                'poll': 0,
                'clock': '',
                'system': system,
                'processor': '',
                'uptime': 0
            }
            
            # Essayer ntpq seulement sur Linux ou si disponible
            if system != 'windows':
                try:
                    result = subprocess.run(['ntpq', '-c', 'rv'], 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        # Parser la sortie de ntpq -c rv
                        output = result.stdout.strip()
                        for line in output.split(','):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"')
                                
                                if key in stats:
                                    try:
                                        if key in ['stratum', 'precision', 'poll', 'uptime']:
                                            stats[key] = int(value)
                                        elif key in ['rootdelay', 'rootdispersion']:
                                            stats[key] = float(value)
                                        else:
                                            stats[key] = value
                                    except ValueError:
                                        stats[key] = value
                        
                        stats['service_status'] = 'active'
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.debug("ntpq non disponible sur ce système")
            
            # Windows : Utiliser w32tm pour obtenir des infos
            elif system == 'windows':
                try:
                    result = subprocess.run(['w32tm', '/query', '/status'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        stats['service_status'] = 'active'
                        # Parser les informations de base si possible
                        for line in result.stdout.split('\n'):
                            if 'Stratum:' in line:
                                try:
                                    stats['stratum'] = int(line.split(':')[1].strip())
                                except:
                                    pass
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.debug("w32tm non disponible")
            
            # Ajouter les connexions actives (universel)
            connections = self.get_active_connections()
            stats['active_connections'] = len(connections)
            stats['unique_clients'] = len(set(conn['client_ip'] for conn in connections))
            
            # Si des connexions sont trouvées, service probablement actif
            if stats['active_connections'] > 0 and stats['service_status'] == 'unknown':
                stats['service_status'] = 'active'
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'service_status': 'error',
                'system': platform.system().lower(),
                'active_connections': 0,
                'unique_clients': 0,
                'error': str(e)
            }
    
    def get_client_statistics(self, hours: int = 24) -> Dict:
        """Récupérer les statistiques des clients"""
        try:
            # Nettoyer l'historique ancien
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            for client_ip in list(self.connection_history.keys()):
                self.connection_history[client_ip] = [
                    timestamp for timestamp in self.connection_history[client_ip]
                    if timestamp > cutoff_time
                ]
                
                # Supprimer les clients sans connexions récentes
                if not self.connection_history[client_ip]:
                    del self.connection_history[client_ip]
            
            # Calculer les statistiques
            total_clients = len(self.connection_history)
            total_connections = sum(len(connections) for connections in self.connection_history.values())
            
            # Clients les plus actifs
            top_clients = sorted(
                self.connection_history.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
            
            return {
                'period_hours': hours,
                'total_unique_clients': total_clients,
                'total_connections': total_connections,
                'average_connections_per_client': total_connections / total_clients if total_clients > 0 else 0,
                'top_clients': [
                    {'ip': ip, 'connection_count': len(connections)}
                    for ip, connections in top_clients
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques clients: {e}")
            return {
                'period_hours': hours,
                'total_unique_clients': 0,
                'total_connections': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_connection_stats(self) -> Dict:
        """Récupérer les statistiques de connexion actuelles"""
        try:
            connections = self.get_active_connections()
            
            # Grouper par IP client
            client_ips = {}
            for conn in connections:
                ip = conn['client_ip']
                if ip not in client_ips:
                    client_ips[ip] = []
                client_ips[ip].append(conn)
            
            return {
                'total_connections': len(connections),
                'unique_clients': len(client_ips),
                'connections_per_client': {
                    ip: len(conns) for ip, conns in client_ips.items()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats de connexion: {e}")
            return {
                'total_connections': 0,
                'unique_clients': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_service_status(self) -> Dict:
        """Vérifier le statut du service NTP - VERSION ROBUSTE"""
        try:
            import platform
            system = platform.system().lower()
            
            service_status = 'unknown'
            listening = False
            
            # Vérifier si le port 123 est en écoute - GESTION ROBUSTE
            try:
                for conn in psutil.net_connections(kind='udp'):
                    if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == self.ntp_port:
                        listening = True
                        break
            except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess) as e:
                logger.debug(f"Erreur lors de la vérification du port (non critique): {e}")
                listening = False
            except Exception as e:
                logger.debug(f"Erreur inattendue lors de la vérification du port: {e}")
                listening = False
            
            # Si on écoute sur le port, considérer comme actif
            if listening and service_status in ['unknown', 'inactive']:
                service_status = 'active'
            
            return {
                'service_status': service_status,
                'port_listening': listening,
                'port': self.ntp_port,
                'system': system,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification du service: {e}")
            return {
                'service_status': 'unknown',
                'port_listening': False,
                'port': self.ntp_port,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Instance globale du service
client_monitor_service = ClientMonitorService() 
