"""Rotas para registro, listagem, atualização de status e histórico de achados."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend import repositories
from backend.database import get_db
from backend.routers.apps import _require_app
from backend.schemas import (
    FindingCreate,
    FindingHistoryOut,
    FindingOut,
    FindingStatus,
    FindingStatusUpdate,
    SeverityLevel,
)

router = APIRouter(prefix="/api/apps/{app_id}/findings", tags=["Findings"])


@router.get("", response_model=list[FindingOut])
def list_app_findings(
    app_id: int,
    severidade: SeverityLevel | None = Query(default=None),
    finding_status: FindingStatus | None = Query(default=None, alias="status"),
    item_id: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[FindingOut]:
    _require_app(conn, app_id)
    return repositories.list_findings(
        conn,
        app_id=app_id,
        severidade=severidade,
        status=finding_status,
        item_id=item_id,
    )


@router.post(
    "",
    response_model=FindingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_app_finding(
    app_id: int,
    payload: FindingCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> FindingOut:
    _require_app(conn, app_id)
    return repositories.create_finding(conn, app_id, payload)


@router.get("/{finding_id}", response_model=FindingOut)
def get_app_finding(
    app_id: int,
    finding_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> FindingOut:
    _require_app(conn, app_id)
    finding = repositories.get_finding(conn, app_id, finding_id)
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achado com id={finding_id} não encontrado na aplicação {app_id}.",
        )
    return finding


@router.patch("/{finding_id}", response_model=FindingOut)
def update_app_finding_status(
    app_id: int,
    finding_id: int,
    payload: FindingStatusUpdate,
    conn: sqlite3.Connection = Depends(get_db),
) -> FindingOut:
    _require_app(conn, app_id)
    updated = repositories.update_finding_status(conn, app_id, finding_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achado com id={finding_id} não encontrado na aplicação {app_id}.",
        )
    return updated


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app_finding(
    app_id: int,
    finding_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _require_app(conn, app_id)
    deleted = repositories.delete_finding(conn, app_id, finding_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achado com id={finding_id} não encontrado na aplicação {app_id}.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{finding_id}/history", response_model=list[FindingHistoryOut])
def get_finding_history(
    app_id: int,
    finding_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[FindingHistoryOut]:
    _require_app(conn, app_id)
    history = repositories.list_finding_history(conn, app_id, finding_id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achado com id={finding_id} não encontrado na aplicação {app_id}.",
        )
    return history
