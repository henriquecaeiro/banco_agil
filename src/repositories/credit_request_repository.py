import csv
import logging
import time
from collections.abc import Callable
from pathlib import Path

from src.exceptions import CreditRequestPersistenceError
from src.models import CreditRequest

logger = logging.getLogger(__name__)

PERSISTENCE_RETRY_ATTEMPTS = 3
PERSISTENCE_RETRY_DELAY_SECONDS = 0.1


class CreditRequestRepository:
    def __init__(
        self,
        path: Path,
        *,
        retry_attempts: int = PERSISTENCE_RETRY_ATTEMPTS,
        retry_delay_seconds: float = PERSISTENCE_RETRY_DELAY_SECONDS,
    ):
        self.path = path
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds

    def save(self, request: CreditRequest) -> None:
        self._persist_with_retry(
            lambda: self._append_request(request),
            operation_name="save credit request",
        )

    def update_status(self, request: CreditRequest) -> None:
        self._persist_with_retry(
            lambda: self._rewrite_status(request),
            operation_name="update credit request status",
        )

    def _persist_with_retry(self, write_operation: Callable[[], None], *, operation_name: str) -> None:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                write_operation()
                return
            except PermissionError as error:
                last_error = error
                logger.warning(
                    "Failed to %s because the destination file is unavailable "
                    "(attempt %s/%s): %s",
                    operation_name,
                    attempt,
                    self.retry_attempts,
                    self.path,
                    exc_info=attempt == self.retry_attempts,
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)
            except FileNotFoundError as error:
                logger.exception(
                    "Failed to persist credit request because the destination file was not found: %s",
                    self.path,
                )
                raise CreditRequestPersistenceError(
                    "Credit request file is unavailable."
                ) from error
            except OSError as error:
                logger.exception(
                    "Failed to persist credit request due to an I/O error on %s",
                    self.path,
                )
                raise CreditRequestPersistenceError(
                    "Credit request file is unavailable."
                ) from error

        raise CreditRequestPersistenceError(
            "Credit request file is temporarily unavailable."
        ) from last_error

    def _append_request(self, request: CreditRequest) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Credit request file not found: {self.path}")
        with self.path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CreditRequest.model_fields.keys())
            if file.tell() == 0:
                writer.writeheader()
            row = request.model_dump(mode="json")
            writer.writerow(row)

    def _rewrite_status(self, request: CreditRequest) -> None:
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
