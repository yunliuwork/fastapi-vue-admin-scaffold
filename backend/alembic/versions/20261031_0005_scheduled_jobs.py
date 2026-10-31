"""scheduled jobs"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0005"
down_revision: str | None = "20261031_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("job_key", sa.String(length=64), nullable=False),
        sa.Column("trigger_type", sa.String(length=16), nullable=False),
        sa.Column("trigger_config", sa.String(length=255), nullable=False, server_default="{}"),
        sa.Column("params", sa.String(length=512), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("builtin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remark", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scheduled_jobs_job_key", "scheduled_jobs", ["job_key"], unique=True)
    op.create_table(
        "scheduled_job_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("scheduled_jobs.id"), nullable=False),
        sa.Column("job_name", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("trigger_mode", sa.String(length=16), nullable=False, server_default="scheduled"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scheduled_job_logs_job_id", "scheduled_job_logs", ["job_id"])
    op.create_index("ix_scheduled_job_logs_started_at", "scheduled_job_logs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_scheduled_job_logs_started_at", table_name="scheduled_job_logs")
    op.drop_index("ix_scheduled_job_logs_job_id", table_name="scheduled_job_logs")
    op.drop_table("scheduled_job_logs")
    op.drop_index("ix_scheduled_jobs_job_key", table_name="scheduled_jobs")
    op.drop_table("scheduled_jobs")
