from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domain.models import EvalCase, EvalSpec, JudgeConfig


class EddRepository(Protocol):
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...

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
    ) -> EvalSpec: ...

    async def list_eval_specs(self, *, tenant_id: str, limit: int = 100) -> list[EvalSpec]: ...

    async def get_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> EvalSpec: ...

    async def update_eval_spec(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        updates: dict[str, Any],
    ) -> EvalSpec: ...

    async def delete_eval_spec(self, *, tenant_id: str, eval_spec_id: UUID) -> None: ...

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
    ) -> EvalCase: ...

    async def list_eval_cases(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID | None = None,
        limit: int = 100,
    ) -> list[EvalCase]: ...

    async def get_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> EvalCase: ...

    async def update_eval_case(
        self,
        *,
        tenant_id: str,
        eval_case_id: UUID,
        updates: dict[str, Any],
    ) -> EvalCase: ...

    async def delete_eval_case(self, *, tenant_id: str, eval_case_id: UUID) -> None: ...
