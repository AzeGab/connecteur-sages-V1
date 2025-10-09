# app/services/codial/__init__.py
# Package Codial - Gestion des synchronisations avec Codial (HFSQL)
# Organisation par flux de données

# Flux HFSQL -> PostgreSQL -> BatiSimply
from .hfsql_to_batisimply import (
    transfer_chantiers_hfsql_to_postgres,
    transfer_chantiers_postgres_to_batisimply,
    transfer_heures_hfsql_to_postgres,
    transfer_heures_postgres_to_batisimply,
    sync_hfsql_to_batisimply
)

# Flux BatiSimply -> PostgreSQL -> HFSQL
from .batisimply_to_hfsql import (
    transfer_chantiers_batisimply_to_postgres,
    transfer_chantiers_postgres_to_hfsql,
    transfer_heures_batisimply_to_postgres,
    transfer_heures_postgres_to_hfsql,
    sync_batisimply_to_hfsql
)

# Utilitaires
from .utils import (
    init_codial_tables,
    check_codial_connection
)

# Exports publics
__all__ = [
    # Flux HFSQL -> PostgreSQL -> BatiSimply
    'transfer_chantiers_hfsql_to_postgres',
    'transfer_chantiers_postgres_to_batisimply',
    'transfer_heures_hfsql_to_postgres',
    'transfer_heures_postgres_to_batisimply',
    'sync_hfsql_to_batisimply',
    
    # Flux BatiSimply -> PostgreSQL -> HFSQL
    'transfer_chantiers_batisimply_to_postgres',
    'transfer_chantiers_postgres_to_hfsql',
    'transfer_heures_batisimply_to_postgres',
    'transfer_heures_postgres_to_hfsql',
    'sync_batisimply_to_hfsql',
    
    # Utilitaires
    'init_codial_tables',
    'check_codial_connection'
]