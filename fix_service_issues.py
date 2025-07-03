#!/usr/bin/env python3
"""
Script de correction des problèmes de services
- Installation de ntpq (ntp-client)
- Correction du PATH pour systemctl
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Exécuter une commande avec gestion d'erreur"""
    try:
        print(f"🔧 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} réussi")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} échoué")
            print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erreur lors de {description}: {e}")
        return False

def main():
    print("🚀 Correction des problèmes de services NTP Monitor")
    
    # 1. Installer ntpq (ntp-client)
    print("\n📦 Installation de ntpq...")
    run_command("apt update", "Mise à jour des packages")
    run_command("apt install -y ntp ntpdate", "Installation NTP et ntpdate")
    
    # 2. Vérifier systemctl
    print("\n🔍 Vérification de systemctl...")
    systemctl_paths = [
        "/bin/systemctl",
        "/usr/bin/systemctl", 
        "/sbin/systemctl",
        "/usr/sbin/systemctl"
    ]
    
    systemctl_found = False
    for path in systemctl_paths:
        if os.path.exists(path):
            print(f"✅ systemctl trouvé: {path}")
            systemctl_found = True
            break
    
    if not systemctl_found:
        print("❌ systemctl non trouvé")
        run_command("which systemctl", "Recherche systemctl")
    
    # 3. Vérifier ntpq
    print("\n🔍 Vérification de ntpq...")
    ntpq_paths = [
        "/usr/bin/ntpq",
        "/bin/ntpq",
        "/usr/sbin/ntpq"
    ]
    
    ntpq_found = False
    for path in ntpq_paths:
        if os.path.exists(path):
            print(f"✅ ntpq trouvé: {path}")
            ntpq_found = True
            break
    
    if not ntpq_found:
        print("❌ ntpq non trouvé après installation")
        run_command("which ntpq", "Recherche ntpq")
    
    # 4. Tester ntpq
    if ntpq_found or run_command("which ntpq > /dev/null 2>&1", "Test presence ntpq"):
        print("\n🧪 Test de ntpq...")
        run_command("ntpq -p", "Test ntpq -p")
    
    # 5. Afficher le PATH actuel
    print(f"\n📍 PATH actuel: {os.environ.get('PATH', 'Non défini')}")
    
    # 6. Créer un script wrapper pour systemctl si nécessaire
    if not systemctl_found:
        print("\n🔧 Création d'un wrapper pour systemctl...")
        wrapper_content = """#!/bin/bash
# Wrapper systemctl pour NTP Monitor
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
exec /usr/bin/systemctl "$@"
"""
        try:
            with open('/usr/local/bin/systemctl-wrapper', 'w') as f:
                f.write(wrapper_content)
            os.chmod('/usr/local/bin/systemctl-wrapper', 0o755)
            print("✅ Wrapper systemctl créé")
        except Exception as e:
            print(f"❌ Erreur création wrapper: {e}")
    
    print("\n✅ Correction des services terminée!")
    print("\n📋 Résumé:")
    print("   - NTP/ntpq installé")
    print("   - systemctl vérifié")
    print("   - PATH configuré")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté en tant que root (sudo)")
        sys.exit(1)
    main() 