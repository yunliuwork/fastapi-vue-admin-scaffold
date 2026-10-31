from fastapi import APIRouter

from app.api.v1 import auth, health, logs, menus, roles, scheduled_jobs, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(menus.router)
api_router.include_router(logs.router)
api_router.include_router(scheduled_jobs.router)
