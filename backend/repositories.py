"""Camada de persistência SQLite utilizando exclusivamente consultas parametrizadas"""

import json
import sqlite3
from datetime import datetime, timezone

from backend.config import CONTRACTS_DIR
from backend.schemas import (
    AnswerIn,
    AnswerOut,
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    AppSummaryOut,
    CategorySummaryCount,
    FindingCreate,
    FindingHistoryOut,
    FindingOut,
    FindingStatus,
    FindingStatusUpdate,
    SeverityLevel,
)

def _utc_now_iso() -> str:
    # Retorna timestamp UTC
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _row_to_app(row: sqlite3.Row) -> ApplicationOut:
    return ApplicationOut(
        id=row["id"],
        nome=row["nome"],
        url=row["url"],
        descricao=row["descricao"],
        stack=row["stack"],
        criada_em=row["criada_em"],
    )

def _row_to_finding(row: sqlite3.Row) -> FindingOut:
    return FindingOut(
        id=row["id"],
        app_id=row["app_id"],
        item_id=row["item_id"],
        titulo=row["titulo"],
        descricao=row["descricao"],
        severidade=row["severidade"],
        prioridade=row["prioridade"],
        status=row["status"],
        recomendacao=row["recomendacao"],
    )

def _load_item_categories() -> dict[str, str]:
    # Carrega o mapeamento item_id -> categoria do contrato (ou engine quando integrado)
    checklist_file = CONTRACTS_DIR / "checklist.json"
    if not checklist_file.exists():
        return {}
    try:
        items = json.loads(checklist_file.read_text(encoding="utf-8"))
        return {
            str(item["id"]): str(item["categoria"])
            for item in items
            if isinstance(item, dict) and "id" in item and "categoria" in item
        }
    except (OSError, ValueError):
        return {}

# Applications CRUD

def list_applications(conn: sqlite3.Connection) -> list[ApplicationOut]:
    cursor = conn.execute(
        "SELECT id, nome, url, descricao, stack, criada_em FROM applications ORDER BY id ASC;"
    )
    return [_row_to_app(row) for row in cursor.fetchall()]

def get_application(conn: sqlite3.Connection, app_id: int) -> ApplicationOut | None:
    cursor = conn.execute(
        "SELECT id, nome, url, descricao, stack, criada_em FROM applications WHERE id = ?;",
        (app_id,),
    )
    row = cursor.fetchone()
    return _row_to_app(row) if row else None

def create_application(
    conn: sqlite3.Connection, payload: ApplicationCreate
) -> ApplicationOut:
    now = _utc_now_iso()
    cursor = conn.execute(
        """
        INSERT INTO applications (nome, url, descricao, stack, criada_em)
        VALUES (?, ?, ?, ?, ?);
        """,
        (payload.nome, payload.url, payload.descricao, payload.stack, now),
    )
    conn.commit()
    app_id = int(cursor.lastrowid)
    created = get_application(conn, app_id)
    assert created is not None
    return created

def update_application(
    conn: sqlite3.Connection, app_id: int, payload: ApplicationUpdate
) -> ApplicationOut | None:
    existing = get_application(conn, app_id)
    if existing is None:
        return None

    nome = payload.nome if payload.nome is not None else existing.nome
    url = payload.url if payload.url is not None else existing.url
    descricao = payload.descricao if payload.descricao is not None else existing.descricao
    stack = payload.stack if payload.stack is not None else existing.stack

    conn.execute(
        """
        UPDATE applications
        SET nome = ?, url = ?, descricao = ?, stack = ?
        WHERE id = ?;
        """,
        (nome, url, descricao, stack, app_id),
    )
    conn.commit()
    return get_application(conn, app_id)

def delete_application(conn: sqlite3.Connection, app_id: int) -> bool:
    cursor = conn.execute("DELETE FROM applications WHERE id = ?;", (app_id,))
    conn.commit()
    return cursor.rowcount > 0

