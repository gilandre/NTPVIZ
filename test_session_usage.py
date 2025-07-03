#!/usr/bin/env python3
"""
Test d'utilisation des sessions DatabaseManager pour identifier l'erreur 'NoneType' object is not callable
"""
import sys
import os

# Ajouter le chemin de l'application
sys.path.insert(0, '/opt/NTPVIZ')
os.chdir('/opt/NTPVIZ')

print("🧪 Test d'utilisation des sessions DatabaseManager...")

try:
    # Import du database_manager
    from backend.database_manager import db_manager
    print("✅ Database Manager importé")
    print(f"   Initialized: {db_manager.initialized}")
    
    # Test 1: get_session()
    print("\n1️⃣ Test get_session()...")
    session = db_manager.get_session()
    print(f"   Session retournée: {session}")
    print(f"   Type de session: {type(session)}")
    
    if session is None:
        print("❌ get_session() retourne None!")
    else:
        print("✅ get_session() fonctionne")
        
        # Test 2: Utilisation de la session
        print("\n2️⃣ Test utilisation session...")
        
        # Import du modèle NTPServer
        from backend.models.ntp_server import NTPServer
        print("✅ NTPServer importé")
        
        # Test requête simple
        print("   Test requête NTPServer...")
        try:
            servers = session.query(NTPServer).all()
            print(f"✅ Requête réussie: {len(servers)} serveurs trouvés")
            
            for server in servers:
                print(f"   - {server.name}: {server.address}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la requête: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            session.close()
            print("✅ Session fermée")
    
    # Test 3: get_session_context()
    print("\n3️⃣ Test get_session_context()...")
    try:
        with db_manager.get_session_context() as session:
            print("✅ Context manager fonctionne")
            servers = session.query(NTPServer).filter_by(is_active=True).all()
            print(f"✅ Requête dans context: {len(servers)} serveurs actifs")
            
    except Exception as e:
        print(f"❌ Erreur avec context manager: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Test terminé") 