from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import now_ms
from app.db.base import Base


class ScheduledJob(Base):
    __tablename__ = "sys_scheduled_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    job_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    trigger_type: Mapped[str] = mapped_column(String(16))
    trigger_config: Mapped[str] = mapped_column(String(255), default="{}")
    params: Mapped[str] = mapped_column(String(512), default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    remark: Mapped[str] = mapped_column(String(255), default="")
    last_run_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_status: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    updated_at: Mapped[int] = mapped_column(BigInteger, default=now_ms, onupdate=now_ms)

    logs: Mapped[list["ScheduledJobLog"]] = relationship(back_populates="job")


class ScheduledJobLog(Base):
    __tablename__ = "sys_scheduled_job_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("sys_scheduled_jobs.id"), index=True)
    job_name: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text, default="")
    trigger_mode: Mapped[str] = mapped_column(String(16), default="scheduled")
    started_at: Mapped[int] = mapped_column(BigInteger, default=now_ms, index=True)
    finished_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    job: Mapped[ScheduledJob] = relationship(back_populates="logs")