# Findings CRUD & Status History

def list_findings(
    conn: sqlite3.Connection,
    app_id: int,
    severidade: SeverityLevel | None = None,
    status: FindingStatus | None = None,
    item_id: str | None = None,
) -> list[FindingOut]:
    query = """
        SELECT id, app_id, item_id, titulo, descricao, severidade, prioridade, status, recomendacao
        FROM findings
        WHERE app_id = ?
    """
    params: list[object] = [app_id]

    if severidade is not None:
        query += " AND severidade = ?"
        params.append(severidade)
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    if item_id is not None:
        query += " AND item_id = ?"
        params.append(item_id)

    query += " ORDER BY prioridade ASC, id ASC;"
    cursor = conn.execute(query, tuple(params))
    return [_row_to_finding(row) for row in cursor.fetchall()]

def get_finding(
    conn: sqlite3.Connection, app_id: int, finding_id: int
) -> FindingOut | None:
    cursor = conn.execute(
        """
        SELECT id, app_id, item_id, titulo, descricao, severidade, prioridade, status, recomendacao
        FROM findings
        WHERE app_id = ? AND id = ?;
        """,
        (app_id, finding_id),
    )
    row = cursor.fetchone()
    return _row_to_finding(row) if row else None

def create_finding(
    conn: sqlite3.Connection, app_id: int, payload: FindingCreate
) -> FindingOut:
    now = _utc_now_iso()
    assert payload.prioridade is not None
    cursor = conn.execute(
        """
        INSERT INTO findings (
            app_id, item_id, titulo, descricao, severidade, prioridade, status, recomendacao, criado_em, atualizado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            app_id,
            payload.item_id,
            payload.titulo,
            payload.descricao,
            payload.severidade,
            payload.prioridade,
            payload.status,
            payload.recomendacao,
            now,
            now,
        ),
    )
    finding_id = int(cursor.lastrowid)
    conn.execute(
        """
        INSERT INTO finding_status_history (finding_id, status_anterior, status_novo, alterado_em)
        VALUES (?, ?, ?, ?);
        """,
        (finding_id, None, payload.status, now),
    )
    conn.commit()
    created = get_finding(conn, app_id, finding_id)
    assert created is not None
    return created

def update_finding_status(
    conn: sqlite3.Connection,
    app_id: int,
    finding_id: int,
    payload: FindingStatusUpdate,
) -> FindingOut | None:
    existing = get_finding(conn, app_id, finding_id)
    if existing is None:
        return None

    now = _utc_now_iso()
    if existing.status != payload.status:
        conn.execute(
            """
            UPDATE findings
            SET status = ?, atualizado_em = ?
            WHERE app_id = ? AND id = ?;
            """,
            (payload.status, now, app_id, finding_id),
        )
        conn.execute(
            """
            INSERT INTO finding_status_history (finding_id, status_anterior, status_novo, alterado_em)
            VALUES (?, ?, ?, ?);
            """,
            (finding_id, existing.status, payload.status, now),
        )
        conn.commit()

    return get_finding(conn, app_id, finding_id)

def delete_finding(conn: sqlite3.Connection, app_id: int, finding_id: int) -> bool:
    cursor = conn.execute(
        "DELETE FROM findings WHERE app_id = ? AND id = ?;",
        (app_id, finding_id),
    )
    conn.commit()
    return cursor.rowcount > 0

def list_finding_history(
    conn: sqlite3.Connection, app_id: int, finding_id: int
) -> list[FindingHistoryOut] | None:
    if get_finding(conn, app_id, finding_id) is None:
        return None
    cursor = conn.execute(
        """
        SELECT id, finding_id, status_anterior, status_novo, alterado_em
        FROM finding_status_history
        WHERE finding_id = ?
        ORDER BY id ASC;
        """,
        (finding_id,),
    )
    return [
        FindingHistoryOut(
            id=row["id"],
            finding_id=row["finding_id"],
            status_anterior=row["status_anterior"],
            status_novo=row["status_novo"],
            alterado_em=row["alterado_em"],
        )
        for row in cursor.fetchall()
    ]

# Answers & Consolidated Summary

def upsert_answers(
    conn: sqlite3.Connection, app_id: int, answers: list[AnswerIn]
) -> list[AnswerOut]:
    now = _utc_now_iso()
    for ans in answers:
        conn.execute(
            """
            INSERT INTO answers (app_id, item_id, resposta, origem, evidencia, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(app_id, item_id) DO UPDATE SET
                resposta = excluded.resposta,
                origem = excluded.origem,
                evidencia = excluded.evidencia,
                atualizado_em = excluded.atualizado_em;
            """,
            (app_id, ans.item_id, ans.resposta, ans.origem, ans.evidencia, now),
        )
    conn.commit()
    return list_answers(conn, app_id)


def list_answers(conn: sqlite3.Connection, app_id: int) -> list[AnswerOut]:
    cursor = conn.execute(
        """
        SELECT app_id, item_id, resposta, origem, evidencia
        FROM answers
        WHERE app_id = ?
        ORDER BY id ASC;
        """,
        (app_id,),
    )
    return [
        AnswerOut(
            app_id=row["app_id"],
            item_id=row["item_id"],
            resposta=row["resposta"],
            origem=row["origem"],
            evidencia=row["evidencia"],
        )
        for row in cursor.fetchall()
    ]


def get_app_summary(conn: sqlite3.Connection, app_id: int) -> AppSummaryOut:
    por_severidade: dict[SeverityLevel, int] = {
        "critica": 0,
        "alta": 0,
        "media": 0,
        "baixa": 0,
    }
    por_status: dict[FindingStatus, int] = {
        "aberto": 0,
        "em_correcao": 0,
        "corrigido": 0,
    }

    findings = list_findings(conn, app_id)
    for finding in findings:
        por_severidade[finding.severidade] += 1
        por_status[finding.status] += 1

    total_achados = len(findings)
    answers = list_answers(conn, app_id)
    item_categories = _load_item_categories()
    por_categoria: dict[str, CategorySummaryCount] = {}

    if answers:
        avaliados = [a for a in answers if a.resposta != "nao_se_aplica"]
        total_itens_avaliados = len(avaliados)
        ok_count = sum(1 for a in avaliados if a.resposta == "ok")
        percentual_atendido = (
            round((ok_count / total_itens_avaliados) * 100.0, 1)
            if total_itens_avaliados > 0
            else 0.0
        )

        for ans in answers:
            categoria = item_categories.get(ans.item_id, "Geral")
            if categoria not in por_categoria:
                por_categoria[categoria] = CategorySummaryCount()
            counts = por_categoria[categoria]
            if ans.resposta == "ok":
                counts.ok += 1
            elif ans.resposta == "falha":
                counts.falha += 1
            elif ans.resposta == "nao_se_aplica":
                counts.nao_se_aplica += 1
            elif ans.resposta == "nao_verificado":
                counts.nao_verificado += 1
    else:
        total_itens_avaliados = total_achados
        percentual_atendido = (
            round((por_status["corrigido"] / total_achados) * 100.0, 1)
            if total_achados > 0
            else 0.0
        )
        for finding in findings:
            categoria = (
                item_categories.get(finding.item_id, "Geral")
                if finding.item_id
                else "Geral"
            )
            if categoria not in por_categoria:
                por_categoria[categoria] = CategorySummaryCount()
            counts = por_categoria[categoria]
            if finding.status == "corrigido":
                counts.ok += 1
            else:
                counts.falha += 1

    return AppSummaryOut(
        app_id=app_id,
        percentual_atendido=percentual_atendido,
        total_itens_avaliados=total_itens_avaliados,
        total_achados=total_achados,
        por_severidade=por_severidade,
        por_status=por_status,
        por_categoria=por_categoria,
    )
