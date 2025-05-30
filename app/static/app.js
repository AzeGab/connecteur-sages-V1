document.addEventListener('DOMContentLoaded', function() {
    // Animation permanente de l'icône de synchronisation
    var syncIcon = document.getElementById('syncIcon');
    if (syncIcon) {
        syncIcon.classList.add('animate-spin');
    }

    // Fonctions de synchronisation
    window.syncBatigestToBatisimply = function() {
        showSyncStatus('Synchronisation Batigest → Batisimply en cours...', 'blue');
        setTimeout(() => {
            showSyncSuccess('Synchronisation Batigest → Batisimply terminée avec succès !');
        }, 3000);
    };

    window.syncBatisimplyToBatigest = function() {
        showSyncStatus('Synchronisation Batisimply → Batigest en cours...', 'purple');
        setTimeout(() => {
            showSyncSuccess('Synchronisation Batisimply → Batigest terminée avec succès !');
        }, 3000);
    };

    window.showSyncStatus = function(message, color) {
        const statusDiv = document.getElementById('statusMessage');
        const colorClasses = color === 'blue' ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-purple-50 border-purple-200 text-purple-700';
        statusDiv.innerHTML = `
            <div class="${colorClasses} border rounded-2xl p-6 text-center">
                <div class="flex items-center justify-center mb-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-current"></div>
                </div>
                <p class="font-medium">${message}</p>
            </div>
        `;
        statusDiv.classList.remove('hidden');
    };

    window.showSyncSuccess = function(message) {
        const statusDiv = document.getElementById('statusMessage');
        statusDiv.innerHTML = `
            <div class="bg-green-50 border border-green-200 text-green-700 rounded-2xl p-6 text-center">
                <div class="flex items-center justify-center mb-4">
                    <i class="fas fa-check-circle text-3xl text-green-500"></i>
                </div>
                <p class="font-medium">${message}</p>
            </div>
        `;
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    };

    // Simulation de mise à jour du statut des connexions
    window.updateConnectionStatus = function() {
        // Vous pouvez connecter ceci à votre API réelle
        const sqlStatus = document.getElementById('sqlStatus');
        const pgStatus = document.getElementById('pgStatus');
        // Exemple de mise à jour (à remplacer par votre logique)
        // sqlStatus.innerHTML = '<i class="fas fa-check-circle text-xs"></i><span>Connecté</span>';
        // sqlStatus.className = 'px-3 py-1 bg-green-100 text-green-600 rounded-full text-sm font-medium flex items-center space-x-1';
    };
});
