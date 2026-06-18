import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic
from docx import Document
from pydantic import BaseModel, ConfigDict, ValidationError

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Ты аудитор документов. Тебе дают текст документа, ты ищешь в нём ошибки:
опечатки, грамматические ошибки, фактические неточности, противоречия внутри текста,
нарушения логики и стиля.

Если ошибок нет, "errors" — пустой список."""


class AuditError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    location: str
    description: str


class AuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    errors: list[AuditError]
    summary: str


AUDIT_REPORT_TOOL = {
    "name": "submit_audit_report",
    "description": "Отправить структурированный отчёт об ошибках, найденных в документе.",
    "input_schema": AuditReport.model_json_schema(),
}


def extract_text_from_bytes(content: bytes, suffix: str) -> str:
    suffix = suffix.lower()
    if suffix == ".txt":
        return content.decode("utf-8")
    if suffix == ".docx":
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")


def extract_text(path: str) -> str:
    suffix = Path(path).suffix
    with open(path, "rb") as f:
        return extract_text_from_bytes(f.read(), suffix)


def audit(text: str) -> AuditReport:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        tools=[AUDIT_REPORT_TOOL],
        tool_choice={"type": "tool", "name": "submit_audit_report"},
    )
    tool_use_block = next(
        block for block in response.content if block.type == "tool_use"
    )
    return AuditReport.model_validate(tool_use_block.input)


if __name__ == "__main__":
    path = sys.argv[1]

    try:
        document_text = extract_text(path)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    try:
        result = audit(document_text)
    except ValidationError as e:
        print("Ответ модели не соответствует схеме AuditReport:", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

    print(result.model_dump_json(indent=2))
