"""Create experiment_runs and evaluation_results tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260526_0003"
down_revision: str | None = "20260526_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experiment_runs",
        sa.Column("experiment_run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("eval_spec_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_version", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_experiment_runs_tenant_id", "experiment_runs", ["tenant_id"])
    op.create_index("ix_experiment_runs_eval_spec_id", "experiment_runs", ["eval_spec_id"])
    op.create_index("ix_experiment_runs_status", "experiment_runs", ["status"])

    op.create_table(
        "evaluation_results",
        sa.Column("evaluation_result_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("experiment_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("eval_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_version", sa.String(length=128), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("scaffold_output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("judge_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_results_tenant_id", "evaluation_results", ["tenant_id"])
    op.create_index(
        "ix_evaluation_results_experiment_run_id",
        "evaluation_results",
        ["experiment_run_id"],
    )
    op.create_index("ix_evaluation_results_eval_case_id", "evaluation_results", ["eval_case_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_eval_case_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_experiment_run_id", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_tenant_id", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_experiment_runs_status", table_name="experiment_runs")
    op.drop_index("ix_experiment_runs_eval_spec_id", table_name="experiment_runs")
    op.drop_index("ix_experiment_runs_tenant_id", table_name="experiment_runs")
    op.drop_table("experiment_runs")
