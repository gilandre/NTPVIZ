#!/usr/bin/env python3
"""
Script de redémarrage automatique de l'application NTP Monitor
Usage: python restart_app.py
"""

import os
import signal
import subprocess
import sys
import time
import psutil

def find_app_processes():
    """Trouve tous les processus Python exécutant app.py"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' or 'python' in proc.info['name']:
                cmdline = proc.info['cmdline']
                if cmdline and any('app.py' in arg for arg in cmdline):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def kill_app_processes():
    """Arrête tous les processus de l'application"""
    processes = find_app_processes()
    
    if not processes:
        print("🔍 Aucun processus app.py trouvé")
        return True
    
    print(f"🔄 Arrêt de {len(processes)} processus app.py...")
    
    for proc in processes:
        try:
            print(f"   ⏹️  Arrêt du processus PID {proc.pid}")
            proc.terminate()  # Envoi SIGTERM
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Attendre que les processus s'arrêtent proprement
    time.sleep(2)
    
    # Vérifier s'il reste des processus et les forcer à s'arrêter
    remaining = find_app_processes()
    if remaining:
        print("⚠️  Forçage de l'arrêt des processus restants...")
        for proc in remaining:
            try:
                proc.kill()  # Envoi SIGKILL
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(1)
    
    # Vérification finale
    final_check = find_app_processes()
    if final_check:
        print(f"❌ Impossible d'arrêter {len(final_check)} processus")
        return False
    else:
        print("✅ Tous les processus arrêtés avec succès")
        return True

def start_app():
    """Démarre l'application"""
    print("🚀 Démarrage de l'application...")
    
    # Vérifier si nous sommes dans le bon répertoire
    if not os.path.exists('app.py'):
        print("❌ Fichier app.py non trouvé dans le répertoire courant")
        print(f"   Répertoire courant: {os.getcwd()}")
        return False
    
    # Vérifier si l'environnement virtuel est activé
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not venv_active:
        print("⚠️  Environnement virtuel non détecté")
        print("   Tentative de démarrage avec Python système...")
    else:
        print("✅ Environnement virtuel détecté")
    
    try:
        # Démarrer l'application en arrière-plan
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre un peu pour voir si l'application démarre correctement
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ Application démarrée avec succès (PID: {process.pid})")
            print("🌐 Application accessible sur http://localhost:5001")
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ L'application a échoué au démarrage")
            if stdout:
                print(f"STDOUT: {stdout}")
            if stderr:
                print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔄 SCRIPT DE REDÉMARRAGE - NTP MONITOR")
    print("=" * 60)
    print()
    
    # Étape 1: Arrêter l'application
    print("📋 Étape 1: Arrêt de l'application")
    if not kill_app_processes():
        print("❌ Impossible d'arrêter l'application")
        sys.exit(1)
    
    print()
    
    # Étape 2: Attendre un peu
    print("⏳ Attente de 2 secondes...")
    time.sleep(2)
    
    # Étape 3: Démarrer l'application
    print("📋 Étape 2: Démarrage de l'application")
    if not start_app():
        print("❌ Impossible de démarrer l'application")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🎉 REDÉMARRAGE TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)
    print()
    print("🔗 Liens utiles:")
    print("   • Application: http://localhost:5001")
    print("   • Test Canvas: http://localhost:5001/test-canvas-elements")
    print("   • Admin Modal: Cliquer sur 'Administration Système'")
    print()
    print("💡 Conseil: Ouvrez F12 → Console pour voir les logs de debug")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du script par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1) 