import csv
from pathlib import Path

from src.models import Customer


class CustomerRepository:
    """Small CSV repository; all customers are fictitious demonstration data."""

    def __init__(self, path: Path):
        self.path = path

    def find_by_cpf(self, cpf: str) -> Customer | None:
        if not self.path.exists():
            raise FileNotFoundError(f"Customer file not found: {self.path}")
        with self.path.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                if row.get("cpf") == cpf:
                    return Customer(**row)
        return None

    def update_score(self, cpf: str, score: int) -> Customer:
        if not self.path.exists():
            raise FileNotFoundError(f"Customer file not found: {self.path}")
        with self.path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
            fields = rows[0].keys() if rows else []
        for row in rows:
            if row.get("cpf") == cpf:
                row["score"] = str(score)
                with self.path.open("w", encoding="utf-8", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                return Customer(**row)
        raise LookupError("Customer not found")
