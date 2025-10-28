# -*- coding: utf-8 -*-
"""
Gestionnaire minimal de connexions base de données.

Fournit des context managers pour PostgreSQL et SQL Server afin
de centraliser l'ouverture/fermeture et la lecture des identifiants.
"""

from contextlib import contextmanager
from typing import Optional
from .connex import (
    load_credentials,
    connect_to_postgres,
    connect_to_sqlserver,
)


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    @contextmanager
    def postgres(self):
        creds = load_credentials() or {}
        pg = creds.get("postgres")
        conn = None
        try:
            if not pg:
                yield None
                return
            conn = connect_to_postgres(
                pg.get("host"),
                pg.get("user"),
                pg.get("password"),
                pg.get("database"),
                pg.get("port", "5432"),
            )
            yield conn
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    @contextmanager
    def sqlserver(self):
        creds = load_credentials() or {}
        sql = creds.get("sqlserver")
        conn = None
        try:
            if not sql:
                yield None
                return
            conn = connect_to_sqlserver(
                sql.get("server"), sql.get("user"), sql.get("password"), sql.get("database")
            )
            yield conn
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

