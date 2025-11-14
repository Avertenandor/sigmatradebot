"""
Middlewares.

Bot middlewares for request processing.
"""

from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.request_id import RequestIDMiddleware

__all__ = [
    "AuthMiddleware",
    "DatabaseMiddleware",
    "RequestIDMiddleware",
]
