"""
Esse código adiciona todos routers para dentro de uma lista para que possa
ser utilizado no main.py
"""
from fastapi import APIRouter
from app.services.utils import LOGGER

from .users import router as user_router
from .auth import router as auth_router
from .finance import router as finance_router
from .whatsapp import router as whatsapp_router

# Define a lista de routers diretamente
routers = [
    user_router,
    auth_router,
    finance_router,
    whatsapp_router
]

__all__ = [
    "user_router",
    "auth_router", 
    "finance_router",
    "whatsapp_router"
]
