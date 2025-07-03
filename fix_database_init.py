#!/usr/bin/env python3
"""
Script de correction de l'initialisation du DatabaseManager
Problème: L'instance DatabaseManager est créée mais jamais initialisée
Solution: Forcer l'appel à initialize() lors de la création
"""

import os
import sys

def fix_database_manager_init():
    """Corriger l'initialisation du DatabaseManager"""
    
    database_manager_file = "/opt/NTPVIZ/backend/database_manager.py"
    
    print("🔧 Correction de l'initialisation du DatabaseManager...")
    
    try:
        # Lire le fichier
        with open(database_manager_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Fichier database_manager.py lu")
        
        # Remplacer la ligne de création de l'instance
        old_line = "db_manager = DatabaseManager()"
        new_lines = """# Créer et initialiser l'instance DatabaseManager
db_manager = DatabaseManager()
# CORRECTION: Forcer l'initialisation au démarrage
try:
    init_result = db_manager.initialize()
    if init_result:
        db_manager.logger.info("✅ Database Manager MySQL initialisé avec succès")
    else:
        db_manager.logger.error("❌ Échec initialisation Database Manager MySQL")
except Exception as e:
    db_manager.logger.error(f"❌ Erreur initialisation Database Manager: {e}")"""
        
        if old_line in content:
            print(f"🔧 Remplacement de: {old_line}")
            content = content.replace(old_line, new_lines)
            print("✅ Ligne remplacée avec initialisation forcée")
        else:
            print("⚠️ Ligne d'instance non trouvée, ajout à la fin")
            content += "\n" + new_lines
        
        # Sauvegarder le fichier original
        backup_file = database_manager_file + ".backup_init"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content.replace(new_lines, old_line))
        print(f"💾 Sauvegarde créée: {backup_file}")
        
        # Écrire le fichier corrigé
        with open(database_manager_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier database_manager.py corrigé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        return False

def main():
    print("🚀 Script de correction de l'initialisation DatabaseManager")
    
    if os.geteuid() != 0:
        print("❌ Ce script doit être exécuté en tant que root (sudo)")
        sys.exit(1)
    
    success = fix_database_manager_init()
    
    if success:
        print("\n✅ Correction terminée avec succès!")
        print("\n📋 Actions effectuées:")
        print("   - DatabaseManager instance créée ET initialisée")
        print("   - Initialisation forcée au démarrage")
        print("   - Logs d'initialisation ajoutés")
        print("\n🔄 Redémarrez le service ntp-monitor pour appliquer les corrections")
    else:
        print("\n❌ Échec de la correction")
        sys.exit(1)

if __name__ == "__main__":
    main() 