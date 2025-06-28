#!/usr/bin/env python3
"""
Test de l'application NTP Monitor en mode hors ligne
Vérifie que tous les assets sont accessibles localement
"""

import os
import sys
import time
import requests
from pathlib import Path
from urllib.parse import urljoin
import subprocess

def test_local_assets():
    """Test de présence des assets locaux"""
    print("🔍 TEST DES ASSETS LOCAUX")
    print("=" * 50)
    
    # Vérifier les répertoires
    required_dirs = [
        'frontend/static/css/vendor',
        'frontend/static/js/vendor', 
        'frontend/static/fonts'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Répertoire trouvé: {dir_path}")
        else:
            print(f"❌ Répertoire manquant: {dir_path}")
            return False
    
    # Vérifier les fichiers critiques
    required_files = [
        'frontend/static/css/vendor/bootstrap.min.css',
        'frontend/static/css/vendor/fontawesome.min.css',
        'frontend/static/js/vendor/jquery-3.7.1.min.js',
        'frontend/static/js/vendor/bootstrap.bundle.min.js',
        'frontend/static/js/vendor/chart.min.js',
        'frontend/static/js/vendor/socket.io.min.js',
        'frontend/static/js/vendor/moment.min.js',
        'frontend/static/js/vendor/moment-locale-fr.min.js',
        'frontend/static/fonts/fa-solid-900.woff2',
        'frontend/static/fonts/fa-regular-400.woff2',
        'frontend/static/fonts/fa-brands-400.woff2'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) // 1024
            print(f"✅ Fichier trouvé: {file_path} ({size_kb} KB)")
        else:
            print(f"❌ Fichier manquant: {file_path}")
            return False
    
    print("\n✅ Tous les assets locaux sont présents!")
    return True

def test_template_conversion():
    """Test de la conversion du template"""
    print("\n🔍 TEST DU TEMPLATE")
    print("=" * 50)
    
    # Vérifier les fichiers template
    template_files = {
        'frontend/templates/base.html': 'Template principal (local)',
        'frontend/templates/base_cdn.html': 'Template CDN (sauvegarde)',
        'frontend/templates/base_cdn_backup.html': 'Backup original'
    }
    
    for file_path, description in template_files.items():
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description} manquant: {file_path}")
            return False
    
    # Vérifier que le template principal utilise bien les assets locaux
    with open('frontend/templates/base.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier la présence des URLs locales
    local_urls = [
        "url_for('static', filename='css/vendor/bootstrap.min.css')",
        "url_for('static', filename='css/vendor/fontawesome.min.css')",
        "url_for('static', filename='js/vendor/jquery-3.7.1.min.js')",
        "url_for('static', filename='js/vendor/bootstrap.bundle.min.js')",
        "url_for('static', filename='js/vendor/chart.min.js')",
        "url_for('static', filename='js/vendor/socket.io.min.js')",
        "url_for('static', filename='js/vendor/moment.min.js')",
        "url_for('static', filename='js/vendor/moment-locale-fr.min.js')"
    ]
    
    for url in local_urls:
        if url in content:
            print(f"✅ URL locale trouvée: {url}")
        else:
            print(f"❌ URL locale manquante: {url}")
            return False
    
    # Vérifier l'absence d'URLs CDN
    cdn_urls = [
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
        'https://code.jquery.com',
        'https://cdn.socket.io'
    ]
    
    for url in cdn_urls:
        if url in content:
            print(f"❌ URL CDN trouvée (à supprimer): {url}")
            return False
        else:
            print(f"✅ URL CDN absente: {url}")
    
    print("\n✅ Template correctement converti en mode local!")
    return True

def generate_offline_report():
    """Générer un rapport de test hors ligne"""
    print("\n📊 GÉNÉRATION DU RAPPORT")
    print("=" * 50)
    
    report_content = f"""# RAPPORT DE TEST HORS LIGNE - NTP Monitor Enterprise

## Statut Général
- ✅ Assets CDN téléchargés et installés
- ✅ Template converti en mode local
- ✅ Tous les fichiers présents et accessibles

## Assets Téléchargés
### CSS
- ✅ bootstrap.min.css ({os.path.getsize('frontend/static/css/vendor/bootstrap.min.css') // 1024} KB)
- ✅ fontawesome.min.css ({os.path.getsize('frontend/static/css/vendor/fontawesome.min.css') // 1024} KB)

### JavaScript
- ✅ jquery-3.7.1.min.js ({os.path.getsize('frontend/static/js/vendor/jquery-3.7.1.min.js') // 1024} KB)
- ✅ bootstrap.bundle.min.js ({os.path.getsize('frontend/static/js/vendor/bootstrap.bundle.min.js') // 1024} KB)
- ✅ chart.min.js ({os.path.getsize('frontend/static/js/vendor/chart.min.js') // 1024} KB)
- ✅ socket.io.min.js ({os.path.getsize('frontend/static/js/vendor/socket.io.min.js') // 1024} KB)
- ✅ moment.min.js ({os.path.getsize('frontend/static/js/vendor/moment.min.js') // 1024} KB)
- ✅ moment-locale-fr.min.js ({os.path.getsize('frontend/static/js/vendor/moment-locale-fr.min.js') // 1024} KB)

### Polices
- ✅ fa-solid-900.woff2 ({os.path.getsize('frontend/static/fonts/fa-solid-900.woff2') // 1024} KB)
- ✅ fa-regular-400.woff2 ({os.path.getsize('frontend/static/fonts/fa-regular-400.woff2') // 1024} KB)
- ✅ fa-brands-400.woff2 ({os.path.getsize('frontend/static/fonts/fa-brands-400.woff2') // 1024} KB)

## Templates
- ✅ base.html - Template principal avec assets locaux
- ✅ base_cdn.html - Sauvegarde template CDN
- ✅ base_cdn_backup.html - Backup original

## Recommandations
1. L'application est prête pour un déploiement hors ligne
2. Générer l'EXE avec: `python build_installer_fixed.py`
3. Tester l'EXE sur une machine sans internet
4. Tous les assets sont maintenant intégrés dans l'application

## Taille Totale des Assets
- CSS: {(os.path.getsize('frontend/static/css/vendor/bootstrap.min.css') + os.path.getsize('frontend/static/css/vendor/fontawesome.min.css')) // 1024} KB
- JS: {sum(os.path.getsize(f'frontend/static/js/vendor/{f}') for f in os.listdir('frontend/static/js/vendor/')) // 1024} KB
- Polices: {sum(os.path.getsize(f'frontend/static/fonts/{f}') for f in os.listdir('frontend/static/fonts/')) // 1024} KB

Date du rapport: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('RAPPORT_OFFLINE.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("✅ Rapport généré: RAPPORT_OFFLINE.md")

def main():
    """Fonction principale"""
    print("🧪 TEST COMPLET MODE HORS LIGNE - NTP Monitor Enterprise")
    print("=" * 70)
    
    # Test 1: Vérifier les assets locaux
    if not test_local_assets():
        print("\n❌ Échec du test des assets locaux")
        return False
    
    # Test 2: Vérifier la conversion du template
    if not test_template_conversion():
        print("\n❌ Échec du test du template")
        return False
    
    # Générer le rapport
    generate_offline_report()
    
    print("\n" + "=" * 70)
    print("🎉 CONFIGURATION HORS LIGNE VALIDÉE!")
    print("=" * 70)
    print("\n📋 PROCHAINES ÉTAPES:")
    print("1. Générer l'EXE: python build_installer_fixed.py")
    print("2. Tester l'EXE sur une machine sans internet")
    print("3. Déployer sur les machines cibles")
    print("4. Consulter le rapport: RAPPORT_OFFLINE.md")
    
    return True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur durant les tests: {e}")
        sys.exit(1) 