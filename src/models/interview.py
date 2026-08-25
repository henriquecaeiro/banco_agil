from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CreditInterview(BaseModel):
    renda_mensal: Decimal = Field(ge=0)
    tipo_emprego: Literal["formal", "autônomo", "desempregado"]
    despesas_fixas_mensais: Decimal = Field(ge=0)
    numero_dependentes: int = Field(ge=0)
    tem_dividas: bool
