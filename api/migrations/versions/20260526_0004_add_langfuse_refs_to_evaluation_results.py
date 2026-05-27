"""Add Langfuse reference columns to evaluation_results."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260526_0004"
down_revision: str | None = "20260526_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluation_results",
        sa.Column("langfuse_trace_id", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "evaluation_results",
        sa.Column("langfuse_score_id", sa.String(length=256), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_results", "langfuse_score_id")
    op.drop_column("evaluation_results", "langfuse_trace_id")
