# Contrato de Integração (`contracts/`)

Esta pasta contém os **fixtures JSON** que servem como contrato oficial de dados entre os 4 módulos do **AppHardener** (`backend/`, `engine/`, `frontend/` e `scanner/`).

Durante a **Fase 1**, cada integrante desenvolve e testa seu módulo de forma isolada consumindo ou produzindo dados exatamente neste formato.

---

## 1. Entidades e Arquivos de Exemplo

| Entidade | Arquivo de Fixture | Campos principais |
| :--- | :--- | :--- |
| **Application** | [`applications.json`](./applications.json) | `id`, `nome`, `url`, `descricao`, `stack`, `criada_em` |
| **ChecklistItem** | [`checklist.json`](./checklist.json) | `id`, `categoria`, `pergunta`, `referencia`, `severidade_base`, `recomendacao` |
| **Answer** | [`answers.json`](./answers.json) | `app_id`, `item_id`, `resposta`, `origem`, `evidencia` |
| **Finding** | [`findings.json`](./findings.json) | `id`, `app_id`, `item_id`, `titulo`, `descricao`, `severidade`, `prioridade`, `status`, `recomendacao` |
| **Summary** | [`summary.json`](./summary.json) | `app_id`, `percentual_atendido`, `total_itens_avaliados`, `total_achados`, `por_severidade`, `por_status`, `por_categoria` |

---

## 2. Valores Padronizados (Enums)

- **`severidade` / `severidade_base`**: `"critica"` | `"alta"` | `"media"` | `"baixa"`
- **`resposta` (`Answer`)**: `"ok"` | `"falha"` | `"nao_se_aplica"` | `"nao_verificado"`
- **`origem` (`Answer`)**: `"manual"` | `"scanner"`
- **`status` (`Finding`)**: `"aberto"` | `"em_correcao"` | `"corrigido"`

---

## 3. Endpoints da API (Fase 2)

| Método e Rota | Função | Responsável |
| :--- | :--- | :--- |
| `GET /api/apps` | Listar aplicações cadastradas | P1 |
| `POST /api/apps` | Cadastrar nova aplicação | P1 |
| `GET /api/checklist` | Retornar itens do checklist (via `engine.load_checklist()`) | P2 |
| `PUT /api/apps/{id}/answers` | Salvar respostas e gerar achados (via `engine.evaluate(answers)`) | P1 + P2 |
| `GET /api/apps/{id}/findings` | Listar achados da aplicação (com filtros opcionais) | P1 |
| `PATCH /api/apps/{id}/findings/{finding_id}` | Atualizar status de um achado (`aberto`, `em_correcao`, `corrigido`) | P1 |
| `POST /api/apps/{id}/scan` | Rodar verificações passivas na URL (via `scanner.run_checks(url)`) | P4 |
| `GET /api/apps/{id}/summary` | Dados consolidados do painel e do relatório | P1 |

---

## 4. Interfaces Python Internas

- **P2 (`engine/`)**:
  - `load_checklist() -> list[dict]`: carrega o YAML e retorna lista de `ChecklistItem`.
  - `evaluate(answers: list[dict]) -> list[dict]`: recebe lista de `Answer` e devolve lista de `Finding` com severidade, prioridade e recomendação.
- **P4 (`scanner/`)**:
  - `run_checks(url: str) -> list[dict]`: executa verificações passivas na URL e devolve resultados no formato de `Answer` (`origem: "scanner"`).
