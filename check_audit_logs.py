#!/usr/bin/env python3
"""
Script de vérification des logs d'audit - NTP Monitor
Affiche et analyse les logs d'audit générés par l'application
"""

import os
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def read_audit_log(log_file):
    """Lire et parser un fichier de log d'audit"""
    if not os.path.exists(log_file):
        return []
    
    entries = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Format: timestamp | level | json_data
                    parts = line.split(' | ', 2)
                    if len(parts) == 3:
                        timestamp_str, level, json_data = parts
                        
                        # Parser le JSON
                        data = json.loads(json_data)
                        
                        # Ajouter les métadonnées
                        data['log_timestamp'] = timestamp_str
                        data['log_level'] = level
                        data['log_line'] = line_num
                        
                        entries.append(data)
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ Erreur parsing ligne {line_num} dans {log_file}: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Erreur lecture {log_file}: {e}")
        return []
    
    return entries

def format_timestamp(timestamp_str):
    """Formater un timestamp pour l'affichage"""
    try:
        # Parser le timestamp ISO
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def analyze_audit_logs():
    """Analyser tous les logs d'audit"""
    log_dir = "logs"
    
    # Fichiers de logs d'audit
    log_files = {
        'auth': os.path.join(log_dir, 'auth_audit.log'),
        'crud': os.path.join(log_dir, 'crud_audit.log'),
        'admin': os.path.join(log_dir, 'admin_audit.log')
    }
    
    print("=" * 80)
    print("📋 ANALYSE DES LOGS D'AUDIT - NTP MONITOR")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_entries = []
    stats = defaultdict(int)
    
    # Lire tous les fichiers de logs
    for log_type, log_file in log_files.items():
        print(f"📄 Analyse de {log_file}...")
        
        if not os.path.exists(log_file):
            print(f"   ⚠️ Fichier non trouvé: {log_file}")
            continue
        
        entries = read_audit_log(log_file)
        all_entries.extend(entries)
        
        # Statistiques par type
        stats[f'{log_type}_entries'] = len(entries)
        
        if entries:
            print(f"   ✅ {len(entries)} entrées trouvées")
            
            # Dernière entrée
            last_entry = entries[-1]
            print(f"   📅 Dernière entrée: {format_timestamp(last_entry.get('timestamp', 'N/A'))}")
            print(f"   🎯 Action: {last_entry.get('action', 'N/A')}")
        else:
            print(f"   📭 Aucune entrée trouvée")
        
        print()
    
    if not all_entries:
        print("❌ Aucune entrée d'audit trouvée")
        return
    
    # Trier par timestamp
    all_entries.sort(key=lambda x: x.get('timestamp', ''))
    
    print("📊 STATISTIQUES GLOBALES")
    print("-" * 40)
    print(f"📈 Total des entrées: {len(all_entries)}")
    
    # Compter par action
    action_counts = defaultdict(int)
    user_actions = defaultdict(int)
    
    for entry in all_entries:
        action = entry.get('action', 'UNKNOWN')
        action_counts[action] += 1
        
        user_info = entry.get('user', {})
        username = user_info.get('username', 'Unknown')
        user_actions[username] += 1
    
    print("\n🎯 Actions les plus fréquentes:")
    for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {action}: {count}")
    
    print("\n👤 Utilisateurs les plus actifs:")
    for username, count in sorted(user_actions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {username}: {count}")
    
    # Dernières entrées
    print("\n🕐 DERNIÈRES ACTIVITÉS (10 plus récentes)")
    print("-" * 60)
    
    for entry in all_entries[-10:]:
        timestamp = format_timestamp(entry.get('timestamp', 'N/A'))
        action = entry.get('action', 'UNKNOWN')
        user_info = entry.get('user', {})
        username = user_info.get('username', 'Unknown')
        
        # Détails spécifiques selon l'action
        details = ""
        if action in ['LOGIN_SUCCESS', 'LOGIN_FAILED']:
            details = f"User: {entry.get('details', {}).get('username', 'N/A')}"
            if not entry.get('details', {}).get('success', False):
                details += f" | Reason: {entry.get('details', {}).get('reason', 'N/A')}"
        elif action in ['USER_CREATED', 'USER_UPDATED', 'USER_DELETED']:
            user_details = entry.get('details', {})
            if 'created_user' in user_details:
                details = f"User: {user_details['created_user'].get('username', 'N/A')}"
            elif 'username' in user_details:
                details = f"User: {user_details['username']}"
        elif action in ['USER_ACTIVATED', 'USER_DEACTIVATED']:
            details = f"User: {entry.get('details', {}).get('username', 'N/A')}"
        elif action == 'PASSWORD_GENERATED':
            details = f"User: {entry.get('details', {}).get('username', 'N/A')}"
        
        print(f"🕐 {timestamp} | {username} | {action}")
        if details:
            print(f"   📝 {details}")
        print()

def show_recent_auth_events(hours=24):
    """Afficher les événements d'authentification récents"""
    log_file = os.path.join("logs", "auth_audit.log")
    
    if not os.path.exists(log_file):
        print("❌ Fichier auth_audit.log non trouvé")
        return
    
    entries = read_audit_log(log_file)
    
    # Filtrer les entrées récentes
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_entries = []
    
    for entry in entries:
        try:
            entry_time = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
            if entry_time >= cutoff_time:
                recent_entries.append(entry)
        except:
            continue
    
    print(f"\n🔐 ÉVÉNEMENTS D'AUTHENTIFICATION ({hours}h)")
    print("-" * 50)
    
    if not recent_entries:
        print("📭 Aucun événement récent")
        return
    
    for entry in recent_entries[-20:]:  # 20 plus récents
        timestamp = format_timestamp(entry.get('timestamp', 'N/A'))
        action = entry.get('action', 'UNKNOWN')
        details = entry.get('details', {})
        username = details.get('username', 'N/A')
        
        # Icône selon le type d'événement
        if action == 'LOGIN_SUCCESS':
            icon = "✅"
        elif action == 'LOGIN_FAILED':
            icon = "❌"
        elif action == 'LOGOUT':
            icon = "🚪"
        else:
            icon = "🔑"
        
        print(f"{icon} {timestamp} | {username} | {action}")
        
        if action == 'LOGIN_FAILED':
            reason = details.get('reason', 'Unknown')
            print(f"   📝 Raison: {reason}")

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'auth':
            show_recent_auth_events()
        elif sys.argv[1] == 'auth-24h':
            show_recent_auth_events(24)
        elif sys.argv[1] == 'auth-7d':
            show_recent_auth_events(24 * 7)
        else:
            print("Usage: python check_audit_logs.py [auth|auth-24h|auth-7d]")
    else:
        analyze_audit_logs()

if __name__ == "__main__":
    main() 