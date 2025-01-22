from datetime import datetime

from pydantic import BaseModel

from app.db.schema.Base import Role
from app.rest.Transaction.entity import TransactionsResponse


class UsersResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    name: str
    balance: int
    role: Role


class UserDetailsResponse(UsersResponse, TransactionsResponse):
    pass

class AdminTransactionRequest(BaseModel):
    user_id: str
