# Módulo `backend/` (Responsável: P1)

API FastAPI, banco de dados SQLite e modelos de dados (`Application`, `Answer`, `Finding`, `Summary`).

## Responsabilidades
- CRUD de aplicações e achados; status e histórico de correção; endpoint de resumo consolidado.
- Proteções da API: validação com Pydantic, consultas parametrizadas, bind exclusivo em `127.0.0.1` e headers de segurança.
- Na Fase 2, importa `engine` (P2) e `scanner` (P4) e serve o `frontend/` (P3).
