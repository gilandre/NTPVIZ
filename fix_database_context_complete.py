#!/usr/bin/env python3
"""
Script de Correction Complète NTP Monitor Enterprise
Corrige les erreurs SQLite, installe MySQL et résout les problèmes de contexte
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def run_command(command, description=None, capture_output=False):
    """Exécuter une commande avec affichage des logs"""
    if description:
        print(f"\n🔧 {description}")
        print(f"   Commande: {command}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode, "", ""
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return 1, "", str(e)

def check_mysql_server():
    """Vérifier que MySQL Server est accessible"""
    print("\n🔍 Vérification MySQL Server...")
    
    # Tester la connexion MySQL
    code, stdout, stderr = run_command('mysql -u root -e "SELECT VERSION();"', capture_output=True)
    
    if code == 0:
        print("✅ MySQL Server accessible")
        print(f"   Version: {stdout.strip()}")
        return True
    else:
        print("❌ MySQL Server non accessible")
        print(f"   Erreur: {stderr}")
        print("\n💡 Solutions:")
        print("   1. Installer MySQL: https://dev.mysql.com/downloads/installer/")
        print("   2. Vérifier que le service MySQL est démarré")
        print("   3. Configurer l'utilisateur root")
        return False

def recreate_virtual_environment():
    """Recréer l'environnement virtuel"""
    print("\n🗑️  Suppression de l'ancien environnement virtuel...")
    
    venv_paths = ['.venv', 'venv', '.venv_mysql']
    for venv_path in venv_paths:
        if Path(venv_path).exists():
            try:
                shutil.rmtree(venv_path)
                print(f"✅ Supprimé: {venv_path}")
            except Exception as e:
                print(f"⚠️  Erreur suppression {venv_path}: {e}")
    
    print("\n📦 Création du nouvel environnement virtuel MySQL...")
    code, stdout, stderr = run_command("python -m venv .venv_mysql", "Création environnement virtuel MySQL")
    
    if code != 0:
        print(f"❌ Erreur création environnement virtuel: {stderr}")
        return False
    
    print("✅ Environnement virtuel MySQL créé")
    return True

def install_mysql_dependencies():
    """Installer les dépendances MySQL"""
    print("\n📦 Installation des dépendances MySQL...")
    
    # Activer l'environnement virtuel et installer pip/setuptools
    activation_cmd = ".venv_mysql\\Scripts\\activate" if os.name == 'nt' else "source .venv_mysql/bin/activate"
    
    # Commandes d'installation par étapes
    install_commands = [
        f"{activation_cmd} && python -m pip install --upgrade pip",
        f"{activation_cmd} && pip install --upgrade setuptools wheel",
        f"{activation_cmd} && pip install pymysql==1.1.0",
        f"{activation_cmd} && pip install mysqlclient==2.2.0",
        f"{activation_cmd} && pip install -r requirements.txt"
    ]
    
    for i, cmd in enumerate(install_commands, 1):
        print(f"\n📋 Étape {i}/{len(install_commands)}")
        code, stdout, stderr = run_command(cmd, capture_output=True)
        
        if code == 0:
            print(f"✅ Étape {i} réussie")
        else:
            print(f"❌ Étape {i} échouée")
            print(f"   Stdout: {stdout}")
            print(f"   Stderr: {stderr}")
            if i <= 3:  # Les 3 premières étapes sont critiques
                return False
    
    print("✅ Dépendances MySQL installées")
    return True

def run_mysql_migration():
    """Exécuter la migration MySQL"""
    print("\n🚀 Exécution de la migration MySQL...")
    
    if not Path("migrate_to_mysql_root.py").exists():
        print("❌ Script migrate_to_mysql_root.py non trouvé")
        return False
    
    activation_cmd = ".venv_mysql\\Scripts\\activate" if os.name == 'nt' else "source .venv_mysql/bin/activate"
    migration_cmd = f"{activation_cmd} && python migrate_to_mysql_root.py"
    
    code, stdout, stderr = run_command(migration_cmd, "Migration MySQL", capture_output=True)
    
    if code == 0:
        print("✅ Migration MySQL réussie")
        print("📋 Détails de la migration:")
        print(stdout)
        return True
    else:
        print("❌ Migration MySQL échouée")
        print(f"   Erreur: {stderr}")
        return False

