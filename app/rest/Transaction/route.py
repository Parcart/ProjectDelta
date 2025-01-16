from typing import Annotated

from fastapi import Depends

from app.db.DAO import DAO
from app.db.schema.Base import TransactionType
from app.jwt_auth.auth_jwt import get_current_active_user
from app.rest.CustomAPIRouter import APIRouter
from app.rest.Transaction.entity import TransactionResponse, TransactionsResponse, CreateTransactionRequest

from app.rest.User.entity import User as UserModel


class Transaction:
    """
    Пополнение баланса и получения списка транзакций
    """

    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["Transaction"])
        self.route.add_api_route("/add_transaction", self.add_transaction, methods=["POST"])
        self.route.add_api_route("/transactions", self.read_transactions, methods=["GET"])

    @staticmethod
    async def add_transaction(current_user: Annotated[UserModel, Depends(get_current_active_user)],
                              transaction_request: CreateTransactionRequest):
        await DAO().Transaction.post(current_user.id, transaction_request.amount, transaction_request.description, transaction_type=TransactionType.DEBIT)
        return 200

    @staticmethod
    async def read_transactions(current_user: Annotated[UserModel, Depends(get_current_active_user)]):
        transactions = await DAO().Transaction.get(current_user.id)
        response = [TransactionResponse(**transaction.__dict__) for transaction in transactions]
        return TransactionsResponse(transactions=response)
