"""operation log params, response, and status"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0004"
down_revision: str | None = "20261031_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("operation_logs", sa.Column("params", sa.Text(), nullable=False, server_default=""))
    op.add_column("operation_logs", sa.Column("response_body", sa.Text(), nullable=False, server_default=""))
    op.add_column("operation_logs", sa.Column("status_code", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("operation_logs", "status_code")
    op.drop_column("operation_logs", "response_body")
    op.drop_column("operation_logs", "params")
