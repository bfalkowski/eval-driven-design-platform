"""Create eval_specs and eval_cases tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260526_0002"
down_revision: str | None = "20260526_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_specs",
        sa.Column("eval_spec_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("rubric", sa.Text(), nullable=False),
        sa.Column("pass_threshold", sa.Float(), nullable=False),
        sa.Column("judge_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_specs_tenant_id", "eval_specs", ["tenant_id"])

    op.create_table(
        "eval_cases",
        sa.Column("eval_case_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("eval_spec_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("langfuse_trace_id", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_cases_tenant_id", "eval_cases", ["tenant_id"])
    op.create_index("ix_eval_cases_eval_spec_id", "eval_cases", ["eval_spec_id"])


def downgrade() -> None:
    op.drop_index("ix_eval_cases_eval_spec_id", table_name="eval_cases")
    op.drop_index("ix_eval_cases_tenant_id", table_name="eval_cases")
    op.drop_table("eval_cases")
    op.drop_index("ix_eval_specs_tenant_id", table_name="eval_specs")
    op.drop_table("eval_specs")
