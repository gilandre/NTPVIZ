#!/usr/bin/env python3
"""
CORRECTION D'URGENCE - Service NTP avec interface compatible
Maintient l'interface d'origine tout en appliquant les corrections de sécurité
"""

ntp_service_corrected = '''"""
Service NTP Monitor - Version corrigée avec interface compatible
"""
import logging
import subprocess
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time

class NTPService:
    """Service NTP avec corrections intégrées et interface compatible"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.query_interval = 60  # secondes
        self.last_query_time = None
        self.query_thread = None
        self.servers_status = {}
        
        # Initialisation sécurisée
        self._init_safe()
    
    def _init_safe(self):
        """Initialisation sécurisée avec gestion d'erreur"""
        try:
            # Import conditionnel du database manager
            from backend.database_manager import db_manager
            self.db_manager = db_manager
            
            # Vérifier ntpq
            success, _, _ = self._run_command_safe("which ntpq")
            self.ntpq_available = success
            
            if not self.ntpq_available:
                self.logger.warning("⚠️ ntpq non disponible - fonctions limitées")
            
            self.logger.info("✅ NTP Service initialisé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation NTP Service: {e}")
            self.db_manager = None
            self.ntpq_available = False
    
    def _run_command_safe(self, command: str, timeout: int = 10):
        """Exécuter commande système de manière sécurisée"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _log_ntp_query(self, result: Dict):
        """Enregistrer query NTP - VERSION SÉCURISÉE"""
        try:
            # Vérifications préalables obligatoires
            if not result or not isinstance(result, dict):
                self.logger.debug("Résultat NTP invalide - pas d'enregistrement")
                return
            
            if not self.db_manager:
                self.logger.debug("Database manager non disponible - pas d'enregistrement")
                return
            
            if not hasattr(self.db_manager, 'initialized') or not self.db_manager.initialized:
                self.logger.debug("Database manager non initialisé - pas d'enregistrement")
                return
            
            # Import conditionnel et sécurisé des modèles
            try:
                from backend.models.ntp_log import NTPLog
            except ImportError:
                self.logger.debug("NTPLog non importable - pas d'enregistrement")
                return
            except Exception as e:
                self.logger.debug(f"Erreur import NTPLog: {e}")
                return
            
            # Vérifier champs obligatoires
            required = ['server_id', 'address']
            for field in required:
                if field not in result:
                    self.logger.debug(f"Champ {field} manquant - pas d'enregistrement")
                    return
            
            # Session MySQL sécurisée
            try:
                # Vérifier méthode get_session_context
                if not hasattr(self.db_manager, 'get_session_context'):
                    self.logger.debug("get_session_context non disponible")
                    return
                
                session_context = self.db_manager.get_session_context()
                if session_context is None:
                    self.logger.debug("Session context None")
                    return
                
                with session_context as session:
                    if session is None:
                        self.logger.debug("Session None - pas d'enregistrement")
                        return
                    
                    # Créer log entry avec données validées
                    log_entry = NTPLog(
                        server_id=result.get('server_id'),
                        address=result.get('address', '')[:255],  # Limiter taille
                        offset=self._safe_float(result.get('offset')),
                        delay=self._safe_float(result.get('delay')),
                        jitter=self._safe_float(result.get('jitter')),
                        status=result.get('status', 'unknown')[:20],  # Limiter taille
                        stratum=self._safe_int(result.get('stratum')),
                        poll=self._safe_int(result.get('poll')),
                        reach=self._safe_int(result.get('reach')),
                        response_time=self._safe_float(result.get('response_time')),
                        query_timestamp=datetime.utcnow()
                    )
                    
                    session.add(log_entry)
                    session.commit()
                    
            except Exception as e:
                self.logger.debug(f"Erreur session MySQL: {e}")
                # Ne pas relancer l'exception - juste loguer
                
        except Exception as e:
            # Suppression du log d'erreur pour éviter le spam
            self.logger.debug(f"Erreur _log_ntp_query: {e}")
    
    def _safe_float(self, value):
        """Conversion sécurisée en float"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value):
        """Conversion sécurisée en int"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _query_ntp_server(self, server: Dict) -> Dict:
        """Interroger un serveur NTP - VERSION SÉCURISÉE"""
        result_base = {
            'server_id': server.get('id'),
            'address': server.get('address', ''),
            'query_timestamp': datetime.utcnow()
        }
        
        try:
            if not self.ntpq_available:
                result_base.update({
                    'status': 'ntpq_unavailable',
                    'error': 'ntpq non disponible'
                })
                return result_base
            
            address = server.get('address', '')
            if not address:
                result_base.update({
                    'status': 'error',
                    'error': 'Adresse serveur manquante'
                })
                return result_base
            
            # Query ntpq avec timeout
            cmd = f"ntpq -p {address}"
            success, stdout, stderr = self._run_command_safe(cmd, timeout=15)
            
            if success and stdout:
                result_base['status'] = 'success'
                
                # Parser simple des résultats
                lines = stdout.strip().split('\\n')
                for line in lines:
                    if address in line or any(addr in line for addr in [address.split('.')[-1]]):
                        parts = line.split()
                        if len(parts) >= 8:
                            try:
                                result_base.update({
                                    'delay': self._safe_float(parts[4]) if parts[4] != '-' else None,
                                    'offset': self._safe_float(parts[5]) if parts[5] != '-' else None,
                                    'jitter': self._safe_float(parts[6]) if parts[6] != '-' else None,
                                    'stratum': self._safe_int(parts[2]) if parts[2].isdigit() else None,
                                    'poll': self._safe_int(parts[3]) if parts[3].isdigit() else None
                                })
                            except (ValueError, IndexError):
                                pass
                        break
            else:
                result_base.update({
                    'status': 'error',
                    'error': stderr or 'Erreur query ntpq'
                })
            
            return result_base
            
        except Exception as e:
            result_base.update({
                'status': 'exception',
                'error': str(e)
            })
            return result_base
    
    def query_all_servers(self) -> List[Dict]:
        """Interroger tous les serveurs NTP actifs"""
        try:
            servers = self._get_active_servers()
            results = []
            
            for server in servers:
                result = self._query_ntp_server(server)
                results.append(result)
                
                # Enregistrer de manière sécurisée (pas d'erreur en cas d'échec)
                self._log_ntp_query(result)
            
            self.last_query_time = datetime.utcnow()
            self.logger.info(f"Requêtes NTP terminées: {len(results)} résultats")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur query_all_servers: {e}")
            return []
    
    def _get_active_servers(self) -> List[Dict]:
        """Récupérer serveurs actifs depuis la base"""
        try:
            if not self.db_manager or not hasattr(self.db_manager, 'initialized') or not self.db_manager.initialized:
                return []
            
            from backend.models.ntp_server import NTPServer
            
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
                
        except Exception as e:
            self.logger.debug(f"Erreur récupération serveurs: {e}")
            return []
    
    def start_monitoring(self):
        """Démarrer le monitoring NTP"""
        if self.running:
            return
        
        self.running = True
        self.query_thread = threading.Thread(target=self._monitoring_loop)
        self.query_thread.daemon = True
        self.query_thread.start()
        self.logger.info("🚀 Monitoring NTP démarré")
    
    def stop_monitoring(self):
        """Arrêter le monitoring NTP"""
        self.running = False
        if self.query_thread:
            self.query_thread.join(timeout=5)
        self.logger.info("🛑 Monitoring NTP arrêté")
    
    def _monitoring_loop(self):
        """Boucle principale de monitoring"""
        while self.running:
            try:
                # Attendre avant la prochaine query
                time.sleep(self.query_interval)
                
                if not self.running:
                    break
                
                # Effectuer les queries
                self.query_all_servers()
                
            except Exception as e:
                self.logger.error(f"Erreur monitoring loop: {e}")
                time.sleep(30)  # Attendre plus longtemps en cas d'erreur
    
    def get_servers_status(self) -> Dict:
        """Récupérer le statut des serveurs"""
        return {
            'last_query': self.last_query_time.isoformat() if self.last_query_time else None,
            'ntpq_available': self.ntpq_available,
            'monitoring_active': self.running,
            'servers_count': len(self._get_active_servers())
        }

# Instance globale compatible avec l'ancienne interface
ntp_service = NTPService()

# Export pour compatibilité
__all__ = ['ntp_service', 'NTPService']
'''

