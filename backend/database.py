"""Gerenciamento de conexão e schema SQLite com suporte a chaves estrangeiras."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

from backend.config import get_db_path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    url TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    stack TEXT NOT NULL DEFAULT '',
    criada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    resposta TEXT NOT NULL CHECK (resposta IN ('ok', 'falha', 'nao_se_aplica', 'nao_verificado')),
    origem TEXT NOT NULL DEFAULT 'manual' CHECK (origem IN ('manual', 'scanner')),
    evidencia TEXT NOT NULL DEFAULT '',
    atualizado_em TEXT NOT NULL,
    UNIQUE (app_id, item_id),
    FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL,
    item_id TEXT,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    severidade TEXT NOT NULL CHECK (severidade IN ('critica', 'alta', 'media', 'baixa')),
    prioridade INTEGER NOT NULL CHECK (prioridade >= 1),
    status TEXT NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'em_correcao', 'corrigido')),
    recomendacao TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS finding_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id INTEGER NOT NULL,
    status_anterior TEXT,
    status_novo TEXT NOT NULL CHECK (status_novo IN ('aberto', 'em_correcao', 'corrigido')),
    alterado_em TEXT NOT NULL,
    FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_answers_app_id ON answers(app_id);
CREATE INDEX IF NOT EXISTS idx_findings_app_id ON findings(app_id);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
CREATE INDEX IF NOT EXISTS idx_findings_severidade ON findings(severidade);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Abre conexão SQLite com row_factory estruturado e foreign_keys habilitadas."""
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Inicializa as tabelas do banco de dados caso ainda não existam."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Dependência FastAPI para prover uma conexão SQLite por requisição."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
