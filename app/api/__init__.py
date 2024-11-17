# This file marks the api directory as a Python package
# It can be used to export specific items from the package

from app.api.authentication import router as auth_router
from app.api.subscription import router as subscription_router
from app.api.repository_review import router as review_router
from app.api.email_communication import router as email_router

__all__ = [
    "auth_router",
    "subscription_router",
    "review_router",
    "email_router"
]
