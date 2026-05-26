from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.errors import NotFoundError
from app.domain.models import EvalCase, EvalSpec, JudgeConfig


class InMemoryEddRepository:
    def __init__(self) -> None:
        self._specs: dict[UUID, EvalSpec] = {}
        self._cases: dict[UUID, EvalCase] = {}
        self._lock = asyncio.Lock()

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        return None

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
        spec = EvalSpec(
            eval_spec_id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            version=version,
            rubric=rubric,
            pass_threshold=pass_threshold,
            judge_config=judge_config,
            created_at=now,
            updated_at=now,
        )
        async with self._lock:
            self._specs[spec.eval_spec_id] = spec
        return spec

    async def list_eval_specs(self, *, tenant_id: str, limit: int = 100) -> list[EvalSpec]:
        async with self._lock:
            rows = [spec for spec in self._specs.values() if spec.tenant_id == tenant_id]
        rows.sort(key=lambda spec: spec.created_at, reverse=True)
        return rows[:limit]

    async def get_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> EvalSpec:
        async with self._lock:
            spec = self._specs.get(eval_spec_id)
        if spec is None or spec.tenant_id != tenant_id:
            raise NotFoundError()
        return spec

    async def update_eval_spec(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        updates: dict[str, Any],
    ) -> EvalSpec:
        async with self._lock:
            current = self._specs.get(eval_spec_id)
            if current is None or current.tenant_id != tenant_id:
                raise NotFoundError()
            data = current.model_dump()
            data.update(updates)
            data["updated_at"] = datetime.now(UTC)
            updated = EvalSpec.model_validate(data)
            self._specs[eval_spec_id] = updated
        return updated

    async def delete_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> None:
        async with self._lock:
            spec = self._specs.get(eval_spec_id)
            if spec is None or spec.tenant_id != tenant_id:
                raise NotFoundError()
            del self._specs[eval_spec_id]
            case_ids = [
                case_id
                for case_id, case in self._cases.items()
                if case.eval_spec_id == eval_spec_id
            ]
            for case_id in case_ids:
                del self._cases[case_id]

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
        case = EvalCase(
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
        async with self._lock:
            self._cases[case.eval_case_id] = case
        return case

    async def list_eval_cases(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID | None = None,
        limit: int = 100,
    ) -> list[EvalCase]:
        async with self._lock:
            rows = [case for case in self._cases.values() if case.tenant_id == tenant_id]
        if eval_spec_id is not None:
            rows = [case for case in rows if case.eval_spec_id == eval_spec_id]
        rows.sort(key=lambda case: case.created_at, reverse=True)
        return rows[:limit]

    async def get_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> EvalCase:
        async with self._lock:
            case = self._cases.get(eval_case_id)
        if case is None or case.tenant_id != tenant_id:
            raise NotFoundError()
        return case

    async def update_eval_case(
        self,
        *,
        tenant_id: str,
        eval_case_id: UUID,
        updates: dict[str, Any],
    ) -> EvalCase:
        async with self._lock:
            current = self._cases.get(eval_case_id)
            if current is None or current.tenant_id != tenant_id:
                raise NotFoundError()
            data = current.model_dump()
            data.update(updates)
            data["updated_at"] = datetime.now(UTC)
            updated = EvalCase.model_validate(data)
            self._cases[eval_case_id] = updated
        return updated

    async def delete_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> None:
        async with self._lock:
            case = self._cases.get(eval_case_id)
            if case is None or case.tenant_id != tenant_id:
                raise NotFoundError()
            del self._cases[eval_case_id]
