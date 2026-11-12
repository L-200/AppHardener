"""Módulo engine (P2): carregamento do checklist YAML e motor de avaliação de achados."""


def load_checklist() -> list[dict]:
    """Carrega os itens do checklist a partir do YAML e retorna no formato ChecklistItem do contrato."""
    raise NotImplementedError("A ser implementado por P2 na Fase 1")


def evaluate(answers: list[dict]) -> list[dict]:
    """Recebe lista de respostas (Answer) e retorna achados (Finding) com severidade e prioridade."""
    raise NotImplementedError("A ser implementado por P2 na Fase 1")
