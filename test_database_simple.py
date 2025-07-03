#!/usr/bin/env python3
"""
Test d'import du database_manager pour diagnostiquer le problème
"""
import sys
import os

# Ajouter le chemin de l'application
sys.path.insert(0, '/opt/NTPVIZ')
os.chdir('/opt/NTPVIZ')

print("🧪 Test d'import du database_manager...")

try:
    print("1. Import du module backend.database_manager...")
    from backend.database_manager import db_manager
    print("✅ Import réussi")
    
    print(f"2. État d'initialisation: {db_manager.initialized}")
    print(f"3. Engine: {db_manager.engine}")
    print(f"4. SessionLocal: {db_manager.SessionLocal}")
    
    if not db_manager.initialized:
        print("❌ Database Manager PAS initialisé - c'est le problème !")
    else:
        print("✅ Database Manager initialisé correctement")
        
except Exception as e:
    print(f"❌ Erreur lors de l'import: {e}")
    import traceback
    traceback.print_exc() 