#!/usr/bin/env python3
"""
DIAGNOSTIC HOLISTIQUE FINAL - NTP Monitor Enterprise
Analyse complète et solutions permanentes pour tous les problèmes identifiés
"""

import os
import sys
import subprocess
import logging
import traceback
from datetime import datetime

class DiagnosticHolistique:
    """Diagnostic complet du système NTP Monitor"""
    
    def __init__(self):
        self.rapport = []
        self.problemes = []
        self.solutions = []
        
        # Configuration des chemins
        self.app_path = "/opt/NTPVIZ"
        self.log_file = "/opt/NTPVIZ/logs/app.log"
        self.service_name = "ntp-monitor"
        
        self.log("🚀 DIAGNOSTIC HOLISTIQUE FINAL - NTP Monitor Enterprise")
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
    
    def analyser_logs_erreurs(self):
        """Analyse approfondie des logs d'erreurs"""
        self.log("\n📊 ANALYSE DES LOGS D'ERREURS")
        self.log("-" * 40)
        
        try:
            # Compter les types d'erreurs
            success, stdout, stderr = self.run_command(
                f"tail -1000 {self.log_file} | grep -E 'ERROR|Exception|Traceback' | sort | uniq -c | sort -nr"
            )
            
            if success and stdout:
                self.log("🔍 Top des erreurs les plus fréquentes:")
                for line in stdout.strip().split('\n')[:10]:
                    self.log(f"   {line}")
                    
                    # Identifier les problèmes critiques
                    if "'NoneType' object is not callable" in line:
                        count = line.strip().split()[0]
                        self.problemes.append({
                            'type': 'CRITIQUE',
                            'description': 'Erreur NoneType répétitive',
                            'frequence': int(count),
                            'source': 'ntp_service.py',
                            'impact': 'MAJEUR - Empêche l\'enregistrement des logs NTP'
                        })
            else:
                self.log("❌ Impossible d'analyser les logs")
                
        except Exception as e:
            self.log(f"❌ Erreur analyse logs: {e}")
    
    def analyser_modeles_database(self):
        """Analyse des modèles et de la base de données"""
        self.log("\n🗄️ ANALYSE MODÈLES ET BASE DE DONNÉES")
        self.log("-" * 40)
        
        # Test import des modèles
        models_test = [
            'backend.models.user.User',
            'backend.models.ntp_server.NTPServer',
            'backend.models.ntp_log.NTPLog',
            'backend.models.alert.Alert',
            'backend.models.system_config.SystemConfig'
        ]
        
        models_ok = 0
        models_erreur = 0
        
        for model in models_test:
            success, stdout, stderr = self.run_command(
                f"cd {self.app_path} && /opt/NTPVIZ/.venv/bin/python -c 'import {model.replace('.', '.').rsplit('.', 1)[0]}; print(\"OK\")'"
            )
            
            if success:
                models_ok += 1
                self.log(f"  ✅ {model}")
            else:
                models_erreur += 1
                self.log(f"  ❌ {model}: {stderr}")
                
                self.problemes.append({
                    'type': 'MODELE',
                    'description': f'Problème import modèle {model}',
                    'source': model.split('.')[-2] + '.py',
                    'impact': 'MOYEN - Fonctionnalité réduite'
                })
        
        self.log(f"\n📈 Résumé modèles: {models_ok} OK, {models_erreur} erreurs")
        
        # Test connexion database
        success, stdout, stderr = self.run_command(
            f"cd {self.app_path} && /opt/NTPVIZ/.venv/bin/python -c 'from backend.database_manager import db_manager; print(f\"MySQL OK: {{db_manager.initialized}}\")'"
        )
        
        if success and "MySQL OK: True" in stdout:
            self.log("✅ Database Manager MySQL fonctionnel")
        else:
            self.log(f"❌ Problème Database Manager: {stderr}")
            self.problemes.append({
                'type': 'CRITIQUE',
                'description': 'Database Manager non fonctionnel',
                'source': 'database_manager.py',
                'impact': 'CRITIQUE - Application non fonctionnelle'
            })
    
    def analyser_service_ntp(self):
        """Analyse du service NTP principal"""
        self.log("\n🌐 ANALYSE SERVICE NTP")
        self.log("-" * 40)
        
        # Vérifier les méthodes problématiques
        methodes_a_tester = [
            '_log_ntp_query',
            '_update_server_status_safe',
            'query_all_servers'
        ]
        
        for methode in methodes_a_tester:
            success, stdout, stderr = self.run_command(
                f"grep -n 'def {methode}' {self.app_path}/backend/services/ntp_service.py"
            )
            
            if success:
                self.log(f"  ✅ Méthode {methode} trouvée: ligne {stdout.split(':')[0]}")
            else:
                self.log(f"  ❌ Méthode {methode} manquante")
                
                self.problemes.append({
                    'type': 'SERVICE',
                    'description': f'Méthode {methode} manquante ou défectueuse',
                    'source': 'ntp_service.py',
                    'impact': 'MAJEUR - Erreurs de log répétitives'
                })
        
        # Analyser les imports du service NTP
        success, stdout, stderr = self.run_command(
            f"head -30 {self.app_path}/backend/services/ntp_service.py | grep -E 'import|from'"
        )
        
        if success:
            self.log("📦 Imports du service NTP:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    self.log(f"   {line.strip()}")
    
    def analyser_systeme(self):
        """Analyse de l'environnement système"""
        self.log("\n🖥️ ANALYSE SYSTÈME")
        self.log("-" * 40)
        
        # Service status
        success, stdout, stderr = self.run_command(f"systemctl is-active {self.service_name}")
        self.log(f"Service {self.service_name}: {stdout.strip()}")
        
        # Mémoire utilisée
        success, stdout, stderr = self.run_command(f"systemctl show {self.service_name} --property=MemoryCurrent")
        if success:
            self.log(f"Mémoire: {stdout.strip()}")
        
        # Vérifier ntpq
        success, stdout, stderr = self.run_command("which ntpq")
        if success:
            self.log(f"✅ ntpq disponible: {stdout.strip()}")
        else:
            self.log("❌ ntpq non disponible")
            self.problemes.append({
                'type': 'SYSTEM',
                'description': 'ntpq manquant',
                'source': 'système',
                'impact': 'MOYEN - Monitoring NTP limité'
            })
        
        # Vérifier systemctl
        success, stdout, stderr = self.run_command("which systemctl")
        if success:
            self.log(f"✅ systemctl disponible: {stdout.strip()}")
        else:
            self.log("❌ systemctl non disponible dans PATH")
            self.problemes.append({
                'type': 'SYSTEM',
                'description': 'systemctl PATH incorrect',
                'source': 'système',
                'impact': 'MOYEN - Monitoring service limité'
            })
    
    def generer_solutions(self):
        """Générer des solutions pour tous les problèmes identifiés"""
        self.log("\n🔧 GÉNÉRATION DES SOLUTIONS")
        self.log("-" * 40)
        
        solutions_par_type = {
            'CRITIQUE': [],
            'MAJEUR': [],
            'MOYEN': [],
            'MINEUR': []
        }
        
        for probleme in self.problemes:
            impact = probleme.get('impact', 'MINEUR').split(' - ')[0]
            
            if "'NoneType' object is not callable" in probleme['description']:
                solution = {
                    'probleme': probleme['description'],
                    'solution': 'Corriger la méthode _log_ntp_query dans ntp_service.py',
                    'commandes': [
                        'Vérifier les imports NTPLog',
                        'Réparer la méthode d\'enregistrement des logs',
                        'Ajouter des vérifications de type None'
                    ],
                    'priorite': 'CRITIQUE'
                }
                solutions_par_type['CRITIQUE'].append(solution)
            
            elif 'modèle' in probleme['description'].lower():
                solution = {
                    'probleme': probleme['description'],
                    'solution': 'Réparer les imports et définitions des modèles SQLAlchemy',
                    'commandes': [
                        'Vérifier les imports backend.database',
                        'Réparer les relations SQLAlchemy',
                        'Tester tous les modèles individuellement'
                    ],
                    'priorite': 'MAJEUR'
                }
                solutions_par_type['MAJEUR'].append(solution)
            
            elif 'ntpq' in probleme['description'].lower():
                solution = {
                    'probleme': probleme['description'],
                    'solution': 'Installer et configurer ntpq',
                    'commandes': [
                        'apt install -y ntp ntpdate',
                        'Vérifier le PATH',
                        'Tester ntpq -p'
                    ],
                    'priorite': 'MOYEN'
                }
                solutions_par_type['MOYEN'].append(solution)
        
        # Afficher les solutions par priorité
        for priorite in ['CRITIQUE', 'MAJEUR', 'MOYEN', 'MINEUR']:
            if solutions_par_type[priorite]:
                self.log(f"\n🚨 SOLUTIONS {priorite}:")
                for i, solution in enumerate(solutions_par_type[priorite], 1):
                    self.log(f"  {i}. {solution['probleme']}")
                    self.log(f"     💡 {solution['solution']}")
                    for cmd in solution['commandes']:
                        self.log(f"        - {cmd}")
    
    def creer_script_correction(self):
        """Créer un script de correction automatique"""
        self.log("\n📝 CRÉATION SCRIPT DE CORRECTION")
        self.log("-" * 40)
        
        script_content = """#!/bin/bash
# SCRIPT DE CORRECTION HOLISTIQUE - NTP Monitor Enterprise
# Généré automatiquement par le diagnostic holistique

set -e

echo "🚀 CORRECTION HOLISTIQUE NTP Monitor Enterprise"
echo "=============================================="

# 1. Arrêter le service
echo "🛑 Arrêt du service..."
systemctl stop ntp-monitor

# 2. Sauvegarder les fichiers critiques
echo "💾 Sauvegarde des fichiers..."
cp /opt/NTPVIZ/backend/services/ntp_service.py /opt/NTPVIZ/backend/services/ntp_service.py.backup_holistique
cp /opt/NTPVIZ/backend/database_manager.py /opt/NTPVIZ/backend/database_manager.py.backup_holistique

# 3. Installer les packages système manquants
echo "📦 Installation packages système..."
apt update
apt install -y ntp ntpdate

# 4. Vérifier l'environnement virtuel
echo "🐍 Vérification environnement virtuel..."
source /opt/NTPVIZ/.venv/bin/activate
pip install --upgrade sqlalchemy pymysql flask-login

# 5. Redémarrer le service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor
systemctl status ntp-monitor

echo "✅ Correction holistique terminée!"
"""
        
        try:
            script_path = "/tmp/correction_holistique.sh"
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            self.log(f"✅ Script de correction créé: {script_path}")
            self.solutions.append({
                'type': 'SCRIPT',
                'description': 'Script de correction automatique',
                'path': script_path
            })
        except Exception as e:
            self.log(f"❌ Erreur création script: {e}")
    
    def generer_rapport_final(self):
        """Générer le rapport final complet"""
        self.log("\n📋 RAPPORT FINAL")
        self.log("=" * 50)
        
        self.log(f"\n🔍 PROBLÈMES IDENTIFIÉS: {len(self.problemes)}")
        
        critiques = [p for p in self.problemes if 'CRITIQUE' in p.get('impact', '')]
        majeurs = [p for p in self.problemes if 'MAJEUR' in p.get('impact', '')]
        moyens = [p for p in self.problemes if 'MOYEN' in p.get('impact', '')]
        
        self.log(f"   🚨 Critiques: {len(critiques)}")
        self.log(f"   ⚠️  Majeurs: {len(majeurs)}")
        self.log(f"   ℹ️  Moyens: {len(moyens)}")
        
        if critiques:
            self.log("\n🚨 PROBLÈMES CRITIQUES À CORRIGER EN PRIORITÉ:")
            for p in critiques:
                self.log(f"   - {p['description']} ({p['source']})")
        
        self.log(f"\n💡 SOLUTIONS GÉNÉRÉES: {len(self.solutions)}")
        
        self.log("\n🎯 RECOMMANDATIONS FINALES:")
        self.log("   1. Exécuter le script de correction holistique")
        self.log("   2. Surveiller les logs après correction")
        self.log("   3. Vérifier tous les endpoints de l'API")
        self.log("   4. Tester la connexion web")
        
        # Sauvegarder le rapport
        try:
            rapport_path = f"/tmp/rapport_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(rapport_path, 'w') as f:
                for line in self.rapport:
                    f.write(line + '\n')
            self.log(f"\n📄 Rapport sauvegardé: {rapport_path}")
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde rapport: {e}")
    
    def executer_diagnostic(self):
        """Exécuter le diagnostic complet"""
        try:
            self.analyser_logs_erreurs()
            self.analyser_modeles_database() 
            self.analyser_service_ntp()
            self.analyser_systeme()
            self.generer_solutions()
            self.creer_script_correction()
            self.generer_rapport_final()
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERREUR FATALE: {e}")
            traceback.print_exc()
            return False

def main():
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté en tant que root (sudo)")
        sys.exit(1)
    
    diagnostic = DiagnosticHolistique()
    success = diagnostic.executer_diagnostic()
    
    if success:
        print("\n✅ DIAGNOSTIC HOLISTIQUE TERMINÉ AVEC SUCCÈS!")
        sys.exit(0)
    else:
        print("\n❌ ÉCHEC DU DIAGNOSTIC HOLISTIQUE")
        sys.exit(1)

if __name__ == "__main__":
    main() 