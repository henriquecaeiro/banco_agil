from decimal import Decimal

from pydantic import BaseModel, Field


class Customer(BaseModel):
    cpf: str
    nome: str
    data_nascimento: str
    score: int = Field(ge=0, le=1000)
    limite_credito: Decimal = Field(ge=0)
