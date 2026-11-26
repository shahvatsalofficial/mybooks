from __future__ import annotations

import asyncio
from typing import Callable, Awaitable, List, Optional
from pydantic import BaseModel, Field


class RepairAttemptRecord(BaseModel):
    attempt: int
    sql: str
    error: Optional[str] = None
    hint_category: Optional[str] = None


class SqlRepairOutcome(BaseModel):
    succeeded: bool
    final_sql: str
    attempts_used: int
    history: List[RepairAttemptRecord] = Field(default_factory=list)


class BoundedSqlRepairLoop:
    """Executes bounded SQL synthesis -> AST check -> execute -> reflect retries."""

    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self.ast_validator = DeterministicSqlAstValidator(max_limit=500)
        self.classifier = SqlErrorClassifier()

    async def run(
        self,
        initial_sql: str,
        execute_fn: Callable[[str], Awaitable[List[dict]]],
        repair_fn: Callable[[str, ErrorReflectionHint], Awaitable[str]],
    ) -> SqlRepairOutcome:
        current_sql = initial_sql
        history: List[RepairAttemptRecord] = []

        for attempt in range(1, self.max_attempts + 1):
            ast_res = self.ast_validator.validate(current_sql)
            if not ast_res.is_valid:
                err_msg = "; ".join(ast_res.violations)
                hint = ErrorReflectionHint(
                    category=SqlErrorCategory.SYNTAX_ERROR,
                    offending_symbol="AST",
                    repair_instruction=f"AST policy rejected SQL: {err_msg}",
                )
                history.append(
                    RepairAttemptRecord(
                        attempt=attempt, sql=current_sql, error=err_msg, hint_category=hint.category.value
                    )
                )
                if attempt < self.max_attempts:
                    current_sql = await repair_fn(current_sql, hint)
                continue

            try:
                _rows = await execute_fn(ast_res.normalized_sql)
                history.append(RepairAttemptRecord(attempt=attempt, sql=ast_res.normalized_sql))
                return SqlRepairOutcome(
                    succeeded=True,
                    final_sql=ast_res.normalized_sql,
                    attempts_used=attempt,
                    history=history,
                )
            except Exception as exc:
                err_str = str(exc)
                hint = self.classifier.classify(err_str)
                history.append(
                    RepairAttemptRecord(
                        attempt=attempt,
                        sql=ast_res.normalized_sql,
                        error=err_str,
                        hint_category=hint.category.value,
                    )
                )
                if attempt < self.max_attempts:
                    current_sql = await repair_fn(ast_res.normalized_sql, hint)

        return SqlRepairOutcome(
            succeeded=False,
            final_sql=current_sql,
            attempts_used=self.max_attempts,
            history=history,
        )


async def demo_repair_loop() -> None:
    attempt_counter = {"n": 0}

    async def mock_execute(sql: str) -> List[dict]:
        attempt_counter["n"] += 1
        if "s.cat_id" in sql:
            raise RuntimeError('ERROR: column "s.cat_id" does not exist')
        return [{"category_name": "Retail", "failed_cnt": 142}]

    async def mock_repair(sql: str, hint: ErrorReflectionHint) -> str:
        await asyncio.sleep(0.01)
        return sql.replace("s.cat_id", "m.category_id")

    loop = BoundedSqlRepairLoop(max_attempts=3)
    broken_sql = (
        "SELECT mc.category_name, COUNT(*) AS failed_cnt "
        "FROM analytics.settlement_events s "
        "JOIN analytics.merchants m ON s.merchant_id = m.id "
        "JOIN analytics.merchant_categories mc ON s.cat_id = mc.id "
        "WHERE s.settled_date >= '2026-08-01' AND s.status = 'failed' "
        "GROUP BY mc.category_name"
    )
    outcome = await loop.run(broken_sql, mock_execute, mock_repair)
    print(f"Succeeded: {outcome.succeeded} | Attempts: {outcome.attempts_used}")
    for rec in outcome.history:
        print(f"  Attempt {rec.attempt}: error={rec.error} | hint={rec.hint_category}")


if __name__ == "__main__":
    asyncio.run(demo_repair_loop())
