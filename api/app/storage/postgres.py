from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.errors import NotFoundError
from app.domain.models import (
    EvalCase,
    EvalSpec,
    EvaluationResult,
    ExperimentRun,
    ExperimentRunStatus,
    JudgeConfig,
)
from app.storage.orm import Base, EvalCaseRow, EvalSpecRow, EvaluationResultRow, ExperimentRunRow


class PostgresEddRepository:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, pool_pre_ping=True)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_schema(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def health_check(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    async def close(self) -> None:
        await self._engine.dispose()

    async def create_eval_spec(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str | None,
        version: str,
        rubric: str,
        pass_threshold: float,
        judge_config: JudgeConfig,
    ) -> EvalSpec:
        now = datetime.now(UTC)
        row = EvalSpecRow(
            eval_spec_id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            version=version,
            rubric=rubric,
            pass_threshold=pass_threshold,
            judge_config=judge_config.model_dump(),
            created_at=now,
            updated_at=now,
        )
        async with self._sessionmaker() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _spec_to_domain(row)

    async def list_eval_specs(self, *, tenant_id: str, limit: int = 100) -> list[EvalSpec]:
        statement = (
            select(EvalSpecRow)
            .where(EvalSpecRow.tenant_id == tenant_id)
            .order_by(EvalSpecRow.created_at.desc())
            .limit(limit)
        )
        async with self._sessionmaker() as session:
            rows = (await session.scalars(statement)).all()
        return [_spec_to_domain(row) for row in rows]

    async def get_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> EvalSpec:
        statement = select(EvalSpecRow).where(
            EvalSpecRow.eval_spec_id == eval_spec_id,
            EvalSpecRow.tenant_id == tenant_id,
        )
        async with self._sessionmaker() as session:
            row = await session.scalar(statement)
        if row is None:
            raise NotFoundError()
        return _spec_to_domain(row)

    async def update_eval_spec(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        updates: dict[str, Any],
    ) -> EvalSpec:
        async with self._sessionmaker() as session:
            row = await session.scalar(
                select(EvalSpecRow).where(
                    EvalSpecRow.eval_spec_id == eval_spec_id,
                    EvalSpecRow.tenant_id == tenant_id,
                )
            )
            if row is None:
                raise NotFoundError()
            for key, value in updates.items():
                if key == "judge_config" and isinstance(value, JudgeConfig):
                    setattr(row, key, value.model_dump())
                else:
                    setattr(row, key, value)
            row.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(row)
            return _spec_to_domain(row)

    async def delete_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> None:
        async with self._sessionmaker() as session:
            row = await session.scalar(
                select(EvalSpecRow).where(
                    EvalSpecRow.eval_spec_id == eval_spec_id,
                    EvalSpecRow.tenant_id == tenant_id,
                )
            )
            if row is None:
                raise NotFoundError()
            cases = (
                await session.scalars(
                    select(EvalCaseRow).where(EvalCaseRow.eval_spec_id == eval_spec_id)
                )
            ).all()
            for case in cases:
                await session.delete(case)
            await session.delete(row)
            await session.commit()

    async def create_eval_case(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        name: str,
        input_payload: dict[str, Any],
        notes: str | None,
        source: str,
        langfuse_trace_id: str | None,
    ) -> EvalCase:
        await self.get_eval_spec(tenant_id=tenant_id, eval_spec_id=eval_spec_id)
        now = datetime.now(UTC)
        row = EvalCaseRow(
            eval_case_id=uuid4(),
            tenant_id=tenant_id,
            eval_spec_id=eval_spec_id,
            name=name,
            input_payload=input_payload,
            notes=notes,
            source=source,
            langfuse_trace_id=langfuse_trace_id,
            created_at=now,
            updated_at=now,
        )
        async with self._sessionmaker() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _case_to_domain(row)

    async def list_eval_cases(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID | None = None,
        limit: int = 100,
    ) -> list[EvalCase]:
        statement = select(EvalCaseRow).where(EvalCaseRow.tenant_id == tenant_id)
        if eval_spec_id is not None:
            statement = statement.where(EvalCaseRow.eval_spec_id == eval_spec_id)
        statement = statement.order_by(EvalCaseRow.created_at.desc()).limit(limit)
        async with self._sessionmaker() as session:
            rows = (await session.scalars(statement)).all()
        return [_case_to_domain(row) for row in rows]

    async def get_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> EvalCase:
        statement = select(EvalCaseRow).where(
            EvalCaseRow.eval_case_id == eval_case_id,
            EvalCaseRow.tenant_id == tenant_id,
        )
        async with self._sessionmaker() as session:
            row = await session.scalar(statement)
        if row is None:
            raise NotFoundError()
        return _case_to_domain(row)

    async def update_eval_case(
        self,
        *,
        tenant_id: str,
        eval_case_id: UUID,
        updates: dict[str, Any],
    ) -> EvalCase:
        async with self._sessionmaker() as session:
            row = await session.scalar(
                select(EvalCaseRow).where(
                    EvalCaseRow.eval_case_id == eval_case_id,
                    EvalCaseRow.tenant_id == tenant_id,
                )
            )
            if row is None:
                raise NotFoundError()
            for key, value in updates.items():
                setattr(row, key, value)
            row.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(row)
            return _case_to_domain(row)

    async def delete_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> None:
        async with self._sessionmaker() as session:
            row = await session.scalar(
                select(EvalCaseRow).where(
                    EvalCaseRow.eval_case_id == eval_case_id,
                    EvalCaseRow.tenant_id == tenant_id,
                )
            )
            if row is None:
                raise NotFoundError()
            await session.delete(row)
            await session.commit()

    async def create_experiment_run(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        candidate_version: str,
        status: str,
        result_count: int,
        completed_at: datetime | None,
    ) -> ExperimentRun:
        now = datetime.now(UTC)
        row = ExperimentRunRow(
            experiment_run_id=uuid4(),
            tenant_id=tenant_id,
            eval_spec_id=eval_spec_id,
            candidate_version=candidate_version,
            status=status,
            result_count=result_count,
            created_at=now,
            updated_at=now,
            completed_at=completed_at,
        )
        async with self._sessionmaker() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _run_to_domain(row)

    async def list_experiment_runs(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID | None = None,
        limit: int = 100,
    ) -> list[ExperimentRun]:
        statement = select(ExperimentRunRow).where(ExperimentRunRow.tenant_id == tenant_id)
        if eval_spec_id is not None:
            statement = statement.where(ExperimentRunRow.eval_spec_id == eval_spec_id)
        statement = statement.order_by(ExperimentRunRow.created_at.desc()).limit(limit)
        async with self._sessionmaker() as session:
            rows = (await session.scalars(statement)).all()
        return [_run_to_domain(row) for row in rows]

    async def get_experiment_run(
        self,
        *,
        tenant_id: str,
        experiment_run_id: UUID,
    ) -> ExperimentRun:
        statement = select(ExperimentRunRow).where(
            ExperimentRunRow.experiment_run_id == experiment_run_id,
            ExperimentRunRow.tenant_id == tenant_id,
        )
        async with self._sessionmaker() as session:
            row = await session.scalar(statement)
        if row is None:
            raise NotFoundError()
        return _run_to_domain(row)

    async def create_evaluation_result(
        self,
        *,
        tenant_id: str,
        experiment_run_id: UUID,
        eval_case_id: UUID,
        candidate_version: str,
        score: float,
        passed: bool,
        scaffold_output: dict[str, Any],
        judge_breakdown: dict[str, Any],
    ) -> EvaluationResult:
        row = EvaluationResultRow(
            evaluation_result_id=uuid4(),
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
            eval_case_id=eval_case_id,
            candidate_version=candidate_version,
            score=score,
            passed=passed,
            scaffold_output=scaffold_output,
            judge_breakdown=judge_breakdown,
            created_at=datetime.now(UTC),
        )
        async with self._sessionmaker() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _result_to_domain(row)

    async def list_evaluation_results(
        self,
        *,
        tenant_id: str,
        experiment_run_id: UUID | None = None,
        limit: int = 100,
    ) -> list[EvaluationResult]:
        statement = select(EvaluationResultRow).where(EvaluationResultRow.tenant_id == tenant_id)
        if experiment_run_id is not None:
            statement = statement.where(
                EvaluationResultRow.experiment_run_id == experiment_run_id
            )
        statement = statement.order_by(EvaluationResultRow.created_at.desc()).limit(limit)
        async with self._sessionmaker() as session:
            rows = (await session.scalars(statement)).all()
        return [_result_to_domain(row) for row in rows]

    async def get_evaluation_result(
        self,
        *,
        tenant_id: str,
        evaluation_result_id: UUID,
    ) -> EvaluationResult:
        statement = select(EvaluationResultRow).where(
            EvaluationResultRow.evaluation_result_id == evaluation_result_id,
            EvaluationResultRow.tenant_id == tenant_id,
        )
        async with self._sessionmaker() as session:
            row = await session.scalar(statement)
        if row is None:
            raise NotFoundError()
        return _result_to_domain(row)


def _spec_to_domain(row: EvalSpecRow) -> EvalSpec:
    return EvalSpec(
        eval_spec_id=row.eval_spec_id,
        tenant_id=row.tenant_id,
        name=row.name,
        description=row.description,
        version=row.version,
        rubric=row.rubric,
        pass_threshold=row.pass_threshold,
        judge_config=JudgeConfig.model_validate(row.judge_config),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _case_to_domain(row: EvalCaseRow) -> EvalCase:
    return EvalCase(
        eval_case_id=row.eval_case_id,
        tenant_id=row.tenant_id,
        eval_spec_id=row.eval_spec_id,
        name=row.name,
        input_payload=row.input_payload,
        notes=row.notes,
        source=row.source,
        langfuse_trace_id=row.langfuse_trace_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _run_to_domain(row: ExperimentRunRow) -> ExperimentRun:
    return ExperimentRun(
        experiment_run_id=row.experiment_run_id,
        tenant_id=row.tenant_id,
        eval_spec_id=row.eval_spec_id,
        candidate_version=row.candidate_version,
        status=ExperimentRunStatus(row.status),
        result_count=row.result_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def _result_to_domain(row: EvaluationResultRow) -> EvaluationResult:
    return EvaluationResult(
        evaluation_result_id=row.evaluation_result_id,
        tenant_id=row.tenant_id,
        experiment_run_id=row.experiment_run_id,
        eval_case_id=row.eval_case_id,
        candidate_version=row.candidate_version,
        score=row.score,
        passed=row.passed,
        scaffold_output=row.scaffold_output,
        judge_breakdown=row.judge_breakdown,
        created_at=row.created_at,
    )
