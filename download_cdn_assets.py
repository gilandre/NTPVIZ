#!/usr/bin/env python3
"""
Script de téléchargement des assets CDN pour NTP Monitor Enterprise
Télécharge tous les fichiers externes pour un déploiement hors ligne
"""

import os
import requests
import urllib.parse
from pathlib import Path

# Configuration des assets CDN à télécharger
CDN_ASSETS = {
    # jQuery
    'jquery-3.7.1.min.js': 'https://code.jquery.com/jquery-3.7.1.min.js',
    
    # Bootstrap 5.3.0
    'bootstrap.bundle.min.js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'bootstrap.min.css': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    
    # Chart.js
    'chart.min.js': 'https://cdn.jsdelivr.net/npm/chart.js',
    
    # Socket.IO 4.7.2
    'socket.io.min.js': 'https://cdn.socket.io/4.7.2/socket.io.min.js',
    
    # Moment.js
    'moment.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js',
    'moment-locale-fr.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/locale/fr.min.js',
    
    # Font Awesome 6.4.0
    'fontawesome.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
}

# Répertoires de destination
STATIC_DIR = Path('frontend/static')
CSS_DIR = STATIC_DIR / 'css' / 'vendor'
JS_DIR = STATIC_DIR / 'js' / 'vendor'
FONTS_DIR = STATIC_DIR / 'fonts'

