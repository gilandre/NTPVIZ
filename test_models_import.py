#!/usr/bin/env python3
"""
Test d'import de tous les modèles pour identifier les problèmes
"""
import sys
import os

# Ajouter le chemin de l'application
sys.path.insert(0, '/opt/NTPVIZ')
os.chdir('/opt/NTPVIZ')

print("🧪 Test d'import des modèles...")

models_to_test = [
    ('backend.models.user', 'User'),
    ('backend.models.ntp_server', 'NTPServer'), 
    ('backend.models.ntp_log', 'NTPLog'),
    ('backend.models.alert', 'Alert'),
    ('backend.models.system_config', 'SystemConfig'),
    ('backend.models.alert_threshold', 'AlertThreshold'),
    ('backend.models.ntp_log_aggregated', 'BaseNTPLogAggregated')
]

for module_name, class_name in models_to_test:
    try:
        print(f"\n📦 Test import {module_name}.{class_name}...")
        
        # Import du module
        module = __import__(module_name, fromlist=[class_name])
        print(f"  ✅ Module {module_name} importé")
        
        # Import de la classe
        cls = getattr(module, class_name)
        print(f"  ✅ Classe {class_name} importée")
        
        # Test de base de la classe
        print(f"  ✅ Classe {class_name}: {cls}")
        
    except Exception as e:
        print(f"  ❌ Erreur {module_name}.{class_name}: {e}")
        import traceback
        traceback.print_exc()

print("\n🎯 Test terminé") 