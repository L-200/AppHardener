# Módulo `backend/` (Responsável: P1)

API FastAPI, persistência em SQLite e validação de dados (`Application`, `Answer`, `Finding`, `Summary`) para o **AppHardener**.

---

## 1. Estrutura do Módulo

```text
backend/
├── __init__.py
├── config.py          # Configurações de bind local (127.0.0.1:8000) e caminho do SQLite
├── database.py        # Conexão SQLite, PRAGMA foreign_keys = ON e criação de tabelas/índices
├── schemas.py         # Modelos Pydantic alinhados ao contrato em contracts/
├── repositories.py    # Consultas SQL parametrizadas (CRUD, histórico e resumo consolidado)
├── main.py            # Aplicação FastAPI, middlewares de segurança e health check
├── routers/
│   ├── apps.py        # Endpoints de aplicações, respostas do checklist e resumo
│   └── findings.py    # Endpoints de achados, filtros e histórico de status
└── tests/
    └── test_api.py    # Testes de integração, validação, SQLi e conformidade com contracts/
```

---

## 2. Endpoints Implementados (Fase 1)

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/health` | Verifica disponibilidade da API e cabeçalhos de segurança |
| `GET` | `/api/apps` | Lista aplicações cadastradas |
| `POST` | `/api/apps` | Cadastra nova aplicação no SQLite |
| `GET` | `/api/apps/{app_id}` | Obtém detalhes de uma aplicação |
| `PATCH` | `/api/apps/{app_id}` | Atualiza dados de uma aplicação |
| `DELETE` | `/api/apps/{app_id}` | Remove aplicação e seus achados/respostas em cascata |
| `GET` | `/api/apps/{app_id}/findings` | Lista achados da aplicação (filtros: `severidade`, `status`, `item_id`) |
| `POST` | `/api/apps/{app_id}/findings` | Registra novo achado de segurança no SQLite |
| `GET` | `/api/apps/{app_id}/findings/{finding_id}` | Obtém detalhes de um achado específico |
| `PATCH` | `/api/apps/{app_id}/findings/{finding_id}` | Atualiza o `status` (`aberto`, `em_correcao`, `corrigido`) e grava histórico |
| `DELETE` | `/api/apps/{app_id}/findings/{finding_id}` | Remove um achado específico |
| `GET` | `/api/apps/{app_id}/findings/{finding_id}/history` | Lista o histórico de transições de status do achado |
| `GET` | `/api/apps/{app_id}/answers` | Lista respostas registradas do checklist para a aplicação |
| `PUT` | `/api/apps/{app_id}/answers` | Salva/atualiza respostas do checklist no SQLite |
| `GET` | `/api/apps/{app_id}/summary` | Retorna o resumo consolidado conforme `contracts/summary.json` |

---

## 3. Controles de Segurança Aplicados na Própria API

- **Bind exclusivo local**: Configurado por padrão em `127.0.0.1:8000`.
- **Validação estrita de entrada (Pydantic)**: Validação de URLs (`http`/`https` via `AnyHttpUrl`), limites de tamanho, rejeição de campos extras e validação por `Literal` de severidades e status.
- **Prevenção de SQL Injection**: Todas as operações no SQLite utilizam exclusivamente consultas parametrizadas (`?`) e `CHECK` constraints no schema.
- **Cabeçalhos de segurança HTTP**: Middleware adiciona `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`, `Referrer-Policy: strict-origin-when-cross-origin` e `Cache-Control: no-store`.

---

## 4. Como Executar e Testar

Na raiz do repositório (`AppHardener/`):

```bash
# Executar a suíte de testes do módulo P1
.venv/bin/pytest backend/tests -v

# Iniciar o servidor localmente em http://127.0.0.1:8000
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
