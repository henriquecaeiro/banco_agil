from src.models import CreditInterview, Customer
from src.repositories import CustomerRepository
from src.tools.score import calculate_score


class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def apply_interview(self, cpf: str, interview: CreditInterview) -> Customer:
        return self.customer_repository.update_score(cpf, calculate_score(interview))
