# app/services/batigest/__init__.py
# Package Batigest - Gestion des synchronisations avec Batigest (SQL Server)
# Organisation par flux de données

# Flux SQL Server -> PostgreSQL -> BatiSimply
from .sqlserver_to_batisimply import (
    transfer_chantiers_sqlserver_to_postgres,
    transfer_chantiers_postgres_to_batisimply,
    transfer_heures_sqlserver_to_postgres,
    transfer_heures_postgres_to_batisimply,
    transfer_devis_sqlserver_to_postgres,
    transfer_devis_postgres_to_batisimply,
    sync_sqlserver_to_batisimply
)

# Flux BatiSimply -> PostgreSQL -> SQL Server
from .batisimply_to_sqlserver import (
    transfer_chantiers_batisimply_to_postgres,
    transfer_chantiers_postgres_to_sqlserver,
    transfer_heures_batisimply_to_postgres,
    transfer_heures_postgres_to_sqlserver,
    transfer_devis_batisimply_to_postgres,
    transfer_devis_postgres_to_sqlserver,
    sync_batisimply_to_sqlserver
)

# Utilitaires
from .utils import (
    init_batigest_tables,
    check_batigest_connection
)

# Exports publics
__all__ = [
    # Flux SQL Server -> PostgreSQL -> BatiSimply
    'transfer_chantiers_sqlserver_to_postgres',
    'transfer_chantiers_postgres_to_batisimply',
    'transfer_heures_sqlserver_to_postgres',
    'transfer_heures_postgres_to_batisimply',
    'transfer_devis_sqlserver_to_postgres',
    'transfer_devis_postgres_to_batisimply',
    'sync_sqlserver_to_batisimply',
    
    # Flux BatiSimply -> PostgreSQL -> SQL Server
    'transfer_chantiers_batisimply_to_postgres',
    'transfer_chantiers_postgres_to_sqlserver',
    'transfer_heures_batisimply_to_postgres',
    'transfer_heures_postgres_to_sqlserver',
    'transfer_devis_batisimply_to_postgres',
    'transfer_devis_postgres_to_sqlserver',
    'sync_batisimply_to_sqlserver',
    
    # Utilitaires
    'init_batigest_tables',
    'check_batigest_connection'
]