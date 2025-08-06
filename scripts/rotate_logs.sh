#!/bin/bash
# Script de rotation des logs pour NTP Monitor

LOG_FILE="logs/app.log"
MAX_SIZE_MB=10
BACKUP_DIR="logs/backups"

# Créer le répertoire de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Vérifier la taille du fichier
if [ -f "$LOG_FILE" ]; then
    SIZE_MB=$(du -m "$LOG_FILE" | cut -f1)
    
    if [ "$SIZE_MB" -gt "$MAX_SIZE_MB" ]; then
        echo "Rotation des logs - Taille: ${SIZE_MB}MB"
        
        # Créer le backup
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="$BACKUP_DIR/app.log.$TIMESTAMP"
        
        # Garder les 1000 dernières lignes
        tail -n 1000 "$LOG_FILE" > "$BACKUP_FILE"
        
        # Tronquer le fichier original
        tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "$LOG_FILE"
        
        echo "Logs rotés: $BACKUP_FILE"
        
        # Nettoyer les anciens backups (garder les 5 plus récents)
        ls -t "$BACKUP_DIR"/app.log.* 2>/dev/null | tail -n +6 | xargs -r rm
        
    else
        echo "Taille de log acceptable: ${SIZE_MB}MB"
    fi
else
    echo "Fichier de log non trouvé"
fi
