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
