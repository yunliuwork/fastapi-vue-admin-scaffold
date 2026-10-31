from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import Settings
from app.core.audit import RequestAuditMiddleware
from app.core.errors import AppError
from app.db.base import Base
from app.db.session import init_engine
from app.db.schema import ensure_operation_log_columns, ensure_table_prefixes, ensure_user_columns
from app.db import session as db_session
from app.models import Menu, OperationLog, Role, ScheduledJob, ScheduledJobLog, User  # noqa: F401
from app.scheduler.runner import start_scheduler, stop_scheduler
from app.services.seed import ensure_operation_log_menu, ensure_scheduled_task_menu, seed_if_empty


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        engine = init_engine(settings.database_url)
        ensure_table_prefixes(engine)
        if settings.auto_create_tables:
            Base.metadata.create_all(bind=engine)
        ensure_user_columns(engine)
        ensure_operation_log_columns(engine)
        if settings.seed_on_startup:
            db = db_session.session_factory()
            try:
                seed_if_empty(db)
                ensure_operation_log_menu(db)
                ensure_scheduled_task_menu(db)
            finally:
                db.close()
        scheduler = start_scheduler(settings)
        try:
            yield
        finally:
            stop_scheduler(scheduler)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestAuditMiddleware)

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        message = "参数错误"
        errors = exc.errors()
        if errors:
            message = str(errors[0].get("msg", message)).removeprefix("Value error, ")
        return JSONResponse(status_code=422, content={"code": 422, "message": message, "data": None})

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
