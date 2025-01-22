from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends

from app.rest.CustomAPIRouter import APIRouter
from .entity import UsersResponse, UserDetailsResponse
from ..Transaction.entity import TransactionResponse
from ...db.DAO import DAO
from ...db.schema.Entity import User as UserBase
from ...jwt_auth.auth_jwt import get_admin_user


class Admin:

    def __init__(self):
        self.route = APIRouter(prefix="/admin", tags=["Admin"])
        self.route.add_api_route("/users", self.get_all_users, methods=["GET"])
        self.route.add_api_route("/users/{user_id}", self.get_user_profile, methods=["GET"])
        self.route.add_api_route("/add_transaction", self.create_transaction, methods=["POST"])
        self.route.add_api_route("/transactions", self.read_transactions, methods=["GET"])

    @staticmethod
    async def get_all_users(current_user: Annotated[UserBase, Depends(get_admin_user)]):
        users = await DAO().Admin.get_all_users()
        response = {
            "users": []
        }

        for user in users:
            response["users"].append(
                UsersResponse(id=user.id, email=user.email, created_at=user.created_at, name=user.profile.name,
                              balance=user.balance.voice_seconds, role=user.role)
            )

        return response

    @staticmethod
    async def get_user_profile(current_user: Annotated[UserBase, Depends(get_admin_user)],
                               user_id: str):
        user = await DAO().User.get(user_id=user_id)
        user = UsersResponse(id=user.id, email=user.email, created_at=user.created_at, name=user.profile.name,
                             balance=user.balance.voice_seconds, role=user.role)
        transactions = await DAO().Transaction.get(current_user.id)
        response = [TransactionResponse(**transaction.__dict__) for transaction in transactions]
        if user:
            return UserDetailsResponse(**user.model_dump(), transactions=response)

        raise HTTPException(status_code=404, detail="User not found")

    @staticmethod
    async def create_transaction(current_user: Annotated[UserBase, Depends(get_admin_user)],
                                 transaction_request: TransactionResponse):
        await DAO().Transaction.post(current_user.id, transaction_request.amount, transaction_request.description,
                                     transaction_type=transaction_request.transaction_type)
        return 200

    @staticmethod
    async def read_transactions(current_user: Annotated[UserBase, Depends(get_admin_user)]):
        transactions = await DAO().Admin.get_transactions()
        response = [TransactionResponse(**transaction.__dict__) for transaction in transactions]
        return response
