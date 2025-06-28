#!/usr/bin/env python3
"""
Script de diagnostic et correction - Problème "Service inactif / Port undefined"
NTP Monitor Enterprise
"""

import os
import sys
import requests
import subprocess
import time
import json
import psutil
import socket
from pathlib import Path

def print_header(title):
    """Afficher un en-tête stylé"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step, description):
    """Afficher une étape"""
    print(f"\n[{step}] {description}")

def check_application_running():
    """Vérifier si l'application NTP Monitor est en cours d'exécution"""
    print_step("1", "Vérification application NTP Monitor...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/session/check', timeout=5)
        if response.status_code == 200:
            print("✅ Application en cours d'exécution")
            return True
        else:
            print(f"❌ Application répond avec erreur: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Application non accessible sur http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def check_ntp_service_endpoint():
    """Vérifier l'endpoint service/status"""
    print_step("2", "Test de l'endpoint /api/ntp/service/status...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/ntp/service/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint accessible")
            
            # Afficher les données reçues
            print(f"  Service Status: {data.get('service_status', 'undefined')}")
            print(f"  Port: {data.get('port', 'undefined')}")
            print(f"  Port Listening: {data.get('port_listening', 'undefined')}")
            print(f"  Active Connections: {data.get('active_connections', 'undefined')}")
            
            # Vérifier si le port est défini
            if data.get('port') is None or data.get('port') == 'undefined':
                print("❌ PROBLÈME: Port undefined dans la réponse")
                return False, data
            else:
                print("✅ Port correctement défini")
                return True, data
                
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Erreur: {error_data.get('error', 'Unknown')}")
            except:
                print(f"  Réponse: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur de requête: {e}")
        return False, None

def check_ntp_port_listening():
    """Vérifier si le port 123 est en écoute"""
    print_step("3", "Vérification port NTP 123...")
    
    listening = False
    process_info = []
    
    try:
        for conn in psutil.net_connections(kind='udp'):
            if conn.laddr and conn.laddr.port == 123:
                listening = True
                try:
                    if conn.pid:
                        process = psutil.Process(conn.pid)
                        process_info.append({
                            'pid': conn.pid,
                            'name': process.name(),
                            'cmdline': ' '.join(process.cmdline()),
                            'address': f"{conn.laddr.ip}:{conn.laddr.port}"
                        })
                except:
                    pass
        
        if listening:
            print("✅ Port 123 en écoute")
            for proc in process_info:
                print(f"  PID {proc['pid']}: {proc['name']} ({proc['address']})")
        else:
            print("❌ Port 123 non en écoute")
            
        return listening, process_info
        
    except Exception as e:
        print(f"❌ Erreur vérification port: {e}")
        return False, []

def check_ntp_system_service():
    """Vérifier les services NTP système"""
    print_step("4", "Vérification services NTP système...")
    
    services_to_check = ['ntpsec', 'ntp', 'chrony', 'systemd-timesyncd']
    active_services = []
    
    for service in services_to_check:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status = result.stdout.strip()
                print(f"✅ {service}: {status}")
                active_services.append(service)
            else:
                print(f"❌ {service}: inactif")
                
        except subprocess.TimeoutExpired:
            print(f"⏳ {service}: timeout")
        except FileNotFoundError:
            print(f"❓ {service}: systemctl non disponible")
        except Exception as e:
            print(f"❌ {service}: erreur - {e}")
    
    return active_services

def check_network_connectivity():
    """Vérifier la connectivité réseau vers serveurs NTP"""
    print_step("5", "Test connectivité serveurs NTP...")
    
    test_servers = [
        '0.pool.ntp.org',
        '1.pool.ntp.org',
        'time.google.com',
        'pool.ntp.org'
    ]
    
    working_servers = []
    
    for server in test_servers:
        try:
            # Test simple de connectivité
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect((server, 123))
            sock.close()
            print(f"✅ {server}: accessible")
            working_servers.append(server)
        except Exception as e:
            print(f"❌ {server}: {e}")
    
    return working_servers

def fix_client_monitor_service():
    """Corriger le service client_monitor_service"""
    print_step("6", "Correction service client monitoring...")
    
    try:
        # Vérifier le fichier client_monitor_service.py
        service_file = Path('backend/services/client_monitor_service.py')
        
        if not service_file.exists():
            print("❌ Fichier client_monitor_service.py non trouvé")
            return False
        
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si la méthode get_service_status existe et retourne le port
        if 'def get_service_status(self)' in content and "'port': self.ntp_port" in content:
            print("✅ Service client_monitor_service semble correct")
            return True
        else:
            print("❌ Service client_monitor_service nécessite des corrections")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification service: {e}")
        return False

