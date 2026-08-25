import csv
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.models import CreditRequest, Customer
from src.repositories import CreditRequestRepository


class CreditService:
    def __init__(self, score_limits_path: Path, request_repository: CreditRequestRepository):
        self.score_limits_path = score_limits_path
        self.request_repository = request_repository

    def current_limit(self, customer: Customer) -> Decimal:
        return customer.limite_credito

    def maximum_limit(self, score: int) -> Decimal:
        if not self.score_limits_path.exists():
            raise FileNotFoundError(f"Score limits file not found: {self.score_limits_path}")
        with self.score_limits_path.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                if int(row["score_min"]) <= score <= int(row["score_max"]):
                    return Decimal(row["limite_maximo"])
        raise ValueError("No score range found for customer")

    def request_increase(self, customer: Customer, requested_limit: str) -> CreditRequest:
        try:
            value = Decimal(requested_limit.replace(",", ".").replace("R$", "").strip())
        except (InvalidOperation, AttributeError) as error:
            raise ValueError("Informe um valor monetário válido.") from error
        if value <= 0:
            raise ValueError("O novo limite deve ser maior que zero.")
        status = "aprovado" if value <= self.maximum_limit(customer.score) else "rejeitado"
        request = CreditRequest(
            cpf_cliente=customer.cpf,
            data_hora_solicitacao=datetime.now(UTC),
            limite_atual=customer.limite_credito,
            novo_limite_solicitado=value,
            status_pedido=status,
        )
        self.request_repository.save(request)
        return request
