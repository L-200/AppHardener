"""Configurações da API e banco de dados do AppHardener"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_DB_PATH = BASE_DIR / "apphardener.db"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def get_db_path() -> Path:
    """Retorna o caminho do arquivo SQLite configurável via variável de ambiente."""
    env_path = os.getenv("APPHARDENER_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


HOST: str = os.getenv("APPHARDENER_HOST", "127.0.0.1")
PORT: int = int(os.getenv("APPHARDENER_PORT", "8000"))
