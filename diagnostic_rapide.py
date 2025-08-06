#!/usr/bin/env python3
"""
Script de diagnostic rapide - NTP Monitor
Analyse les logs et l'état de l'application en temps réel
"""

import os
import sys
import time
import subprocess
import requests
from datetime import datetime, timedelta
import json

def check_application_status():
    """Vérifier l'état de l'application"""
    print("🔍 Vérification de l'état de l'application...")
    
    try:
        # Test de connectivité
        response = requests.get('http://localhost:5001/api/dashboard/summary', timeout=5)
        if response.status_code == 200:
            print("   ✅ Application accessible sur port 5001")
            return True
        else:
            print(f"   ❌ Application répond avec code {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Application inaccessible: {e}")
        return False

def analyze_recent_logs(minutes=10):
    """Analyser les logs récents"""
    print(f"\n📋 Analyse des logs des {minutes} dernières minutes...")
    
    if not os.path.exists('logs/app.log'):
        print("   ❌ Fichier de log non trouvé")
        return
    
    try:
        # Lire les dernières lignes du log
        result = subprocess.run(['tail', '-500', 'logs/app.log'], 
                              capture_output=True, text=True)
        logs = result.stdout
        
        # Analyser les patterns
        errors = {
            'serveurs_indisponibles': 0,
            'offset_critical': 0,
            'latence_critical': 0,
            'erreurs_http': 0,
            'exceptions': 0
        }
        
        for line in logs.split('\n'):
            if 'No response received' in line:
                errors['serveurs_indisponibles'] += 1
            elif 'Offset critical' in line:
                errors['offset_critical'] += 1
            elif 'Latence critical' in line:
                errors['latence_critical'] += 1
            elif 'HTTP/1.1" 5' in line:  # Erreurs 5xx
                errors['erreurs_http'] += 1
            elif 'Exception' in line or 'Error' in line:
                errors['exceptions'] += 1
        
        # Afficher les résultats
        print("   📊 Résumé des problèmes détectés :")
        for problem, count in errors.items():
            if count > 0:
                icon = "🔴" if count > 10 else "🟠" if count > 5 else "🟡"
                print(f"      {icon} {problem.replace('_', ' ').title()}: {count}")
            else:
                print(f"      ✅ {problem.replace('_', ' ').title()}: {count}")
        
        return errors
        
    except Exception as e:
        print(f"   ❌ Erreur analyse logs: {e}")
        return None

def check_ntp_servers():
    """Vérifier l'état des serveurs NTP problématiques"""
    print("\n🌐 Test de connectivité des serveurs NTP...")
    
    problematic_servers = ['192.168.7.28', '70.137.36.66']
    
    for server in problematic_servers:
        print(f"   🔍 Test de {server}...")
        try:
            # Test de ping simple
            result = subprocess.run(['ping', '-c', '1', '-W', '2000', server], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"      ✅ {server} - Ping OK")
                
                # Test NTP si ping OK
                try:
                    ntp_result = subprocess.run(['ntpdate', '-q', server], 
                                              capture_output=True, text=True, timeout=10)
                    if ntp_result.returncode == 0:
                        print(f"      ✅ {server} - Service NTP OK")
                    else:
                        print(f"      ❌ {server} - Service NTP non responsive")
                except subprocess.TimeoutExpired:
                    print(f"      ⏱️ {server} - Timeout NTP (>10s)")
                except Exception as e:
                    print(f"      ❌ {server} - Erreur test NTP: {e}")
            else:
                print(f"      ❌ {server} - Ping échoué")
                
        except subprocess.TimeoutExpired:
            print(f"      ⏱️ {server} - Timeout ping")
        except Exception as e:
            print(f"      ❌ {server} - Erreur: {e}")

def check_system_resources():
    """Vérifier l'utilisation des ressources système"""
    print("\n💻 Vérification des ressources système...")
    
    try:
        # Espace disque
        result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            disk_info = lines[1].split()
            used_percent = disk_info[4].rstrip('%')
            print(f"   💾 Espace disque utilisé: {used_percent}%")
            
            if int(used_percent) > 90:
                print("      🔴 ATTENTION: Espace disque critique")
            elif int(used_percent) > 80:
                print("      🟠 ATTENTION: Espace disque élevé")
            else:
                print("      ✅ Espace disque OK")
        
        # Taille du fichier de log
        if os.path.exists('logs/app.log'):
            log_size = os.path.getsize('logs/app.log') / (1024 * 1024)  # MB
            print(f"   📋 Taille du log: {log_size:.1f} MB")
            
            if log_size > 100:
                print("      🟠 ATTENTION: Fichier de log volumineux")
            else:
                print("      ✅ Taille du log OK")
        
        # Charge système (si disponible)
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().split()[0]
                print(f"   ⚡ Charge système: {load}")
        except:
            pass  # Pas disponible sur macOS
            
    except Exception as e:
        print(f"   ❌ Erreur vérification ressources: {e}")

def get_api_metrics():
    """Obtenir des métriques via l'API"""
    print("\n📊 Récupération des métriques via API...")
    
    endpoints = [
        '/api/dashboard/summary',
        '/api/alerts/summary', 
        '/api/admin/stats/overview'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:5001{endpoint}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {endpoint} - OK")
                
                # Afficher quelques métriques clés
                if endpoint == '/api/alerts/summary':
                    if 'active' in data:
                        print(f"      📊 Alertes actives: {data['active']}")
                elif endpoint == '/api/admin/stats/overview':
                    if 'servers' in data:
                        print(f"      📊 Serveurs: {data['servers'].get('active', 0)}/{data['servers'].get('total', 0)}")
                    if 'alerts' in data:
                        print(f"      📊 Alertes: {data['alerts'].get('active', 0)} actives")
            else:
                print(f"   ❌ {endpoint} - Code {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} - Erreur: {e}")

def main():
    """Fonction principale de diagnostic"""
    print("=" * 70)
    print("🔧 DIAGNOSTIC RAPIDE - NTP MONITOR")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Tests principaux
    app_running = check_application_status()
    
    if app_running:
        log_errors = analyze_recent_logs(10)
        check_ntp_servers()
        check_system_resources()
        get_api_metrics()
    else:
        print("\n❌ Application non accessible - diagnostic limité")
        analyze_recent_logs(30)  # Analyser plus de logs si app down
    
    # Recommandations
    print("\n" + "=" * 70)
    print("📋 RECOMMANDATIONS")
    print("=" * 70)
    
    if app_running:
        print("✅ Application fonctionnelle")
        
        if log_errors:
            if log_errors['serveurs_indisponibles'] > 5:
                print("🔴 PRIORITÉ: Vérifier la connectivité des serveurs NTP")
            if log_errors['offset_critical'] > 20:
                print("🟠 ATTENTION: Nombreuses alertes d'offset critique")
            if log_errors['latence_critical'] > 20:
                print("🟠 ATTENTION: Nombreuses alertes de latence critique")
    else:
        print("🔴 PRIORITÉ: Redémarrer l'application")
        print("   Commande: python restart_app.py")
    
    print("\n💡 Actions suggérées:")
    print("   • Surveiller les logs: tail -f logs/app.log")
    print("   • Interface web: http://localhost:5001")
    print("   • Relancer diagnostic: python diagnostic_rapide.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Diagnostic interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1) 