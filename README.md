# AppHardener

Ferramenta local voltada ao diagnóstico de segurança e ao fortalecimento gradual (*hardening*) de aplicações web — **Projeto Integrador (Trilha 1) • ICC330**.

> **Aviso de uso ético**: O AppHardener e seu módulo de verificação passiva devem ser utilizados exclusivamente em sistemas próprios, locais ou para os quais haja autorização explícita de teste.

---

## 1. Estrutura do Repositório e Divisão por Módulo

Cada integrante é responsável por sua própria pasta e se acopla aos demais através do contrato de dados em [`contracts/`](./contracts/README.md):

```text
AppHardener/
├── contracts/       # Contrato de integração e fixtures JSON (P1 conduz / Todos usam)
├── backend/         # API FastAPI, banco SQLite, validação Pydantic e modelos (P1)
├── engine/          # Checklist YAML, mapeamento OWASP/CWE e cálculo de severidade (P2)
├── frontend/        # Interface web HTML/CSS/JS puro, gráficos e relatório imprimível (P3)
├── scanner/         # Verificações passivas de headers, cookies e caminhos expostos (P4)
├── demo-app/        # Aplicação-alvo vulnerável/endurecida para demonstração (P4)
└── .github/         # Pipeline CI com Semgrep/SCA, gitleaks e pytest (P4)
```

---

## 2. Regras de Trabalho da Equipe

1. **Isolamento de pastas**: durante a Fase 1, nenhum módulo edita a pasta do outro.
2. **Contrato primeiro**: qualquer alteração nos campos de JSON deve ser combinada e refletida primeiro em [`contracts/`](./contracts/README.md).
3. **Fluxo Git**: trabalhar em branch próprio por pessoa/tarefa e abrir PRs curtos.
4. **Segurança do repositório**: nunca commitar segredos, tokens ou arquivos `.db`/`.env` (usar `pre-commit` com `gitleaks`).

---

## 3. Configuração do Ambiente Local

Requisitos: **Python 3.12+**

```bash
# 1. Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Ativar hooks de pre-commit (gitleaks + validações de YAML/JSON)
pre-commit install
```

Para executar a API localmente (apenas em `127.0.0.1`):

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
