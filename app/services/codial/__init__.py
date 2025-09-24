# app/services/codial/__init__.py
# Package Codial - Gestion des flux de données Codial

# Imports des fonctions principales pour faciliter l'utilisation
from .chantiers import (
    transfer_chantiers_codial,
    transfer_chantiers_codial_vers_batisimply
)

from .heures import (
    transfer_heures_batisimply_to_hfsql
)

from .sync import (
    sync_codial_to_batisimply,
    sync_batisimply_to_codial
)

from .utils import (
    init_codial_postgres_table
)

# Exports publics
__all__ = [
    # Chantiers
    'transfer_chantiers_codial',
    'transfer_chantiers_codial_vers_batisimply',
    
    # Heures
    'transfer_heures_batisimply_to_hfsql',
    
    # Synchronisations complètes
    'sync_codial_to_batisimply',
    'sync_batisimply_to_codial',
    
    # Utilitaires
    'init_codial_postgres_table'
]
