import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import quote_plus


load_dotenv("backend/.env")


# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_ENABLED = (
    os.getenv("DB_ENABLED", "false")
    .strip()
    .lower()
    == "true"
)

DB_SERVER = os.getenv(
    "DB_SERVER",
    "LAPTOP-C474B42G",
)

DB_NAME = os.getenv(
    "DB_NAME",
    "RiftLensDB",
)

DB_DRIVER = os.getenv(
    "DB_DRIVER",
    "ODBC Driver 17 for SQL Server",
)


# ============================================================
# SQLALCHEMY
# ============================================================

Base = declarative_base()

engine = None
SessionLocal = None


# ============================================================
# CREAR CONEXIÓN SOLO SI ESTÁ HABILITADA
# ============================================================

if DB_ENABLED:

    odbc_connection = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    DATABASE_URL = (
        "mssql+pyodbc:///?odbc_connect="
        + quote_plus(odbc_connection)
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )