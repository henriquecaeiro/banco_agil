class CreditRequestPersistenceError(Exception):
    """Raised when a credit request cannot be persisted to storage."""

    def __init__(self, message: str = "Credit request persistence failed") -> None:
        super().__init__(message)


class CreditAnalysisError(Exception):
    """Raised when a credit request cannot be analyzed with the available score data."""

    def __init__(self, message: str = "Credit request analysis failed") -> None:
        super().__init__(message)
