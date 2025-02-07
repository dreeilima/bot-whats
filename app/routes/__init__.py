"""
Esse código adiciona todos routers para dentro de uma lista para que possa
ser utilizado no main.py
"""
from fastapi import APIRouter
from app.services.utils import LOGGER

from .whatsapp import router as whatsapp_router
from .auth import router as auth_router
from .users import router as user_router
from .finance import router as finance_router

# Lista de routers
routers = [
    whatsapp_router,
    auth_router,
    user_router, 
    finance_router
]

__all__ = ["routers"]
