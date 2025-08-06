/**
 * Script de nettoyage pour éviter les conflits d'alertes
 * À charger avant les autres scripts d'alertes
 * 
 * ⚠️ DÉSACTIVÉ - Ce script causait des conflits avec les mises à jour temps réel
 * Les timers sont maintenant gérés par le gestionnaire unifié
 */

console.log('⚠️ Script alert-cleanup.js désactivé pour éviter les conflits de timers');

// Fonction de nettoyage désactivée
function stopAllAlertTimers() {
    console.log('⚠️ stopAllAlertTimers désactivée - utiliser le gestionnaire unifié');
    return;
}

// Fonction de nettoyage désactivée
function cleanupGlobalVariables() {
    console.log('⚠️ cleanupGlobalVariables désactivée - utiliser le gestionnaire unifié');
    return;
}

// Fonction de désactivation désactivée
function disableOldManagers() {
    console.log('⚠️ disableOldManagers désactivée - utiliser le gestionnaire unifié');
    return;
}

// Fonction principale désactivée
function performCleanup() {
    console.log('⚠️ performCleanup désactivée - utiliser le gestionnaire unifié');
    return;
}

// Ne pas exécuter le nettoyage automatiquement
// performCleanup();

// Ne pas programmer de nettoyage périodique
// setInterval(performCleanup, 30000);

console.log('✅ Script alert-cleanup.js désactivé avec succès');
