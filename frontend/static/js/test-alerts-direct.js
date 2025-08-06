/**
 * Script de test direct pour forcer la mise à jour des badges d'alertes
 * À exécuter dans la console du navigateur
 */

console.log('🔧 Script de test direct des alertes');

// Fonction pour tester les APIs
async function testAlertsAPI() {
    console.log('📡 Test des APIs d\'alertes...');
    
    try {
        const response = await fetch('/api/alerts/summary');
        const data = await response.json();
        
        console.log('✅ API Summary:', data);
        
        if (data.success && data.summary) {
            const summary = data.summary;
            console.log(`📊 Alertes actives: ${summary.active_alerts}`);
            console.log(`🔴 Critiques: ${summary.by_severity?.critical?.active || 0}`);
            console.log(`🟡 Warnings: ${summary.by_severity?.warning?.active || 0}`);
            
            return summary;
        }
    } catch (error) {
        console.error('❌ Erreur API:', error);
    }
    
    return null;
}

// Fonction pour mettre à jour les badges manuellement
function updateBadgesManually(summary) {
    console.log('🏷️ Mise à jour manuelle des badges...');
    
    if (!summary) {
        console.log('❌ Pas de données summary');
        return;
    }
    
    const activeCount = summary.active_alerts || 0;
    const criticalCount = summary.by_severity?.critical?.active || 0;
    const warningCount = summary.by_severity?.warning?.active || 0;
    
    // Mettre à jour tous les badges avec l'ID alerts-count
    const alertsCountElements = document.querySelectorAll('#alerts-count');
    alertsCountElements.forEach((element, index) => {
        element.textContent = activeCount;
        console.log(`✅ Badge #alerts-count ${index + 1} mis à jour: ${activeCount}`);
    });
    
    // Mettre à jour tous les badges avec la classe alerts-count-badge
    const alertsBadgeElements = document.querySelectorAll('.alerts-count-badge');
    alertsBadgeElements.forEach((element, index) => {
        element.textContent = activeCount;
        element.style.display = activeCount > 0 ? 'inline-block' : 'none';
        console.log(`✅ Badge .alerts-count-badge ${index + 1} mis à jour: ${activeCount}`);
    });
    
    // Mettre à jour les badges par sévérité
    const criticalBadges = document.querySelectorAll('[data-severity="critical"]');
    criticalBadges.forEach((element, index) => {
        element.textContent = criticalCount;
        console.log(`✅ Badge critique ${index + 1} mis à jour: ${criticalCount}`);
    });
    
    const warningBadges = document.querySelectorAll('[data-severity="warning"]');
    warningBadges.forEach((element, index) => {
        element.textContent = warningCount;
        console.log(`✅ Badge warning ${index + 1} mis à jour: ${warningCount}`);
    });
    
    console.log('🎉 Mise à jour manuelle terminée');
}

// Fonction pour diagnostiquer les éléments
function diagnosticElements() {
    console.log('🔍 Diagnostic des éléments...');
    
    const alertsCountElements = document.querySelectorAll('#alerts-count');
    console.log(`📍 Éléments #alerts-count trouvés: ${alertsCountElements.length}`);
    alertsCountElements.forEach((el, i) => {
        console.log(`  ${i + 1}. Valeur actuelle: "${el.textContent}"`);
    });
    
    const alertsBadgeElements = document.querySelectorAll('.alerts-count-badge');
    console.log(`📍 Éléments .alerts-count-badge trouvés: ${alertsBadgeElements.length}`);
    alertsBadgeElements.forEach((el, i) => {
        console.log(`  ${i + 1}. Valeur actuelle: "${el.textContent}"`);
    });
    
    // Vérifier les scripts
    const scripts = document.querySelectorAll('script[src*="alert"]');
    console.log(`📜 Scripts d'alertes trouvés: ${scripts.length}`);
    scripts.forEach((script, i) => {
        console.log(`  ${i + 1}. ${script.src}`);
    });
    
    // Vérifier les gestionnaires
    console.log('🔧 Gestionnaires disponibles:');
    console.log('  - window.optimizedAlertManager:', typeof window.optimizedAlertManager);
    console.log('  - window.alertManager:', typeof window.alertManager);
    console.log('  - window.openAlertsModal:', typeof window.openAlertsModal);
}

// Fonction principale de test
async function runFullTest() {
    console.log('🚀 Démarrage du test complet...');
    
    // 1. Diagnostic
    diagnosticElements();
    
    // 2. Test API
    const summary = await testAlertsAPI();
    
    // 3. Mise à jour manuelle
    if (summary) {
        updateBadgesManually(summary);
    }
    
    // 4. Test des gestionnaires
    console.log('🔧 Test des gestionnaires...');
    if (window.optimizedAlertManager) {
        console.log('✅ OptimizedAlertManager disponible');
        if (typeof window.optimizedAlertManager.updateAllAlerts === 'function') {
            console.log('🔄 Exécution de updateAllAlerts...');
            window.optimizedAlertManager.updateAllAlerts();
        }
    } else {
        console.log('❌ OptimizedAlertManager non disponible');
    }
    
    console.log('✅ Test complet terminé');
}

// Exécuter le test automatiquement
runFullTest();

// Exposer les fonctions pour utilisation manuelle
window.testAlertsAPI = testAlertsAPI;
window.updateBadgesManually = updateBadgesManually;
window.diagnosticElements = diagnosticElements;
window.runFullTest = runFullTest; 