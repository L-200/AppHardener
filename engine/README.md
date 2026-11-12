# Módulo `engine/` (Responsável: P2)

Checklist de segurança em YAML e motor de avaliação de severidade e prioridade.

## Interface esperada (Fase 1 / Fase 2)
- `load_checklist() -> list[dict]`: lê o arquivo YAML do checklist e devolve uma lista de dicionários seguindo o formato de [`contracts/checklist.json`](../contracts/checklist.json).
- `evaluate(answers: list[dict]) -> list[dict]`: recebe uma lista de respostas no formato de [`contracts/answers.json`](../contracts/answers.json) e devolve os achados gerados no formato de [`contracts/findings.json`](../contracts/findings.json).
