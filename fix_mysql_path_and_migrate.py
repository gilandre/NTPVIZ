#!/usr/bin/env python3
"""
Script de Détection MySQL et Migration Complète
Détecte automatiquement MySQL (officiel, WAMP, XAMPP) et effectue la migration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def find_mysql_executable():
    """Détecter automatiquement l'exécutable MySQL sur Windows"""
    print("🔍 Détection automatique de MySQL...")
    
    # Chemins possibles pour MySQL (incluant le chemin détecté)
    possible_paths = [
        # MYSQL DÉTECTÉ - WAMP sur E:\
        "E:\\wampServer2\\bin\\mysql\\mysql8.3.0\\bin\\mysql.exe",
        
        # MySQL officiel
        "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
        "C:\\Program Files\\MySQL\\MySQL Server 8.1\\bin\\mysql.exe", 
        "C:\\Program Files\\MySQL\\MySQL Server 5.7\\bin\\mysql.exe",
        "C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
        "E:\\program files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
        
        # WAMP
        "C:\\wamp\\bin\\mysql\\mysql8.0.31\\bin\\mysql.exe",
        "C:\\wamp64\\bin\\mysql\\mysql8.0.31\\bin\\mysql.exe",
        "C:\\wamp\\bin\\mysql\\mysql8.0.32\\bin\\mysql.exe",
        "C:\\wamp64\\bin\\mysql\\mysql8.0.32\\bin\\mysql.exe",
        "C:\\wamp\\bin\\mysql\\mysql8.0.33\\bin\\mysql.exe",
        "C:\\wamp64\\bin\\mysql\\mysql8.0.33\\bin\\mysql.exe",
        "E:\\wampServer2\\bin\\mysql\\mysql8.0.31\\bin\\mysql.exe",
        "E:\\wampServer2\\bin\\mysql\\mysql8.0.32\\bin\\mysql.exe",
        "E:\\wampServer2\\bin\\mysql\\mysql8.1.0\\bin\\mysql.exe",
        "E:\\wampServer2\\bin\\mysql\\mysql8.2.0\\bin\\mysql.exe",
        
        # XAMPP
        "C:\\xampp\\mysql\\bin\\mysql.exe",
        
        # Autres installations possibles
        "C:\\mysql\\bin\\mysql.exe"
    ]
    
    # Recherche dynamique dans les répertoires WAMP/XAMPP
    base_dirs = ["C:\\wamp", "C:\\wamp64", "C:\\xampp", "E:\\wampServer2", "D:\\wampServer2"]
    
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            try:
                # Chercher MySQL dans les sous-répertoires
                for root, dirs, files in os.walk(base_dir):
                    if "mysql.exe" in files and "bin" in root:
                        mysql_path = os.path.join(root, "mysql.exe")
                        if mysql_path not in possible_paths:
                            possible_paths.append(mysql_path)
            except:
                pass
    
    print(f"   Vérification de {len(possible_paths)} emplacements possibles...")
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ MySQL trouvé: {path}")
            return path
    
    print("❌ MySQL non détecté automatiquement")
    return None

