from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CreditRequest(BaseModel):
    cpf_cliente: str
    data_hora_solicitacao: datetime
    limite_atual: Decimal = Field(ge=0)
    novo_limite_solicitado: Decimal = Field(gt=0)
    status_pedido: Literal["pendente", "aprovado", "rejeitado"]
