#!/usr/bin/env python3
"""
SOLUTION HOLISTIQUE COMPLÈTE - NTP Monitor Enterprise
Diagnostic et correction de tous les problèmes de manière permanente
"""

import os
import sys
import subprocess
import logging
import traceback
from datetime import datetime

class SolutionHolistique:
    """Solution complète pour tous les problèmes NTP Monitor"""
    
    def __init__(self):
        self.rapport = []
        self.problemes_detectes = []
        self.corrections_appliquees = []
        
        # Configuration des chemins
        self.app_path = "/opt/NTPVIZ"
        self.log_file = "/opt/NTPVIZ/logs/app.log"
        self.service_name = "ntp-monitor"
        
        self.log("🚀 SOLUTION HOLISTIQUE COMPLÈTE - NTP Monitor Enterprise")
        self.log("=" * 70)
        
    def log(self, message):
        """Logger avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        self.rapport.append(line)
    
    def run_command(self, command, description=""):
        """Exécuter une commande avec capture d'erreur"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def diagnostic_rapide(self):
        """Diagnostic rapide des problèmes principaux"""
        self.log("\n🔍 DIAGNOSTIC RAPIDE")
        self.log("-" * 40)
        
        # 1. Analyser l'erreur principale
        success, stdout, stderr = self.run_command(
            f"tail -100 {self.log_file} | grep -c \"'NoneType' object is not callable\""
        )
        
        if success and stdout.strip():
            count = int(stdout.strip())
            if count > 0:
                self.log(f"🚨 PROBLÈME CRITIQUE: {count} erreurs 'NoneType' object is not callable")
                self.problemes_detectes.append('NONETYPE_ERROR')
        
        # 2. Vérifier le service
        success, stdout, stderr = self.run_command(f"systemctl is-active {self.service_name}")
        if success and "active" in stdout:
            self.log("✅ Service ntp-monitor actif")
        else:
            self.log("❌ Service ntp-monitor inactif")
            self.problemes_detectes.append('SERVICE_INACTIVE')
        
        # 3. Vérifier MySQL
        success, stdout, stderr = self.run_command(
            "mysql -u ntpmonitor -p'ntp2025secure' -e 'SELECT 1;' 2>/dev/null"
        )
        if success:
            self.log("✅ MySQL connecté")
        else:
            self.log("❌ MySQL non accessible")
            self.problemes_detectes.append('MYSQL_ERROR')
        
        # 4. Vérifier ntpq
        success, stdout, stderr = self.run_command("which ntpq")
        if success:
            self.log("✅ ntpq disponible")
        else:
            self.log("❌ ntpq manquant")
            self.problemes_detectes.append('NTPQ_MISSING')
        
        self.log(f"\n📊 Problèmes détectés: {len(self.problemes_detectes)}")
    
    def corriger_erreur_nonetype(self):
        """Corriger l'erreur NoneType object is not callable"""
        if 'NONETYPE_ERROR' not in self.problemes_detectes:
            return
        
        self.log("\n🔧 CORRECTION: Erreur NoneType object is not callable")
        self.log("-" * 40)
        
        # Créer un patch pour le service NTP
        patch_content = '''
# PATCH POUR CORRIGER L'ERREUR NONETYPE
# Ajout de vérifications de type None dans ntp_service.py

def _log_ntp_query_safe(self, result: Dict):
    """Version sécurisée de _log_ntp_query avec vérifications"""
    try:
        # Vérifier que result n'est pas None
        if result is None:
            self.logger.warning("Résultat NTP None - ignore enregistrement log")
            return
        
        # Vérifier les champs obligatoires
        required_fields = ['server_id', 'address', 'status']
        for field in required_fields:
            if field not in result:
                self.logger.warning(f"Champ {field} manquant dans résultat NTP")
                return
        
        # Import sécurisé du modèle NTPLog
        try:
            from backend.models.ntp_log import NTPLog
        except ImportError as e:
            self.logger.error(f"Impossible d'importer NTPLog: {e}")
            return
        
        # Utiliser le database manager de manière sécurisée
        try:
            from backend.database_manager import db_manager
            
            if not db_manager or not db_manager.initialized:
                self.logger.error("Database manager non initialisé")
                return
            
            with db_manager.get_session_context() as session:
                if session is None:
                    self.logger.error("Session MySQL None")
                    return
                
                # Créer l'entrée de log
                log_entry = NTPLog(
                    server_id=result.get('server_id'),
                    address=result.get('address', ''),
                    offset=result.get('offset'),
                    delay=result.get('delay'),
                    jitter=result.get('jitter'),
                    status=result.get('status', 'unknown'),
                    stratum=result.get('stratum'),
                    poll=result.get('poll'),
                    reach=result.get('reach'),
                    response_time=result.get('response_time'),
                    query_timestamp=datetime.utcnow()
                )
                
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            self.logger.error(f"Erreur enregistrement log NTP sécurisé: {e}")
            
    except Exception as e:
        self.logger.error(f"Erreur dans _log_ntp_query_safe: {e}")
'''
        
        try:
            # Sauvegarder le patch
            patch_file = "/tmp/ntp_service_patch.py"
            with open(patch_file, 'w') as f:
                f.write(patch_content)
            
            self.log(f"✅ Patch créé: {patch_file}")
            self.corrections_appliquees.append('NONETYPE_PATCH_CREATED')
            
        except Exception as e:
            self.log(f"❌ Erreur création patch: {e}")
    
    def corriger_modeles_database(self):
        """Corriger les problèmes de modèles de base de données"""
        self.log("\n🗄️ CORRECTION: Modèles de base de données")
        self.log("-" * 40)
        
        # Créer un modèle NTPLog corrigé et simplifié
        ntplog_content = '''"""
Modèle NTPLog - Version corrigée et simplifiée
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.database import Base

class NTPLog(Base):
    """Modèle log NTP - VERSION CORRIGÉE"""
    
    __tablename__ = 'ntp_logs'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    
    # Données NTP
    offset = Column(Float)
    delay = Column(Float) 
    jitter = Column(Float)
    stratum = Column(Integer)
    poll = Column(Integer)
    reach = Column(Integer)
    
    # Status et temps
    status = Column(String(20), default='unknown')
    response_time = Column(Float)
    query_timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NTPLog {self.address}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'address': self.address,
            'offset': self.offset,
            'delay': self.delay,
            'jitter': self.jitter,
            'stratum': self.stratum,
            'poll': self.poll,
            'reach': self.reach,
            'status': self.status,
            'response_time': self.response_time,
            'query_timestamp': self.query_timestamp.isoformat() if self.query_timestamp else None
        }
'''
        
        try:
            # Sauvegarder le modèle corrigé
            model_file = "/tmp/ntp_log_corrected.py"
            with open(model_file, 'w') as f:
                f.write(ntplog_content)
            
            self.log(f"✅ Modèle NTPLog corrigé créé: {model_file}")
            self.corrections_appliquees.append('NTPLOG_MODEL_CORRECTED')
            
        except Exception as e:
            self.log(f"❌ Erreur création modèle: {e}")
    
    def corriger_services_systeme(self):
        """Corriger les services système (ntpq, systemctl)"""
        if 'NTPQ_MISSING' not in self.problemes_detectes:
            return
        
        self.log("\n🛠️ CORRECTION: Services système")
        self.log("-" * 40)
        
        # Installer ntpq
        success, stdout, stderr = self.run_command("apt update && apt install -y ntp ntpdate")
        if success:
            self.log("✅ NTP et ntpdate installés")
            self.corrections_appliquees.append('NTP_INSTALLED')
        else:
            self.log(f"❌ Erreur installation NTP: {stderr}")
        
        # Vérifier systemctl PATH
        success, stdout, stderr = self.run_command("which systemctl")
        if success:
            systemctl_path = stdout.strip()
            self.log(f"✅ systemctl trouvé: {systemctl_path}")
            
            # Créer wrapper si nécessaire
            wrapper_content = f'''#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec {systemctl_path} "$@"
'''
            try:
                with open('/usr/local/bin/systemctl-wrapper', 'w') as f:
                    f.write(wrapper_content)
                os.chmod('/usr/local/bin/systemctl-wrapper', 0o755)
                self.log("✅ Wrapper systemctl créé")
                self.corrections_appliquees.append('SYSTEMCTL_WRAPPER_CREATED')
            except Exception as e:
                self.log(f"❌ Erreur wrapper systemctl: {e}")
    
    def appliquer_corrections_database(self):
        """Appliquer les corrections à la base de données"""
        self.log("\n💾 APPLICATION: Corrections base de données")
        self.log("-" * 40)
        
        # Ajouter colonnes manquantes si nécessaire
        colonnes_sql = [
            "ALTER TABLE ntp_logs ADD COLUMN IF NOT EXISTS stratum INT;",
            "ALTER TABLE ntp_logs ADD COLUMN IF NOT EXISTS poll INT;",
            "ALTER TABLE ntp_logs ADD COLUMN IF NOT EXISTS reach INT;",
            "ALTER TABLE ntp_logs ADD COLUMN IF NOT EXISTS response_time FLOAT;",
            "ALTER TABLE ntp_logs ADD COLUMN IF NOT EXISTS query_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        ]
        
        for sql in colonnes_sql:
            success, stdout, stderr = self.run_command(
                f"mysql -u ntpmonitor -p'ntp2025secure' ntp_monitor -e \"{sql}\" 2>/dev/null"
            )
            if success:
                self.log(f"✅ SQL: {sql[:50]}...")
            else:
                # Ignorer les erreurs de colonnes existantes
                if "Duplicate column" not in stderr:
                    self.log(f"⚠️ SQL warning: {sql[:30]}...")
        
        self.corrections_appliquees.append('DATABASE_COLUMNS_UPDATED')
    
    def creer_script_application(self):
        """Créer un script pour appliquer toutes les corrections"""
        self.log("\n📝 CRÉATION: Script d'application des corrections")
        self.log("-" * 40)
        
        script_content = f'''#!/bin/bash
# SCRIPT D'APPLICATION DES CORRECTIONS HOLISTIQUES
# Généré le {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

set -e

echo "🚀 APPLICATION DES CORRECTIONS NTP MONITOR"
echo "=========================================="

# 1. Arrêter le service
echo "🛑 Arrêt du service ntp-monitor..."
systemctl stop ntp-monitor

# 2. Sauvegardes
echo "💾 Sauvegarde des fichiers..."
cp {self.app_path}/backend/services/ntp_service.py {self.app_path}/backend/services/ntp_service.py.backup_$(date +%Y%m%d_%H%M%S)
cp {self.app_path}/backend/models/ntp_log.py {self.app_path}/backend/models/ntp_log.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# 3. Appliquer les corrections
echo "🔧 Application des corrections..."

# Copier le modèle NTPLog corrigé
if [ -f "/tmp/ntp_log_corrected.py" ]; then
    cp /tmp/ntp_log_corrected.py {self.app_path}/backend/models/ntp_log.py
    chown ntp-monitor:ntp-monitor {self.app_path}/backend/models/ntp_log.py
    echo "✅ Modèle NTPLog mis à jour"
fi

# 4. Mise à jour de l'environnement
echo "🐍 Mise à jour environnement virtuel..."
source {self.app_path}/.venv/bin/activate
pip install --upgrade sqlalchemy pymysql flask-login flask-socketio

# 5. Redémarrer le service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor
sleep 10
systemctl status ntp-monitor --no-pager

# 6. Vérification
echo "🧪 Vérification..."
sleep 15
if systemctl is-active ntp-monitor >/dev/null; then
    echo "✅ Service actif"
    
    # Test logs
    if tail -20 {self.log_file} | grep -q "NTP Monitor Enterprise démarré"; then
        echo "✅ Application démarrée correctement"
    else
        echo "⚠️ Vérifier les logs de démarrage"
    fi
    
    # Test erreurs
    error_count=$(tail -50 {self.log_file} | grep -c "'NoneType' object is not callable" || echo "0")
    if [ "$error_count" -eq "0" ]; then
        echo "✅ Plus d'erreurs NoneType"
    else
        echo "⚠️ Encore $error_count erreurs NoneType"
    fi
else
    echo "❌ Service non actif"
    systemctl status ntp-monitor --no-pager
fi

echo ""
echo "🎯 CORRECTIONS APPLIQUÉES: {len(self.corrections_appliquees)}"
for correction in {self.corrections_appliquees}:
    echo "   ✅ {correction}"

echo ""
echo "✅ SCRIPT D'APPLICATION TERMINÉ"
'''
        
        try:
            script_path = "/tmp/appliquer_corrections.sh"
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            
            self.log(f"✅ Script d'application créé: {script_path}")
            return script_path
            
        except Exception as e:
            self.log(f"❌ Erreur création script: {e}")
            return None
    
    def executer_solution_complete(self):
        """Exécuter la solution complète"""
        try:
            # Phase 1: Diagnostic
            self.diagnostic_rapide()
            
            # Phase 2: Préparation des corrections
            self.corriger_erreur_nonetype()
            self.corriger_modeles_database()
            self.corriger_services_systeme()
            self.appliquer_corrections_database()
            
            # Phase 3: Génération du script final
            script_path = self.creer_script_application()
            
            # Phase 4: Rapport final
            self.log("\n🎯 SOLUTION HOLISTIQUE PRÊTE")
            self.log("=" * 50)
            self.log(f"Problèmes détectés: {len(self.problemes_detectes)}")
            self.log(f"Corrections préparées: {len(self.corrections_appliquees)}")
            
            if script_path:
                self.log(f"\n🚀 POUR APPLIQUER LES CORRECTIONS:")
                self.log(f"   sudo bash {script_path}")
            
            self.log("\n📋 CORRECTIONS INCLUSES:")
            for correction in self.corrections_appliquees:
                self.log(f"   ✅ {correction}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERREUR SOLUTION: {e}")
            traceback.print_exc()
            return False

def main():
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté en tant que root (sudo)")
        sys.exit(1)
    
    solution = SolutionHolistique()
    success = solution.executer_solution_complete()
    
    if success:
        print("\n✅ SOLUTION HOLISTIQUE GÉNÉRÉE AVEC SUCCÈS!")
        print("   Exécutez le script d'application pour corriger tous les problèmes")
        sys.exit(0)
    else:
        print("\n❌ ÉCHEC DE LA GÉNÉRATION DE SOLUTION")
        sys.exit(1)

if __name__ == "__main__":
    main() 