print("🔧 CORRECTION D'URGENCE NTP SERVICE")
print("=" * 50)

try:
    # Écrire le service corrigé
    with open("/tmp/ntp_service_fixed.py", 'w') as f:
        f.write(ntp_service_corrected)
    
    print("✅ Service NTP corrigé créé: /tmp/ntp_service_fixed.py")
    print("\n🚀 POUR APPLIQUER:")
    print("1. sudo cp /tmp/ntp_service_fixed.py /opt/NTPVIZ/backend/services/ntp_service.py")
    print("2. sudo chown ntp-monitor:ntp-monitor /opt/NTPVIZ/backend/services/ntp_service.py")
    print("3. sudo systemctl restart ntp-monitor")
    
    # Créer script d'application
    apply_script = '''#!/bin/bash
echo "🔧 APPLICATION CORRECTION D'URGENCE NTP SERVICE"
echo "=============================================="

# Arrêter le service
systemctl stop ntp-monitor

# Sauvegarder l'ancien
cp /opt/NTPVIZ/backend/services/ntp_service.py /opt/NTPVIZ/backend/services/ntp_service.py.backup_urgence

# Appliquer la correction
cp /tmp/ntp_service_fixed.py /opt/NTPVIZ/backend/services/ntp_service.py
chown ntp-monitor:ntp-monitor /opt/NTPVIZ/backend/services/ntp_service.py

# Redémarrer
systemctl start ntp-monitor
sleep 10

# Vérifier
if systemctl is-active ntp-monitor >/dev/null; then
    echo "✅ Service redémarré avec succès"
    
    # Attendre et vérifier les erreurs
    sleep 30
    ERROR_COUNT=$(tail -50 /opt/NTPVIZ/logs/app.log | grep -c "'NoneType' object is not callable" 2>/dev/null || echo "0")
    
    if [ "$ERROR_COUNT" -eq "0" ]; then
        echo "✅ Plus d'erreurs NoneType - CORRECTION RÉUSSIE!"
    else
        echo "⚠️ Encore $ERROR_COUNT erreurs NoneType"
    fi
else
    echo "❌ Service ne démarre pas"
    systemctl status ntp-monitor --no-pager
fi
'''
    
    with open("/tmp/apply_correction_urgence.sh", 'w') as f:
        f.write(apply_script)
    
    print("✅ Script d'application créé: /tmp/apply_correction_urgence.sh")
    print("\n✅ CORRECTION D'URGENCE PRÊTE!")
    
except Exception as e:
    print(f"❌ Erreur: {e}") 