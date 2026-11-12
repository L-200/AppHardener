# Módulo `scanner/` (Responsável: P4)

Scanner passivo para verificação de headers de segurança, flags de cookies, redirecionamento HTTPS, caminhos expostos comuns e mensagens de erro.

## Interface esperada (Fase 1 / Fase 2)
- `run_checks(url: str) -> list[dict]`: realiza poucas requisições passivas à URL informada e devolve uma lista de resultados no mesmo formato de [`contracts/answers.json`](../contracts/answers.json) (com `"origem": "scanner"`).
