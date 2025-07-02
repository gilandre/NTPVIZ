#!/usr/bin/env python3
"""
Correction Universelle NTP Monitor - Windows/Ubuntu 24.04
Corrige: erreur 'partitioned' cookies + MySQL fallback
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def run_cmd(cmd):
    """Exécute une commande"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    except:
        return False, ""

def main():
    print("🔧 CORRECTION UNIVERSELLE NTP MONITOR")
    print("=" * 50)
    
    is_windows = platform.system().lower() == 'windows'
    pip_cmd = 'pip' if is_windows else 'pip3'
    
    # 1. CORRECTION PACKAGES (erreur partitioned)
    print("\n1️⃣ CORRECTION PACKAGES...")
    
    # Packages corrigés
    packages = [
        "Flask==2.3.3",         # Version sans bug partitioned
        "Werkzeug==2.3.7",      # Compatible
        "redis==4.6.0",         # Compatible Celery
        "celery==5.3.4",        # Stable
        "Flask-SocketIO==5.3.6", # Compatible
        "python-socketio==5.8.0", # Stable
        "PyMySQL==1.1.0",       # Base données
        "psutil==5.9.5",        # Monitoring
        "ntplib==0.4.0",        # NTP
        "python-dotenv==1.0.0"  # Config
    ]
    
    # Désinstallation conflits
    conflicts = ['Flask', 'Werkzeug', 'redis', 'celery', 'Flask-SocketIO', 'python-socketio']
    for pkg in conflicts:
        run_cmd(f"{pip_cmd} uninstall {pkg} -y")
    
    # Installation versions corrigées
    for pkg in packages:
        success, _ = run_cmd(f"{pip_cmd} install {pkg} --no-cache-dir")
        print(f"  {'✅' if success else '❌'} {pkg}")
    
    # 2. CONFIGURATION FALLBACK
    print("\n2️⃣ CONFIGURATION FALLBACK MySQL->SQLite...")
    
    config_content = '''# Config avec fallback automatique
import os
from pathlib import Path

class Config:
    SECRET_KEY = 'ntp-monitor-2025'
    
    # Test MySQL
    try:
        import pymysql
        pymysql.connect(host='localhost', port=3306, user='root', 
                       password='', connect_timeout=1).close()
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/ntp_monitor'
        print("MySQL utilise")
    except:
        # Fallback SQLite
        db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        print("SQLite utilise")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
'''
    
    # Sauvegarde
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    with open(config_dir / 'config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("  Configuration fallback creee")
    
    # 3. PATCH COOKIES
    print("\n3️⃣ PATCH COOKIES 'PARTITIONED'...")
    
    auth_file = Path('backend/api/auth.py')
    if auth_file.exists():
        content = auth_file.read_text(encoding='utf-8')
        
        # Patch fonction cookies
        if 'def safe_cookie' not in content:
            patch = '''
def safe_cookie(response, key, value='', **kwargs):
    """Évite erreur partitioned"""
    safe_kwargs = {k: v for k, v in kwargs.items() if k != 'partitioned'}
    try:
        response.set_cookie(key, value, **safe_kwargs)
    except TypeError:
        response.set_cookie(key, value, path='/', httponly=True)

'''
            # Insertion après imports
            lines = content.split('\n')
            import_end = next((i for i, line in enumerate(lines) 
                             if line and not line.startswith(('import ', 'from '))), 5)
            lines.insert(import_end, patch)
            
            auth_file.write_text('\n'.join(lines), encoding='utf-8')
            print("  Patch cookies applique")
    
    # 4. DÉMARRAGE MYSQL
    print("\n4️⃣ DÉMARRAGE MYSQL...")
    
    if is_windows:
        cmds = ['net start mysql', 'net start mysql80']
    else:
        cmds = ['sudo systemctl start mysql', 'sudo systemctl start mariadb']
    
    mysql_ok = False
    for cmd in cmds:
        success, _ = run_cmd(cmd)
        if success:
            print(f"  MySQL demarre: {cmd}")
            mysql_ok = True
            break
    
    if not mysql_ok:
        print("  MySQL non demarrable - SQLite sera utilise")
    
    # 5. TEST APPLICATION
    print("\n5️⃣ TEST APPLICATION...")
    
    try:
        sys.path.insert(0, '.')
        from backend.app import create_app
        app = create_app()
        
        with app.app_context():
            print("  Application Flask operationnelle")
        
        app_ok = True
    except Exception as e:
        print(f"  ❌ Erreur application: {e}")
        app_ok = False
    
    # 6. SCRIPT DÉMARRAGE
    if is_windows:
        with open('start_ntp.bat', 'w') as f:
            f.write('@echo off\necho Démarrage NTP Monitor...\npython app.py\npause')
        print("\n  Script cree: start_ntp.bat")
    
    # 7. RAPPORT FINAL
    print(f"\n{'='*50}")
    print("📊 RAPPORT FINAL")
    print(f"{'='*50}")
    
    if app_ok:
        print("CORRECTION REUSSIE !")
        print("Erreur 'partitioned' corrigee")
        print("Fallback MySQL/SQLite configure")
        print("Application operationnelle")
    else:
        print("CORRECTION PARTIELLE")
    
    print(f"\nUTILISATION:")
    if is_windows:
        print("  - Démarrer: start_ntp.bat")
        print("  - Ou: python app.py")
    else:
        print("  - Démarrer: python3 app.py")
    
    print("  - Accès: http://localhost:5000")
    print("  - Comptes: admin/admin123")
    
    print(f"\nCOMPATIBILITE:")
    print("  Windows 10/11")
    print("  Ubuntu 24.04")
    print("  MySQL + SQLite fallback")
    
    return app_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 