# app/services/batigest/__init__.py
# Package Batigest - Gestion des flux de données Batigest

# Imports des fonctions principales pour faciliter l'utilisation
from .chantiers import (
    transfer_chantiers,
    transfer_chantiers_vers_batisimply,
    recup_chantiers_batisimply,
    recup_chantiers_postgres,
    recup_code_projet_chantiers,
    check_batigest_heures_content,
    update_code_projet_chantiers
)

from .heures import (
    transfer_heures_to_postgres,
    transfer_heures_to_sqlserver
)

from .devis import (
    transfer_devis,
    transfer_devis_vers_batisimply
)

from .sync import (
    sync_batigest_to_batisimply,
    sync_batisimply_to_batigest
)

from .utils import (
    init_postgres_table
)

# Exports publics
__all__ = [
    # Chantiers
    'transfer_chantiers',
    'transfer_chantiers_vers_batisimply',
    'recup_chantiers_batisimply',
    'recup_chantiers_postgres',
    'recup_code_projet_chantiers',
    'check_batigest_heures_content',
    'update_code_projet_chantiers',
    
    # Heures
    'transfer_heures_to_postgres',
    'transfer_heures_to_sqlserver',
    
    # Devis
    'transfer_devis',
    'transfer_devis_vers_batisimply',
    
    # Synchronisations complètes
    'sync_batigest_to_batisimply',
    'sync_batisimply_to_batigest',
    
    # Utilitaires
    'init_postgres_table'
]
