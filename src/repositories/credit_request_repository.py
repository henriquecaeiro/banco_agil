import csv
from pathlib import Path

from src.models import CreditRequest


class CreditRequestRepository:
    def __init__(self, path: Path):
        self.path = path

    def save(self, request: CreditRequest) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Credit request file not found: {self.path}")
        with self.path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CreditRequest.model_fields.keys())
            if file.tell() == 0:
                writer.writeheader()
            row = request.model_dump(mode="json")
            writer.writerow(row)

    def update_status(self, request: CreditRequest) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Credit request file not found: {self.path}")
        with self.path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        timestamp = request.model_dump(mode="json")["data_hora_solicitacao"]
        updated = False
        for row in rows:
            if (
                row.get("cpf_cliente") == request.cpf_cliente
                and row.get("data_hora_solicitacao") == timestamp
            ):
                row["status_pedido"] = request.status_pedido
                updated = True
                break
        if not updated:
            raise LookupError("Credit request not found")

        with self.path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CreditRequest.model_fields.keys())
            writer.writeheader()
            writer.writerows(rows)
