#!/usr/bin/env python3
"""
Script de vérification des scripts de déploiement
Valide la cohérence et la complétude des scripts
"""
import os
import sys
import subprocess
from pathlib import Path

def check_script_exists(script_path):
    """Vérifier qu'un script existe et est exécutable"""
    if os.path.exists(script_path):
        if os.access(script_path, os.X_OK):
            return True, "✅ Existe et exécutable"
        else:
            return False, "⚠️ Existe mais pas exécutable"
    else:
        return False, "❌ N'existe pas"

def check_python_script(script_path):
    """Vérifier un script Python"""
    if not os.path.exists(script_path):
        return False, "❌ Script Python non trouvé"
    
    try:
        # Vérifier la syntaxe Python
        result = subprocess.run([sys.executable, "-m", "py_compile", script_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True, "✅ Syntaxe Python valide"
        else:
            return False, f"❌ Erreur de syntaxe: {result.stderr}"
    except Exception as e:
        return False, f"❌ Erreur de vérification: {e}"

def check_bash_script(script_path):
    """Vérifier un script Bash"""
    if not os.path.exists(script_path):
        return False, "❌ Script Bash non trouvé"
    
    try:
        # Vérifier la syntaxe Bash
        result = subprocess.run(["bash", "-n", script_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True, "✅ Syntaxe Bash valide"
        else:
            return False, f"❌ Erreur de syntaxe: {result.stderr}"
    except Exception as e:
        return False, f"❌ Erreur de vérification: {e}"

def check_required_files():
    """Vérifier les fichiers requis pour le déploiement"""
    required_files = [
        "app.py",
        "requirements.txt",
        "env.example",
        "initialiser_database.py",
        "fix_database_schema.py",
        "harmonize_models.py",
        "backend/app.py",
        "backend/database_manager.py",
        "backend/models/__init__.py",
        "backend/models/user.py",
        "backend/models/ntp_server.py",
        "deployment/scripts/deploy_ubuntu_complete.sh",
        "deployment/scripts/update_deployment.sh",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    print("🔍 Vérification des fichiers requis:")
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MANQUANT")
            all_exist = False
    
    return all_exist

def check_deployment_scripts():
    """Vérifier les scripts de déploiement"""
    print("\n🔍 Vérification des scripts de déploiement:")
    
    scripts_to_check = [
        ("deployment/scripts/deploy_ubuntu_complete.sh", "bash"),
        ("deployment/scripts/update_deployment.sh", "bash"),
        ("fix_database_schema.py", "python"),
        ("harmonize_models.py", "python"),
        ("initialiser_database.py", "python")
    ]
    
    all_valid = True
    
    for script_path, script_type in scripts_to_check:
        if script_type == "bash":
            valid, message = check_bash_script(script_path)
        else:
            valid, message = check_python_script(script_path)
        
        print(f"  {message} - {script_path}")
        if not valid:
            all_valid = False
    
    return all_valid

def check_environment_configuration():
    """Vérifier la configuration de l'environnement"""
    print("\n🔍 Vérification de la configuration:")
    
    # Vérifier env.example
    if os.path.exists("env.example"):
        with open("env.example", "r") as f:
            content = f.read()
            required_vars = ["FLASK_ENV", "DEBUG", "HOST", "MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
            missing_vars = [var for var in required_vars if var not in content]
            
            if missing_vars:
                print(f"  ⚠️ Variables manquantes dans env.example: {missing_vars}")
            else:
                print("  ✅ env.example contient toutes les variables requises")
    else:
        print("  ❌ env.example manquant")
        return False
    
    return True

def check_database_models():
    """Vérifier la cohérence des modèles de base de données"""
    print("\n🔍 Vérification des modèles de base de données:")
    
    try:
        # Test d'import des modèles
        sys.path.insert(0, str(Path(__file__).parent))
        
        from backend.models.user import User
        from backend.models.ntp_server import NTPServer
        from backend.models.alert import Alert
        from backend.models.system_config import SystemConfig
        
        print("  ✅ Tous les modèles importables")
        
        # Vérifier les colonnes requises dans NTPServer
        required_columns = [
            'id', 'name', 'address', 'port', 'server_type', 'is_active', 'priority',
            'timeout', 'status', 'last_sync',
            'last_offset', 'last_latency', 'last_delay', 'last_stratum',
            'last_internet_status', 'last_error', 'error_count', 'consecutive_errors',
            'description', 'created_at', 'updated_at', 'created_by', 'deleted_at', 'deleted_by'
        ]
        
        ntp_attrs = [attr for attr in dir(NTPServer) if not attr.startswith('_')]
        missing_attrs = [col for col in required_columns if col not in ntp_attrs]
        
        if missing_attrs:
            print(f"  ⚠️ Attributs manquants dans NTPServer: {missing_attrs}")
        else:
            print("  ✅ NTPServer a tous les attributs requis")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Erreur d'import des modèles: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur lors de la vérification des modèles: {e}")
        return False

def check_deployment_guide():
    """Vérifier le guide de déploiement"""
    print("\n🔍 Vérification du guide de déploiement:")
    
    if os.path.exists("DEPLOYMENT_GUIDE.md"):
        with open("DEPLOYMENT_GUIDE.md", "r") as f:
            content = f.read()
            
            required_sections = [
                "Déploiement automatique",
                "Mise à jour automatique",
                "Commandes de gestion",
                "Dépannage",
                "Rollback"
            ]
            
            missing_sections = [section for section in required_sections if section not in content]
            
            if missing_sections:
                print(f"  ⚠️ Sections manquantes: {missing_sections}")
            else:
                print("  ✅ Guide de déploiement complet")
            
            return len(missing_sections) == 0
    else:
        print("  ❌ DEPLOYMENT_GUIDE.md manquant")
        return False

def main():
    """Fonction principale de vérification"""
    print("🚀 VÉRIFICATION COMPLÈTE DES SCRIPTS DE DÉPLOIEMENT")
    print("=" * 60)
    
    checks = [
        ("Fichiers requis", check_required_files),
        ("Scripts de déploiement", check_deployment_scripts),
        ("Configuration environnement", check_environment_configuration),
        ("Modèles de base de données", check_database_models),
        ("Guide de déploiement", check_deployment_guide)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name.upper()}:")
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  ❌ Erreur lors de la vérification: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TOUTES LES VÉRIFICATIONS ONT RÉUSSI!")
        print("✅ Le déploiement est prêt pour la production")
    else:
        print("⚠️ CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ")
        print("❌ Veuillez corriger les problèmes avant le déploiement")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 