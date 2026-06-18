from typing import Literal

from pydantic import BaseModel, ConfigDict

ErrorType = Literal["typo", "grammar", "factual", "contradiction", "logic"]


class EvalAuditError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ErrorType
    paragraph: int
    description: str


class EvalAuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    errors: list[EvalAuditError]
    summary: str


EVAL_AUDIT_REPORT_TOOL = {
    "name": "submit_audit_report",
    "description": "Отправить структурированный отчёт об ошибках, найденных в документе.",
    "input_schema": EvalAuditReport.model_json_schema(),
}
