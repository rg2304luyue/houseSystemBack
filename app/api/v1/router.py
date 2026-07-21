"""Aggregate all v1 API routers under /api/v1 prefix."""
from fastapi import APIRouter
from app.api.v1 import auth, appointments, chat_ai, comments, contracts, houses, messages, payments, rentals, users

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router, tags=["auth"])
api_v1_router.include_router(appointments.router, tags=["appointments"])
api_v1_router.include_router(chat_ai.router, tags=["chat-ai"])
api_v1_router.include_router(comments.router, tags=["comments"])
api_v1_router.include_router(contracts.router, tags=["contracts"])
api_v1_router.include_router(houses.router, tags=["houses"])
api_v1_router.include_router(messages.router, tags=["messages"])
api_v1_router.include_router(payments.router, tags=["payments"])
api_v1_router.include_router(rentals.router, tags=["rentals"])
api_v1_router.include_router(users.router, tags=["users"])
