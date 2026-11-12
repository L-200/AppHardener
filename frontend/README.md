# Módulo `frontend/` (Responsável: P3)

Interface web em HTML/CSS/JS puro (sem build e sem Node), com Chart.js local.

## Fluxo de trabalho
- **Fase 1**: Consome os arquivos estáticos de [`../contracts/`](../contracts/) para simular as respostas da API.
- **Fase 2**: Troca a URL base para consumir os endpoints reais (`/api/...`) servidos pelo FastAPI em `http://127.0.0.1:8000`.
