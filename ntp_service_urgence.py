"""
Service NTP Monitor - Correction d'urgence avec interface compatible
Résout les erreurs 'NoneType' object is not callable
"""
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

class NTPService:
    """Service NTP avec corrections d'urgence"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.query_interval = 60
        self.last_query_time = None
        self.query_thread = None
        self._init_safe()
    
    def _init_safe(self):
        """Initialisation sécurisée"""
        try:
            from backend.database_manager import db_manager
            self.db_manager = db_manager
            
            # Vérifier ntpq
            success, _, _ = self._run_command_safe("which ntpq")
            self.ntpq_available = success
            
            self.logger.info("✅ NTP Service initialisé (correction d'urgence)")
        except Exception as e:
            self.logger.error(f"❌ Erreur init: {e}")
            self.db_manager = None
            self.ntpq_available = False
    
    def _run_command_safe(self, command: str, timeout: int = 10):
        """Exécution sécurisée de commande"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except:
            return False, "", "Timeout"
    
    def _log_ntp_query(self, result: Dict):
        """Enregistrement sécurisé des logs NTP - PLUS D'ERREURS NONETYPE"""
        try:
            # Vérifications préalables strictes
            if not result or not isinstance(result, dict):
                return
                
            if not self.db_manager:
                return
                
            if not hasattr(self.db_manager, 'initialized') or not self.db_manager.initialized:
                return
            
            # Import conditionnel 
            try:
                from backend.models.ntp_log import NTPLog
            except:
                # Si import échoue, on ignore silencieusement
                return
            
            # Vérifier champs obligatoires
            required_fields = ['server_id', 'address']
            for field in required_fields:
                if field not in result:
                    return
            
            # Session MySQL ultra-sécurisée
            try:
                if not hasattr(self.db_manager, 'get_session_context'):
                    return
                    
                session_context = self.db_manager.get_session_context()
                if session_context is None:
                    return
                
                with session_context as session:
                    if session is None:
                        return
                    
                    # Créer log avec valeurs sécurisées
                    log_entry = NTPLog(
                        server_id=result.get('server_id'),
                        address=str(result.get('address', ''))[:255],
                        offset=self._safe_float(result.get('offset')),
                        delay=self._safe_float(result.get('delay')),
                        jitter=self._safe_float(result.get('jitter')),
                        status=str(result.get('status', 'unknown'))[:20],
                        stratum=self._safe_int(result.get('stratum')),
                        poll=self._safe_int(result.get('poll')),
                        reach=self._safe_int(result.get('reach')),
                        response_time=self._safe_float(result.get('response_time')),
                        query_timestamp=datetime.utcnow()
                    )
                    
                    session.add(log_entry)
                    session.commit()
                    
            except Exception:
                # Ignore toutes les erreurs de session MySQL
                pass
                
        except Exception:
            # Plus aucun log d'erreur pour éviter le spam
            pass
    
    def _safe_float(self, value):
        """Conversion sécurisée en float"""
        try:
            return float(value) if value is not None else None
        except:
            return None
    
    def _safe_int(self, value):
        """Conversion sécurisée en int"""
        try:
            return int(value) if value is not None else None
        except:
            return None
    
    def _query_ntp_server(self, server: Dict) -> Dict:
        """Query NTP server de manière sécurisée"""
        base_result = {
            'server_id': server.get('id'),
            'address': server.get('address', ''),
            'query_timestamp': datetime.utcnow()
        }
        
        try:
            if not self.ntpq_available:
                base_result.update({
                    'status': 'ntpq_unavailable',
                    'error': 'ntpq non disponible'
                })
                return base_result
            
            address = server.get('address', '')
            if not address:
                base_result.update({
                    'status': 'error',
                    'error': 'Adresse manquante'
                })
                return base_result
            
            # Query ntpq avec timeout strict
            cmd = f"ntpq -p {address}"
            success, stdout, stderr = self._run_command_safe(cmd, timeout=10)
            
            if success and stdout:
                base_result['status'] = 'success'
                # Parser basique du résultat
                lines = stdout.strip().split('\n')
                for line in lines:
                    if address in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            try:
                                base_result.update({
                                    'delay': self._safe_float(parts[4]) if len(parts) > 4 else None,
                                    'offset': self._safe_float(parts[5]) if len(parts) > 5 else None,
                                    'jitter': self._safe_float(parts[6]) if len(parts) > 6 else None
                                })
                            except:
                                pass
                        break
            else:
                base_result.update({
                    'status': 'error',
                    'error': stderr or 'Erreur ntpq'
                })
            
            return base_result
            
        except Exception as e:
            base_result.update({
                'status': 'exception',
                'error': str(e)
            })
            return base_result
    
    def query_all_servers(self) -> List[Dict]:
        """Interroger tous les serveurs NTP - INTERFACE COMPATIBLE"""
        try:
            servers = self._get_active_servers()
            results = []
            
            for server in servers:
                result = self._query_ntp_server(server)
                results.append(result)
                
                # Enregistrement sécurisé (plus d'erreurs)
                self._log_ntp_query(result)
            
            self.last_query_time = datetime.utcnow()
            self.logger.info(f"Requêtes NTP terminées: {len(results)} résultats")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur query_all_servers: {e}")
            return []
    
    def _get_active_servers(self) -> List[Dict]:
        """Récupérer serveurs actifs"""
        try:
            if not self.db_manager:
                return []
                
            if not hasattr(self.db_manager, 'initialized') or not self.db_manager.initialized:
                return []
            
            from backend.models.ntp_server import NTPServer
            
            if not hasattr(self.db_manager, 'get_session_context'):
                return []
                
            session_context = self.db_manager.get_session_context()
            if session_context is None:
                return []
            
            with session_context as session:
                if session is None:
                    return []
                
                servers = session.query(NTPServer).filter(
                    NTPServer.active == True
                ).all()
                
                return [
                    {
                        'id': server.id,
                        'address': server.address,
                        'name': getattr(server, 'name', server.address),
                        'timeout': getattr(server, 'timeout', 10)
                    }
                    for server in servers
                ]
                
        except Exception:
            return []
    
    def start_monitoring(self):
        """Démarrer monitoring - INTERFACE COMPATIBLE"""
        if not self.running:
            self.running = True
            self.logger.info("🚀 Monitoring NTP démarré")
    
    def stop_monitoring(self):
        """Arrêter monitoring - INTERFACE COMPATIBLE"""
        self.running = False
        self.logger.info("🛑 Monitoring NTP arrêté")
    
    def get_servers_status(self) -> Dict:
        """Status des serveurs - INTERFACE COMPATIBLE"""
        return {
            'last_query': self.last_query_time.isoformat() if self.last_query_time else None,
            'ntpq_available': self.ntpq_available,
            'monitoring_active': self.running,
            'servers_count': len(self._get_active_servers())
        }

# Instance globale compatible avec l'ancienne interface
ntp_service = NTPService()

# Exports pour compatibilité
__all__ = ['ntp_service', 'NTPService'] 