"""Testes de integração da API AppHardener (P1 - Fase 1)."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import CONTRACTS_DIR
from backend.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Cria cliente de teste isolado apontando para um banco SQLite temporário
    db_file = tmp_path / "test_apphardener.db"
    monkeypatch.setenv("APPHARDENER_DB_PATH", str(db_file))
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_security_headers(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Cache-Control"] == "no-store"


def test_application_crud_and_persistence(client: TestClient) -> None:
    # Cadastrar aplicação
    payload = {
        "nome": "Portal Acadêmico Demo",
        "url": "http://127.0.0.1:5000",
        "descricao": "Aplicação web de demonstração para diagnóstico e hardening.",
        "stack": "Python / Flask / SQLite",
    }
    create_resp = client.post("/api/apps", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["id"] == 1
    assert created["nome"] == payload["nome"]
    assert created["url"] == "http://127.0.0.1:5000"
    assert created["descricao"] == payload["descricao"]
    assert created["stack"] == payload["stack"]
    assert created["criada_em"].endswith("Z")

    # Listar aplicações
    list_resp = client.get("/api/apps")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Buscar por ID
    get_resp = client.get("/api/apps/1")
    assert get_resp.status_code == 200
    assert get_resp.json()["nome"] == "Portal Acadêmico Demo"

    # Atualizar aplicação
    patch_resp = client.patch(
        "/api/apps/1",
        json={"nome": "Portal Acadêmico v2", "stack": "Python / FastAPI"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["nome"] == "Portal Acadêmico v2"
    assert patch_resp.json()["stack"] == "Python / FastAPI"

    # Remover aplicação
    del_resp = client.delete("/api/apps/1")
    assert del_resp.status_code == 204
    assert client.get("/api/apps/1").status_code == 404


def test_application_validation_rejects_invalid_url_and_short_name(
    client: TestClient,
) -> None:
    bad_url = client.post(
        "/api/apps",
        json={"nome": "App Inseguro", "url": "javascript:alert(1)"},
    )
    assert bad_url.status_code == 422

    short_name = client.post(
        "/api/apps",
        json={"nome": "A", "url": "http://127.0.0.1:8080"},
    )
    assert short_name.status_code == 422


def test_findings_crud_filters_history_and_cascade(client: TestClient) -> None:
    app_resp = client.post(
        "/api/apps",
        json={"nome": "Sistema Alvo", "url": "http://127.0.0.1:3000"},
    )
    app_id = app_resp.json()["id"]

    # Criar 2 achados
    f1_resp = client.post(
        f"/api/apps/{app_id}/findings",
        json={
            "item_id": "SEC-01",
            "titulo": "Segredo hardcoded em config.py",
            "descricao": "Chave JWT fixa encontrada no código.",
            "severidade": "critica",
            "prioridade": 1,
            "status": "aberto",
            "recomendacao": "Mover segredo para variável de ambiente.",
        },
    )
    assert f1_resp.status_code == 201
    f1 = f1_resp.json()
    assert f1["id"] == 1
    assert f1["severidade"] == "critica"
    assert f1["prioridade"] == 1
    assert f1["status"] == "aberto"

    f2_resp = client.post(
        f"/api/apps/{app_id}/findings",
        json={
            "item_id": "HDR-01",
            "titulo": "Ausência de Content-Security-Policy",
            "descricao": "Header CSP não enviado.",
            "severidade": "media",
            "recomendacao": "Configurar CSP restritivo.",
        },
    )
    assert f2_resp.status_code == 201
    f2 = f2_resp.json()
    assert f2["prioridade"] == 3  # prioridade default para severidade 'media'

    # Filtrar por severidade
    crit_list = client.get(
        f"/api/apps/{app_id}/findings", params={"severidade": "critica"}
    )
    assert crit_list.status_code == 200
    assert len(crit_list.json()) == 1
    assert crit_list.json()[0]["item_id"] == "SEC-01"

    # Atualizar status do achado 1: aberto -> em_correcao -> corrigido
    upd1 = client.patch(
        f"/api/apps/{app_id}/findings/{f1['id']}",
        json={"status": "em_correcao"},
    )
    assert upd1.status_code == 200
    assert upd1.json()["status"] == "em_correcao"

    upd2 = client.patch(
        f"/api/apps/{app_id}/findings/{f1['id']}",
        json={"status": "corrigido"},
    )
    assert upd2.status_code == 200
    assert upd2.json()["status"] == "corrigido"

    # Verificar histórico de status
    hist_resp = client.get(f"/api/apps/{app_id}/findings/{f1['id']}/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 3
    assert history[0]["status_anterior"] is None
    assert history[0]["status_novo"] == "aberto"
    assert history[1]["status_anterior"] == "aberto"
    assert history[1]["status_novo"] == "em_correcao"
    assert history[2]["status_anterior"] == "em_correcao"
    assert history[2]["status_novo"] == "corrigido"

    # Excluir achado 2
    del_f2 = client.delete(f"/api/apps/{app_id}/findings/{f2['id']}")
    assert del_f2.status_code == 204
    assert len(client.get(f"/api/apps/{app_id}/findings").json()) == 1


def test_contracts_compatibility_end_to_end(client: TestClient) -> None:
    """Garante que a API consome e produz exatamente os formatos de contracts/*.json."""
    apps_fixture = json.loads(
        (CONTRACTS_DIR / "applications.json").read_text(encoding="utf-8")
    )
    answers_fixture = json.loads(
        (CONTRACTS_DIR / "answers.json").read_text(encoding="utf-8")
    )
    findings_fixture = json.loads(
        (CONTRACTS_DIR / "findings.json").read_text(encoding="utf-8")
    )
    summary_fixture = json.loads(
        (CONTRACTS_DIR / "summary.json").read_text(encoding="utf-8")
    )

    # Cadastrar aplicação a partir do fixture
    app_input = {
        k: v for k, v in apps_fixture[0].items() if k not in ("id", "criada_em")
    }
    app_resp = client.post("/api/apps", json=app_input)
    assert app_resp.status_code == 201
    app_data = app_resp.json()
    assert set(app_data.keys()) == set(apps_fixture[0].keys())
    app_id = app_data["id"]

    # Salvar respostas do fixture
    ans_resp = client.put(f"/api/apps/{app_id}/answers", json=answers_fixture)
    assert ans_resp.status_code == 200
    assert ans_resp.json() == answers_fixture

    # Cadastrar os achados do fixture
    created_findings = []
    for f_item in findings_fixture:
        f_input = {k: v for k, v in f_item.items() if k not in ("id", "app_id")}
        f_resp = client.post(f"/api/apps/{app_id}/findings", json=f_input)
        assert f_resp.status_code == 201
        created_findings.append(f_resp.json())

    assert created_findings == findings_fixture

    # Consultar resumo consolidado e comparar com contracts/summary.json
    sum_resp = client.get(f"/api/apps/{app_id}/summary")
    assert sum_resp.status_code == 200
    assert sum_resp.json() == summary_fixture


def test_sql_injection_payload_is_stored_safely(client: TestClient) -> None:
    malicious_name = "App'); DROP TABLE applications; --"
    resp = client.post(
        "/api/apps",
        json={"nome": malicious_name, "url": "http://127.0.0.1:9000"},
    )
    assert resp.status_code == 201
    assert resp.json()["nome"] == malicious_name

    apps_list = client.get("/api/apps").json()
    assert len(apps_list) == 1
    assert apps_list[0]["nome"] == malicious_name
