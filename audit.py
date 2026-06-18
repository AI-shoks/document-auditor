import json
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

Ответь ТОЛЬКО валидным JSON без какого-либо текста до или после, без markdown-обёртки,
строго в формате:
{
  "errors": [
    {"type": "string", "location": "string", "description": "string"}
  ],
  "summary": "string"
}

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


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".txt":
        with open(path, encoding="utf-8") as f:
            return f.read()
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")


def audit(text: str) -> AuditReport:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return AuditReport.model_validate(json.loads(raw))


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
