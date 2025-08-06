#!/usr/bin/env python3
"""
Script de validation des corrections du module d'administration
"""

import os
import re
import sys
from pathlib import Path

def check_file_exists(filepath):
    """Vérifier qu'un fichier existe"""
    return Path(filepath).exists()

def check_file_contains(filepath, pattern, description):
    """Vérifier qu'un fichier contient un pattern"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                return True, f"✅ {description}"
            else:
                return False, f"❌ {description} - Pattern non trouvé"
    except Exception as e:
        return False, f"❌ {description} - Erreur: {e}"

def validate_corrections():
    """Valider toutes les corrections"""
    
    print("🔍 Validation des corrections du module d'administration")
    print("=" * 60)
    
    checks = []
    
    # 1. Vérifier que les fichiers existent
    print("\n📁 Vérification de l'existence des fichiers:")
    
    files_to_check = [
        "frontend/templates/base.html",
        "frontend/static/js/modules/admin-manager-updated.js",
        "frontend/templates/modals/admin-updated.html",
        "backend/app.py"
    ]
    
    for filepath in files_to_check:
        exists = check_file_exists(filepath)
        status = "✅" if exists else "❌"
        print(f"  {status} {filepath}")
        checks.append(exists)
    
    # 2. Vérifier les corrections dans base.html
    print("\n🔧 Vérification des corrections dans base.html:")
    
    base_checks = [
        (
            r'admin-manager-updated\.js',
            "Script admin-manager-updated.js inclus"
        ),
        (
            r'admin-updated\.html',
            "Modal admin-updated.html inclus"
        ),
        (
            r'// Fonction globale pour ouvrir le modal d\'administration - VERSION CORRIGÉE',
            "Fonction openAdminModal corrigée"
        ),
        (
            r'// Vérifier si AdminManager est disponible',
            "Vérification AdminManager ajoutée"
        ),
        (
            r'// Fallback : ouvrir le modal directement',
            "Fallback simplifié"
        )
    ]
    
    for pattern, description in base_checks:
        result, message = check_file_contains("frontend/templates/base.html", pattern, description)
        print(f"  {message}")
        checks.append(result)
    
    # 3. Vérifier les corrections dans admin-manager-updated.js
    print("\n🔧 Vérification des corrections dans admin-manager-updated.js:")
    
    js_checks = [
        (
            r'// Créer l\'instance globale immédiatement',
            "Initialisation immédiate ajoutée"
        ),
        (
            r'window\.adminManager = new AdminManager\(\);',
            "Instance AdminManager créée"
        ),
        (
            r'console\.log\(\'✅ Instance AdminManager créée\'\);',
            "Log de confirmation ajouté"
        ),
        (
            r'console\.warn\(\'⚠️ Modal adminModal non trouvé\'\);',
            "Vérification modal ajoutée"
        )
    ]
    
    for pattern, description in js_checks:
        result, message = check_file_contains("frontend/static/js/modules/admin-manager-updated.js", pattern, description)
        print(f"  {message}")
        checks.append(result)
    
    # 4. Vérifier les corrections dans admin-manager.js (ancien fichier)
    print("\n🔧 Vérification des corrections dans admin-manager.js:")
    
    old_js_checks = [
        (
            r'// Vérifier que les éléments existent avant de les mettre à jour',
            "Vérification éléments ajoutée"
        ),
        (
            r'if \(totalServersEl\.length\)',
            "Vérification existence éléments"
        ),
        (
            r'console\.log\(\'✅ Compteurs mis à jour\'\);',
            "Log de confirmation compteurs"
        )
    ]
    
    for pattern, description in old_js_checks:
        result, message = check_file_contains("frontend/static/js/modules/admin-manager.js", pattern, description)
        print(f"  {message}")
        checks.append(result)
    
    # 5. Vérifier les routes de test
    print("\n🧪 Vérification des routes de test:")
    
    route_checks = [
        (
            r'@app\.route\(\'/test-admin-coherence\'\)',
            "Route test-admin-coherence ajoutée"
        ),
        (
            r'@app\.route\(\'/test-admin-diagnostic\'\)',
            "Route test-admin-diagnostic ajoutée"
        )
    ]
    
    for pattern, description in route_checks:
        result, message = check_file_contains("backend/app.py", pattern, description)
        print(f"  {message}")
        checks.append(result)
    
    # 6. Vérifier les fichiers de documentation
    print("\n📚 Vérification de la documentation:")
    
    doc_files = [
        "CORRECTION_CHARGEMENTS_SANS_FIN.md",
        "ANALYSE_INCOHERENCES_ADMIN.md"
    ]
    
    for filepath in doc_files:
        exists = check_file_exists(filepath)
        status = "✅" if exists else "❌"
        print(f"  {status} {filepath}")
        checks.append(exists)
    
    # Résumé
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    success_rate = (passed / total) * 100
    
    print(f"📊 Résumé: {passed}/{total} vérifications passées ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 Toutes les corrections ont été appliquées avec succès !")
        return True
    else:
        print("⚠️ Certaines corrections sont manquantes ou incomplètes.")
        return False

def main():
    """Fonction principale"""
    try:
        success = validate_corrections()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 