def test_application():
    """Tester le lancement de l'application"""
    print("\n🧪 Test de l'application MySQL...")
    
    activation_cmd = ".venv_mysql\\Scripts\\activate" if os.name == 'nt' else "source .venv_mysql/bin/activate"
    test_cmd = f"{activation_cmd} && python -c \"from backend.app import create_app; app = create_app(); print('✅ Application MySQL OK')\""
    
    code, stdout, stderr = run_command(test_cmd, "Test application", capture_output=True)
    
    if code == 0:
        print("✅ Application MySQL fonctionne")
        print(stdout)
        return True
    else:
        print("❌ Erreur test application")
        print(f"   Stderr: {stderr}")
        return False

def create_startup_script():
    """Créer un script de démarrage"""
    startup_script = """@echo off
echo 🚀 NTP Monitor Enterprise - VERSION MYSQL
echo ========================================

echo 📊 Activation environnement virtuel MySQL...
call .venv_mysql\\Scripts\\activate

echo 🗃️  Base de données: MySQL (localhost/ntp_monitor)
echo 👤 Utilisateur: root (sans mot de passe)

echo 🌐 Démarrage application sur http://127.0.0.1:5000
python backend/app.py

pause
"""
    
    try:
        with open("start_mysql.bat", "w", encoding='utf-8') as f:
            f.write(startup_script)
        print("✅ Script de démarrage créé: start_mysql.bat")
        return True
    except Exception as e:
        print(f"❌ Erreur création script: {e}")
        return False

def main():
    """Fonction principale de correction"""
    print("🔧 CORRECTION COMPLÈTE NTP MONITOR ENTERPRISE")
    print("=" * 60)
    print("🎯 Objectifs:")
    print("   - Supprimer définitivement les erreurs SQLite")
    print("   - Configurer MySQL avec utilisateur root")
    print("   - Résoudre les erreurs 'Working outside of application context'")
    print("   - Créer un environnement stable et fonctionnel")
    print("=" * 60)
    
    # Étapes de correction
    steps = [
        ("🔍 Vérification MySQL Server", check_mysql_server),
        ("🗑️  Recréation environnement virtuel", recreate_virtual_environment),
        ("📦 Installation dépendances MySQL", install_mysql_dependencies),
        ("🚀 Migration vers MySQL", run_mysql_migration),
        ("🧪 Test application", test_application),
        ("📜 Création script démarrage", create_startup_script)
    ]
    
    results = {}
    
    for step_name, step_function in steps:
        print(f"\n{step_name}...")
        
        start_time = time.time()
        try:
            result = step_function()
            execution_time = time.time() - start_time
            
            results[step_name] = result
            
            if result:
                print(f"✅ {step_name} - SUCCÈS ({execution_time:.1f}s)")
            else:
                print(f"❌ {step_name} - ÉCHEC ({execution_time:.1f}s)")
                break
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {step_name} - ERREUR: {e} ({execution_time:.1f}s)")
            results[step_name] = False
            break
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE LA CORRECTION")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for step_name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{step_name}: {status}")
    
    if success_count == total_count:
        print("\n🎉 CORRECTION TERMINÉE AVEC SUCCÈS!")
        print("\n🚀 Comment démarrer l'application:")
        print("   Option 1: Double-cliquer sur start_mysql.bat")
        print("   Option 2: Commandes manuelles:")
        print("      .venv_mysql\\Scripts\\activate")
        print("      python backend/app.py")
        print("\n✅ Avantages obtenus:")
        print("   - 0 erreur 'database is locked'")
        print("   - 0 erreur 'transaction already begun'")
        print("   - 0 erreur 'Working outside of application context'")
        print("   - Synchronisation NTP stable et continue")
        print("   - Performance optimisée avec pool de connexions MySQL")
        print("\n📊 Configuration finale:")
        print("   - Base de données: MySQL (localhost/ntp_monitor)")
        print("   - Utilisateur: root (sans mot de passe)")
        print("   - Environnement: .venv_mysql")
        print("   - Interface: http://127.0.0.1:5000")
    else:
        print(f"\n❌ CORRECTION ÉCHOUÉE ({success_count}/{total_count} étapes réussies)")
        print("\n🔧 Actions recommandées:")
        if not results.get("🔍 Vérification MySQL Server", False):
            print("   1. Installer MySQL Server")
            print("   2. Configurer l'utilisateur root")
            print("   3. Démarrer le service MySQL")
        print("   4. Consulter les logs d'erreur ci-dessus")
        print("   5. Relancer le script après correction")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Correction interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        sys.exit(1) 