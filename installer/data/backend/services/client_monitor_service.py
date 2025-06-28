"""
Service Client Monitor - Monitoring des clients NTP connectés
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
    """Service de monitoring des clients NTP"""
    
    def __init__(self):
        self.ntp_port = 123
        self.connection_history = defaultdict(list)
    
    def get_active_connections(self) -> List[Dict]:
        """Récupérer les connexions NTP actives"""
        connections = []
        
        try:
            # Récupérer les connexions réseau sur le port 123
            for conn in psutil.net_connections(kind='udp'):
                if conn.laddr and conn.laddr.port == self.ntp_port:
                    if conn.raddr:  # Connexion établie
                        connection_info = {
                            'client_ip': conn.raddr.ip,
                            'client_port': conn.raddr.port,
                            'server_ip': conn.laddr.ip,
                            'server_port': conn.laddr.port,
                            'status': conn.status,
                            'pid': conn.pid,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        connections.append(connection_info)
                        
                        # Ajouter à l'historique
                        self.connection_history[conn.raddr.ip].append(datetime.utcnow())
            
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
                logger.error(f"Erreur ntpq: {result.stderr}")
                return []
            
            peers = []
            lines = result.stdout.strip().split('\n')
            
            # Ignorer les 2 premières lignes (headers)
            for line in lines[2:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
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
            
            return peers
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de l'exécution de ntpq")
            return []
        except FileNotFoundError:
            logger.warning("Commande ntpq non disponible")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de ntpq: {e}")
            return []
    
    def get_ntpq_associations(self) -> List[Dict]:
        """Récupérer les associations NTP via ntpq -as"""
        try:
            result = subprocess.run(['ntpq', '-as'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            associations = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if 'associd' in line:
                    # Parser les informations d'association
                    match = re.search(r'associd=(\d+)', line)
                    if match:
                        assoc_id = match.group(1)
                        associations.append({
                            'association_id': assoc_id,
                            'raw_data': line,
                            'timestamp': datetime.utcnow().isoformat()
                        })
            
            return associations
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des associations: {e}")
            return []
    
    def get_ntp_statistics(self) -> Dict:
        """Récupérer les statistiques du service NTP"""
        try:
            # Statistiques ntpq
            result = subprocess.run(['ntpq', '-c', 'rv'], 
                                  capture_output=True, text=True, timeout=10)
            
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
                'system': '',
                'processor': '',
                'uptime': 0
            }
            
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
            
            # Ajouter les connexions actives
            connections = self.get_active_connections()
            stats['active_connections'] = len(connections)
            stats['unique_clients'] = len(set(conn['client_ip'] for conn in connections))
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'service_status': 'error',
                'error': str(e)
            }
    
    def get_client_statistics(self, hours: int = 24) -> Dict:
        """Récupérer les statistiques des clients sur une période"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Nettoyer l'historique ancien
        for ip in list(self.connection_history.keys()):
            self.connection_history[ip] = [
                ts for ts in self.connection_history[ip] if ts > cutoff_time
            ]
            if not self.connection_history[ip]:
                del self.connection_history[ip]
        
        # Calculer les statistiques
        total_connections = sum(len(timestamps) for timestamps in self.connection_history.values())
        unique_clients = len(self.connection_history)
        
        # Top clients
        top_clients = sorted(
            [(ip, len(timestamps)) for ip, timestamps in self.connection_history.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Connexions par heure
        hourly_stats = defaultdict(int)
        for timestamps in self.connection_history.values():
            for ts in timestamps:
                hour_key = ts.strftime('%Y-%m-%d %H:00')
                hourly_stats[hour_key] += 1
        
        return {
            'period_hours': hours,
            'total_connections': total_connections,
            'unique_clients': unique_clients,
            'average_connections_per_client': total_connections / unique_clients if unique_clients > 0 else 0,
            'top_clients': [{'ip': ip, 'connections': count} for ip, count in top_clients],
            'hourly_connections': dict(hourly_stats),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_connection_stats(self) -> Dict:
        """Récupérer les statistiques de connexion pour le dashboard"""
        try:
            # Connexions actives actuelles
            active_connections = self.get_active_connections()
            
            # Statistiques des clients sur 24h
            client_stats = self.get_client_statistics(hours=24)
            
            # Calculer les connexions totales (historique + actives)
            total_connections = client_stats.get('total_connections', 0)
            
            # Si pas d'historique, compter au moins les connexions actives
            if total_connections == 0:
                total_connections = len(active_connections)
            
            return {
                'active_connections': len(active_connections),
                'total_connections': total_connections,
                'unique_clients': client_stats.get('unique_clients', 0),
                'average_connections_per_client': client_stats.get('average_connections_per_client', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats de connexion: {e}")
            return {
                'active_connections': 0,
                'total_connections': 0,
                'unique_clients': 0,
                'average_connections_per_client': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_service_status(self) -> Dict:
        """Vérifier le status du service NTP"""
        try:
            # Vérifier si le service ntpsec/ntp est actif
            result = subprocess.run(['systemctl', 'is-active', 'ntpsec'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                service_status = 'active'
            else:
                # Essayer avec le service ntp classique
                result = subprocess.run(['systemctl', 'is-active', 'ntp'], 
                                      capture_output=True, text=True)
                service_status = 'active' if result.returncode == 0 else 'inactive'
            
            # Vérifier le port d'écoute
            listening = False
            for conn in psutil.net_connections(kind='udp'):
                if conn.laddr and conn.laddr.port == self.ntp_port:
                    listening = True
                    break
            
            return {
                'service_status': service_status,
                'port_listening': listening,
                'port': self.ntp_port,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du service: {e}")
            return {
                'service_status': 'error',
                'port_listening': False,
                'port': self.ntp_port,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Instance globale du service
client_monitor_service = ClientMonitorService() 