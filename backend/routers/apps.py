"""Rotas para cadastro de aplicações, respostas do checklist e resumo consolidado."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend import repositories
from backend.database import get_db
from backend.schemas import (
    AnswerIn,
    AnswerOut,
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    AppSummaryOut,
)

router = APIRouter(prefix="/api/apps", tags=["Applications"])


def _require_app(conn: sqlite3.Connection, app_id: int) -> ApplicationOut:
    app = repositories.get_application(conn, app_id)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aplicação com id={app_id} não encontrada.",
        )
    return app


@router.get("", response_model=list[ApplicationOut])
def list_apps(conn: sqlite3.Connection = Depends(get_db)) -> list[ApplicationOut]:
    return repositories.list_applications(conn)


@router.post(
    "",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_app(
    payload: ApplicationCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> ApplicationOut:
    return repositories.create_application(conn, payload)


@router.get("/{app_id}", response_model=ApplicationOut)
def get_app(
    app_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> ApplicationOut:
    return _require_app(conn, app_id)


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_app(
    app_id: int,
    payload: ApplicationUpdate,
    conn: sqlite3.Connection = Depends(get_db),
) -> ApplicationOut:
    _require_app(conn, app_id)
    updated = repositories.update_application(conn, app_id, payload)
    assert updated is not None
    return updated


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(
    app_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _require_app(conn, app_id)
    repositories.delete_application(conn, app_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{app_id}/answers", response_model=list[AnswerOut])
def get_app_answers(
    app_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[AnswerOut]:
    _require_app(conn, app_id)
    return repositories.list_answers(conn, app_id)


@router.put("/{app_id}/answers", response_model=list[AnswerOut])
def save_app_answers(
    app_id: int,
    answers: list[AnswerIn],
    conn: sqlite3.Connection = Depends(get_db),
) -> list[AnswerOut]:
    _require_app(conn, app_id)
    return repositories.upsert_answers(conn, app_id, answers)


@router.get("/{app_id}/summary", response_model=AppSummaryOut)
def get_summary(
    app_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> AppSummaryOut:
    _require_app(conn, app_id)
    return repositories.get_app_summary(conn, app_id)