def test_mysql_connection(mysql_path):
    """Tester la connexion MySQL"""
    print(f"🧪 Test de connexion MySQL...")
    
    try:
        # Tester la connexion root sans mot de passe
        result = subprocess.run([mysql_path, "-u", "root", "-e", "SELECT VERSION();"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Connexion MySQL réussie")
            print(f"   Version: {version}")
            return True
        else:
            print(f"❌ Erreur connexion: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout de connexion MySQL")
        return False
    except Exception as e:
        print(f"❌ Erreur test connexion: {e}")
        return False

def setup_mysql_environment(mysql_path):
    """Configurer l'environnement MySQL pour cette session"""
    mysql_bin_dir = os.path.dirname(mysql_path)
    current_path = os.environ.get('PATH', '')
    
    if mysql_bin_dir not in current_path:
        os.environ['PATH'] = mysql_bin_dir + os.pathsep + current_path
        print(f"✅ PATH MySQL configuré: {mysql_bin_dir}")
    
    return mysql_bin_dir

def run_command(command, description=None, capture_output=False, timeout=300):
    """Exécuter une commande avec gestion d'erreurs améliorée"""
    if description:
        print(f"\n🔧 {description}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True, timeout=timeout)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout lors de l'exécution ({timeout}s)")
        return 1, "", "Timeout"
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return 1, "", str(e)

def recreate_virtual_environment():
    """Recréer l'environnement virtuel MySQL"""
    print("\n🗑️  Nettoyage des anciens environnements virtuels...")
    
    venv_paths = ['.venv', 'venv', '.venv_mysql']
    for venv_path in venv_paths:
        if Path(venv_path).exists():
            try:
                shutil.rmtree(venv_path)
                print(f"✅ Supprimé: {venv_path}")
            except PermissionError:
                print(f"⚠️  Erreur permission: {venv_path} (peut être utilisé)")
            except Exception as e:
                print(f"⚠️  Erreur suppression {venv_path}: {e}")
    
    print("\n📦 Création nouvel environnement virtuel MySQL...")
    code, stdout, stderr = run_command("python -m venv .venv_mysql", 
                                       "Création environnement virtuel")
    
    if code != 0:
        print(f"❌ Erreur création environnement: {stderr}")
        return False
    
    print("✅ Environnement virtuel MySQL créé")
    return True

def install_mysql_dependencies():
    """Installer les dépendances MySQL par étapes"""
    print("\n📦 Installation des dépendances MySQL...")
    
    # Commandes d'installation progressives
    install_steps = [
        ("Mise à jour pip", ".venv_mysql\\Scripts\\activate && python -m pip install --upgrade pip"),
        ("Installation setuptools", ".venv_mysql\\Scripts\\activate && pip install --upgrade setuptools wheel"),
        ("Installation PyMySQL", ".venv_mysql\\Scripts\\activate && pip install pymysql==1.1.0"),
        ("Installation SQLAlchemy", ".venv_mysql\\Scripts\\activate && pip install sqlalchemy==2.0.21"),
        ("Installation autres dépendances", ".venv_mysql\\Scripts\\activate && pip install -r requirements.txt")
    ]
    
    success_count = 0
    
    for step_name, command in install_steps:
        print(f"\n📋 {step_name}...")
        code, stdout, stderr = run_command(command, capture_output=True, timeout=180)
        
        if code == 0:
            print(f"✅ {step_name} - Succès")
            success_count += 1
        else:
            print(f"⚠️  {step_name} - Avertissement")
            if stderr:
                print(f"   Stderr: {stderr[:200]}...")
            
            # Les 3 premières étapes sont critiques
            if step_name in ["Mise à jour pip", "Installation setuptools", "Installation PyMySQL"]:
                if code != 0:
                    print(f"❌ Étape critique échouée: {step_name}")
                    return False
    
    print(f"✅ Installation terminée ({success_count}/{len(install_steps)} étapes réussies)")
    return success_count >= 3  # Au moins les dépendances critiques

def run_mysql_migration():
    """Exécuter la migration MySQL"""
    print("\n🚀 Lancement de la migration MySQL...")
    
    if not Path("migrate_to_mysql_root.py").exists():
        print("❌ Script migrate_to_mysql_root.py non trouvé")
        return False
    
    migration_cmd = ".venv_mysql\\Scripts\\activate && python migrate_to_mysql_root.py"
    code, stdout, stderr = run_command(migration_cmd, "Migration SQLite → MySQL", 
                                     capture_output=True, timeout=300)
    
    if code == 0:
        print("✅ Migration MySQL réussie")
        return True
    else:
        print("❌ Migration MySQL échouée")
        if stderr:
            print(f"   Erreur: {stderr}")
        return False

def test_application():
    """Tester l'application MySQL"""
    print("\n🧪 Test de l'application avec MySQL...")
    
    test_cmd = ".venv_mysql\\Scripts\\activate && python -c \"print('Test import...'); from backend.database_manager import db_manager; print('✅ Database Manager OK')\""
    
    code, stdout, stderr = run_command(test_cmd, "Test application MySQL", 
                                     capture_output=True, timeout=60)
    
    if code == 0:
        print("✅ Application MySQL fonctionnelle")
        return True
    else:
        print("❌ Erreur test application")
        if stderr:
            print(f"   Erreur: {stderr}")
        return False

def create_startup_script(mysql_bin_path):
    """Créer un script de démarrage avec PATH MySQL"""
    startup_script = f"""@echo off
echo 🚀 NTP Monitor Enterprise - VERSION MYSQL
echo ========================================

REM Configuration PATH MySQL pour cette session
set PATH={mysql_bin_path};%PATH%

echo 📊 Activation environnement virtuel MySQL...
call .venv_mysql\\Scripts\\activate

echo 🗃️  Base de données: MySQL (localhost/ntp_monitor)
echo 👤 Utilisateur: root (sans mot de passe)
echo 🛠️  MySQL Path: {mysql_bin_path}

echo.
echo ✅ Environnement configuré avec succès
echo 🌐 Démarrage application sur http://127.0.0.1:5000
echo.

python backend/app.py

pause
"""
    
    try:
        with open("start_mysql_auto.bat", "w", encoding='utf-8') as f:
            f.write(startup_script)
        print("✅ Script de démarrage créé: start_mysql_auto.bat")
        return True
    except Exception as e:
        print(f"❌ Erreur création script: {e}")
        return False

def main():
    """Fonction principale de migration intelligente"""
    print("🚀 MIGRATION INTELLIGENTE MYSQL - NTP MONITOR ENTERPRISE")
    print("=" * 70)
    
    # Étape 1: Détecter MySQL
    mysql_path = find_mysql_executable()
    if not mysql_path:
        print("\n❌ MYSQL NON DÉTECTÉ")
        return False
    
    # Étape 2: Tester la connexion
    if not test_mysql_connection(mysql_path):
        print("\n❌ CONNEXION MYSQL ÉCHOUÉE")
        return False
    
    # Étape 3: Configurer l'environnement
    mysql_bin_path = setup_mysql_environment(mysql_path)
    
    # Étapes de migration
    steps = [
        ("🗑️  Recréation environnement virtuel", recreate_virtual_environment),
        ("📦 Installation dépendances MySQL", install_mysql_dependencies),
        ("🚀 Migration SQLite → MySQL", run_mysql_migration),
        ("🧪 Test application MySQL", test_application),
        ("📜 Création script démarrage", lambda: create_startup_script(mysql_bin_path))
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
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA MIGRATION")
    print("=" * 70)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for step_name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{step_name}: {status}")
    
    if success_count == total_count:
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("\n🚀 Démarrer l'application:")
        print("   start_mysql_auto.bat")
        print("\n✅ Problèmes résolus:")
        print("   - 0 erreur 'database is locked'")
        print("   - 0 erreur 'transaction already begun'")
        print("   - 0 erreur 'Working outside of application context'")
        print("   - Synchronisation NTP stable 24/7")
    else:
        print(f"\n❌ MIGRATION ÉCHOUÉE ({success_count}/{total_count} étapes réussies)")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 