def restart_application():
    """Redémarrer l'application"""
    print_step("7", "Redémarrage de l'application...")
    
    print("⚠️  Pour redémarrer l'application:")
    print("   1. Fermez la fenêtre de l'application actuelle")
    print("   2. Relancez via le raccourci bureau")
    print("   3. Ou exécutez: python app.py")
    
    return True

def generate_diagnostic_report(results):
    """Générer un rapport de diagnostic"""
    print_step("8", "Génération du rapport de diagnostic...")
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'issue': 'Service inactif / Port undefined',
        'application_running': results.get('app_running', False),
        'endpoint_working': results.get('endpoint_ok', False),
        'endpoint_data': results.get('endpoint_data', {}),
        'port_listening': results.get('port_listening', False),
        'ntp_processes': results.get('ntp_processes', []),
        'active_services': results.get('active_services', []),
        'network_connectivity': results.get('network_ok', []),
        'diagnosis': '',
        'recommended_actions': []
    }
    
    # Diagnostic
    if not results.get('app_running'):
        report['diagnosis'] = "Application NTP Monitor non accessible"
        report['recommended_actions'].append("Redémarrer l'application")
    elif not results.get('endpoint_ok'):
        report['diagnosis'] = "Endpoint service/status défaillant"
        report['recommended_actions'].append("Vérifier les logs d'erreur")
        report['recommended_actions'].append("Redémarrer l'application")
    elif not results.get('port_listening'):
        report['diagnosis'] = "Service NTP système non actif"
        report['recommended_actions'].append("Installer et démarrer un service NTP (ntpsec/ntp)")
        report['recommended_actions'].append("Activer systemd-timesyncd comme alternative")
    else:
        report['diagnosis'] = "Configuration semble correcte"
        report['recommended_actions'].append("Actualiser la page web")
    
    # Sauvegarder le rapport
    with open('diagnostic_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("✅ Rapport sauvegardé: diagnostic_report.json")
    return report

def main():
    """Fonction principale de diagnostic"""
    print_header("DIAGNOSTIC NTP MONITOR - Service inactif / Port undefined")
    
    results = {}
    
    # 1. Vérifier application
    results['app_running'] = check_application_running()
    
    if not results['app_running']:
        print("\n🚨 PROBLÈME MAJEUR: Application non accessible")
        print("   Solution: Redémarrer l'application NTP Monitor")
        return
    
    # 2. Vérifier endpoint
    results['endpoint_ok'], results['endpoint_data'] = check_ntp_service_endpoint()
    
    # 3. Vérifier port NTP
    results['port_listening'], results['ntp_processes'] = check_ntp_port_listening()
    
    # 4. Vérifier services système
    results['active_services'] = check_ntp_system_service()
    
    # 5. Vérifier connectivité
    results['network_ok'] = check_network_connectivity()
    
    # 6. Vérifier service client monitor
    results['service_ok'] = fix_client_monitor_service()
    
    # 7. Générer rapport
    report = generate_diagnostic_report(results)
    
    # Résumé et recommandations
    print_header("RÉSUMÉ DU DIAGNOSTIC")
    
    print(f"🔍 Diagnostic: {report['diagnosis']}")
    print("\n📋 Actions recommandées:")
    for i, action in enumerate(report['recommended_actions'], 1):
        print(f"   {i}. {action}")
    
    # Instructions spécifiques
    if not results['port_listening'] and len(results['active_services']) == 0:
        print_header("INSTALLATION SERVICE NTP MANQUANT")
        print("Il semble qu'aucun service NTP ne soit installé/actif.")
        print("\n🔧 Solutions possibles:")
        print("   1. Installer ntpsec: sudo apt install ntpsec")
        print("   2. Ou activer timesyncd: sudo systemctl enable --now systemd-timesyncd")
        print("   3. Redémarrer NTP Monitor après installation")
    
    elif results['endpoint_ok'] and results['port_listening']:
        print_header("SOLUTION SIMPLE")
        print("✅ Tous les services semblent fonctionner correctement.")
        print("🔄 Solution: Actualisez simplement la page web (F5)")
    
    print("\n" + "=" * 60)
    print("📊 Diagnostic terminé. Consultez diagnostic_report.json pour les détails.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Diagnostic interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur durant le diagnostic: {e}")
        import traceback
        traceback.print_exc() 