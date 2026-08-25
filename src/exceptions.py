class CreditRequestPersistenceError(Exception):
    """Raised when a credit request cannot be persisted to storage."""

    def __init__(self, message: str = "Credit request persistence failed") -> None:
        super().__init__(message)
