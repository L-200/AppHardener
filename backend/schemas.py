"""Schemas Pydantic para validação de entrada e serialização conforme contracts/."""

from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

SeverityLevel = Literal["critica", "alta", "media", "baixa"]
FindingStatus = Literal["aberto", "em_correcao", "corrigido"]
AnswerValue = Literal["ok", "falha", "nao_se_aplica", "nao_verificado"]
AnswerOrigin = Literal["manual", "scanner"]

STATUS_ALIASES: dict[str, FindingStatus] = {
    "aberto": "aberto",
    "em_correcao": "em_correcao",
    "em correção": "em_correcao",
    "em correcao": "em_correcao",
    "corrigido": "corrigido",
}

SEVERITY_DEFAULT_PRIORITY: dict[str, int] = {
    "critica": 1,
    "alta": 2,
    "media": 3,
    "baixa": 4,
}

PRIORITY_ALIASES: dict[str, int] = {
    "critica": 1,
    "alta": 1,
    "media": 2,
    "baixa": 3,
}


def _strip_text(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_url(value: Any) -> str:
    if isinstance(value, str):
        raw = value.strip()
    else:
        raw = str(value)
    validated = str(AnyHttpUrl(raw))
    if not raw.endswith("/") and validated.endswith("/"):
        return validated[:-1]
    return validated


def _normalize_status(value: Any) -> Any:
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return STATUS_ALIASES.get(cleaned, cleaned)
    return value


class ApplicationCreate(BaseModel):
    """Payload de criação de aplicação."""

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=2, max_length=120)
    url: str = Field(..., min_length=4, max_length=500)
    descricao: str = Field(default="", max_length=1000)
    stack: str = Field(default="", max_length=200)

    @field_validator("nome", "descricao", "stack", mode="before")
    @classmethod
    def strip_strings(cls, value: Any) -> Any:
        return _strip_text(value)

    @field_validator("url", mode="before")
    @classmethod
    def validate_http_url(cls, value: Any) -> str:
        return _normalize_url(value)


class ApplicationUpdate(BaseModel):
    """Payload de atualização parcial de aplicação."""

    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    url: str | None = Field(default=None, min_length=4, max_length=500)
    descricao: str | None = Field(default=None, max_length=1000)
    stack: str | None = Field(default=None, max_length=200)

    @field_validator("nome", "descricao", "stack", mode="before")
    @classmethod
    def strip_strings(cls, value: Any) -> Any:
        return _strip_text(value)

    @field_validator("url", mode="before")
    @classmethod
    def validate_http_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_url(value)


class ApplicationOut(BaseModel):
    """Representação de aplicação conforme contracts/applications.json."""

    id: int
    nome: str
    url: str
    descricao: str
    stack: str
    criada_em: str


class FindingCreate(BaseModel):
    """Payload para registro de um achado de segurança."""

    model_config = ConfigDict(extra="ignore")

    item_id: str | None = Field(default=None, max_length=50)
    titulo: str = Field(..., min_length=3, max_length=200)
    descricao: str = Field(default="", max_length=2000)
    severidade: SeverityLevel
    prioridade: int | None = Field(default=None, ge=1, le=10)
    status: FindingStatus = Field(default="aberto")
    recomendacao: str = Field(..., min_length=3, max_length=2000)

    @field_validator("item_id", "titulo", "descricao", "recomendacao", mode="before")
    @classmethod
    def strip_strings(cls, value: Any) -> Any:
        return _strip_text(value)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> Any:
        return _normalize_status(value)

    @field_validator("prioridade", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if cleaned in PRIORITY_ALIASES:
                return PRIORITY_ALIASES[cleaned]
            if cleaned.isdigit():
                return int(cleaned)
        return value

    @model_validator(mode="after")
    def set_default_priority(self) -> "FindingCreate":
        if self.prioridade is None:
            self.prioridade = SEVERITY_DEFAULT_PRIORITY.get(self.severidade, 3)
        return self


class FindingStatusUpdate(BaseModel):
    """Payload para atualização de status de um achado."""

    model_config = ConfigDict(extra="forbid")

    status: FindingStatus

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> Any:
        return _normalize_status(value)


class FindingOut(BaseModel):
    """Representação de achado conforme contracts/findings.json."""

    id: int
    app_id: int
    item_id: str | None = None
    titulo: str
    descricao: str
    severidade: SeverityLevel
    prioridade: int
    status: FindingStatus
    recomendacao: str


class FindingHistoryOut(BaseModel):
    """Registro de histórico de mudança de status de um achado."""

    id: int
    finding_id: int
    status_anterior: FindingStatus | None = None
    status_novo: FindingStatus
    alterado_em: str


class AnswerIn(BaseModel):
    """Payload de resposta de item do checklist conforme contracts/answers.json."""

    model_config = ConfigDict(extra="ignore")

    app_id: int | None = None
    item_id: str = Field(..., min_length=2, max_length=50)
    resposta: AnswerValue
    origem: AnswerOrigin = Field(default="manual")
    evidencia: str = Field(default="", max_length=2000)

    @field_validator("item_id", "evidencia", mode="before")
    @classmethod
    def strip_strings(cls, value: Any) -> Any:
        return _strip_text(value)


class AnswerOut(BaseModel):
    # Representação de resposta conforme contracts/answers.json

    app_id: int
    item_id: str
    resposta: AnswerValue
    origem: AnswerOrigin
    evidencia: str


class CategorySummaryCount(BaseModel):
    # Contagem de respostas por categoria

    ok: int = 0
    falha: int = 0
    nao_se_aplica: int = 0
    nao_verificado: int = 0


class AppSummaryOut(BaseModel):
    # Resumo consolidado da postura de segurança conforme contracts/summary.json

    app_id: int
    percentual_atendido: float
    total_itens_avaliados: int
    total_achados: int
    por_severidade: dict[SeverityLevel, int]
    por_status: dict[FindingStatus, int]
    por_categoria: dict[str, CategorySummaryCount]