def create_directories():
    """Créer les répertoires nécessaires"""
    directories = [CSS_DIR, JS_DIR, FONTS_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Répertoire créé: {directory}")

def download_file(url, filename, target_dir):
    """Télécharger un fichier depuis une URL"""
    try:
        print(f"📥 Téléchargement: {filename}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        target_path = target_dir / filename
        with open(target_path, 'wb') as f:
            f.write(response.content)
        
        size_kb = len(response.content) // 1024
        print(f"✅ Téléchargé: {filename} ({size_kb} KB)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur téléchargement {filename}: {e}")
        return False

def download_font_awesome_fonts():
    """Télécharger les polices Font Awesome"""
    print("📥 Téléchargement des polices Font Awesome...")
    
    # URLs des fichiers de polices FA 6.4.0
    font_urls = {
        'fa-solid-900.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2',
        'fa-regular-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2',
        'fa-brands-400.woff2': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2'
    }
    
    for filename, url in font_urls.items():
        download_file(url, filename, FONTS_DIR)

def fix_fontawesome_css():
    """Corriger les chemins des polices dans le CSS Font Awesome"""
    css_file = CSS_DIR / 'fontawesome.min.css'
    
    if not css_file.exists():
        print("❌ Fichier Font Awesome CSS non trouvé")
        return
    
    print("🔧 Correction des chemins Font Awesome...")
    
    # Lire le fichier CSS
    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les URLs CDN par des chemins locaux
    replacements = {
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/': '../fonts/',
        '../webfonts/': '../fonts/'
    }
    
    for old_path, new_path in replacements.items():
        content = content.replace(old_path, new_path)
    
    # Écrire le fichier corrigé
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Chemins Font Awesome corrigés")

def download_all_assets():
    """Télécharger tous les assets"""
    print("🚀 TÉLÉCHARGEMENT DES ASSETS CDN")
    print("=" * 50)
    
    create_directories()
    
    success_count = 0
    total_count = len(CDN_ASSETS)
    
    for filename, url in CDN_ASSETS.items():
        # Déterminer le répertoire de destination
        if filename.endswith('.css'):
            target_dir = CSS_DIR
        elif filename.endswith('.js'):
            target_dir = JS_DIR
        else:
            target_dir = STATIC_DIR
        
        if download_file(url, filename, target_dir):
            success_count += 1
    
    # Télécharger les polices Font Awesome
    download_font_awesome_fonts()
    
    # Corriger le CSS Font Awesome
    fix_fontawesome_css()
    
    print(f"\n✅ Téléchargement terminé: {success_count}/{total_count} fichiers")
    
    return success_count == total_count

def create_local_template():
    """Créer un template base local sans CDN"""
    print("📝 Création du template base local...")
    
    # Lire le template actuel
    base_template = Path('frontend/templates/base.html')
    
    if not base_template.exists():
        print("❌ Template base.html non trouvé")
        return False
    
    with open(base_template, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacements CDN → Local
    cdn_replacements = {
        # Bootstrap CSS
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css': 
            "{{ url_for('static', filename='css/vendor/bootstrap.min.css') }}",
        
        # Font Awesome
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css':
            "{{ url_for('static', filename='css/vendor/fontawesome.min.css') }}",
        
        # jQuery
        'https://code.jquery.com/jquery-3.7.1.min.js':
            "{{ url_for('static', filename='js/vendor/jquery-3.7.1.min.js') }}",
        
        # Bootstrap JS
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js':
            "{{ url_for('static', filename='js/vendor/bootstrap.bundle.min.js') }}",
        
        # Chart.js
        'https://cdn.jsdelivr.net/npm/chart.js':
            "{{ url_for('static', filename='js/vendor/chart.min.js') }}",
        
        # Socket.IO
        'https://cdn.socket.io/4.7.2/socket.io.min.js':
            "{{ url_for('static', filename='js/vendor/socket.io.min.js') }}",
        
        # Moment.js
        'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js':
            "{{ url_for('static', filename='js/vendor/moment.min.js') }}",
        
        'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/locale/fr.min.js':
            "{{ url_for('static', filename='js/vendor/moment-locale-fr.min.js') }}"
    }
    
    # Appliquer les remplacements
    for cdn_url, local_url in cdn_replacements.items():
        content = content.replace(cdn_url, local_url)
    
    # Sauvegarder la version locale
    local_template = Path('frontend/templates/base_local.html')
    with open(local_template, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Template local créé: {local_template}")
    
    # Créer aussi une sauvegarde de l'original
    backup_template = Path('frontend/templates/base_cdn_backup.html')
    if not backup_template.exists():
        with open(base_template, 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open(backup_template, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ Sauvegarde CDN: {backup_template}")
    
    return True

def update_build_script():
    """Mettre à jour le script de build pour inclure les assets locaux"""
    print("🔧 Mise à jour du script de build...")
    
    build_script = Path('build_installer_fixed.py')
    
    if not build_script.exists():
        print("❌ Script de build non trouvé")
        return False
    
    # Lire le script
    with open(build_script, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter la copie des assets vendor dans copy_application_files
    vendor_copy_code = '''    
    # Copier les assets vendor (CDN locaux)
    vendor_dirs = ['frontend/static/css/vendor', 'frontend/static/js/vendor', 'frontend/static/fonts']
    for vendor_dir in vendor_dirs:
        if os.path.exists(vendor_dir):
            vendor_target = target_dir / vendor_dir.replace('frontend/', '')
            if vendor_target.exists():
                shutil.rmtree(vendor_target)
            shutil.copytree(vendor_dir, vendor_target)
            print(f"✅ {vendor_dir} → {vendor_target}")'''
    
    # Ajouter après la copie du frontend
    content = content.replace(
        'shutil.copytree(source, target)\n            print(f"✅ {source} → {target}")',
        'shutil.copytree(source, target)\n            print(f"✅ {source} → {target}")' + vendor_copy_code
    )
    
    # Sauvegarder
    with open(build_script, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Script de build mis à jour")
    return True

def main():
    """Fonction principale"""
    print("📦 TÉLÉCHARGEMENT ASSETS CDN POUR DÉPLOIEMENT HORS LIGNE")
    print("=" * 60)
    
    # Télécharger tous les assets
    if download_all_assets():
        print("\n✅ Tous les assets téléchargés avec succès!")
        
        # Créer le template local
        if create_local_template():
            print("✅ Template local créé")
        
        # Mettre à jour le build
        if update_build_script():
            print("✅ Script de build mis à jour")
        
        print("\n" + "=" * 60)
        print("🎉 CONFIGURATION HORS LIGNE TERMINÉE!")
        print("=" * 60)
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. Renommez 'base.html' en 'base_cdn.html'")
        print("2. Renommez 'base_local.html' en 'base.html'")
        print("3. Testez l'application en mode hors ligne")
        print("4. Générez l'EXE avec 'python build_installer_fixed.py'")
        print("\n📂 ASSETS TÉLÉCHARGÉS:")
        print("├── frontend/static/css/vendor/")
        print("├── frontend/static/js/vendor/")
        print("└── frontend/static/fonts/")
        
    else:
        print("\n❌ Échec du téléchargement de certains assets")
        return False
    
    return True

if __name__ == '__main__':
    main() 