import io
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from docx import Document
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, ValidationError

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Ты аудитор документов. Тебе дают текст документа, ты ищешь в нём ошибки:
опечатки, грамматические ошибки, фактические неточности, противоречия внутри текста,
нарушения логики и стиля.

Поле type всегда заполняй одним из следующих значений на английском (ровно как
написано, без перевода и без других вариантов): typo, grammar, factual,
contradiction, logic.

ВАЖНО про язык остальных полей (description, suggested_fix, summary): они
должны быть написаны НА ЯЗЫКЕ ВХОДНОГО ДОКУМЕНТА, а не на языке этой
инструкции. Эта системная инструкция написана по-русски, но это не значит,
что ответ должен быть на русском — определи язык документа по его тексту
и пиши на нём. Если документ на английском — description, suggested_fix
и summary должны быть на английском; если документ на русском — на русском;
и так для любого другого языка документа. Не переключайся на язык инструкции
по умолчанию.

Для каждой найденной ошибки заполни suggested_fix:
- Если ошибку можно исправить однозначной текстовой заменой (опечатка, пунктуация,
  грамматика, явная фактическая ошибка с одним правильным вариантом) — укажи в
  suggested_fix предлагаемый исправленный фрагмент текста.
- Если для исправления нужно решение человека (противоречивые цифры/факты внутри
  документа, когда неизвестно, какой из вариантов верный, неоднозначность,
  стилистическое замечание без единственно верного варианта) — suggested_fix
  должен быть строго null. Не придумывай правку, если не уверен, какая из
  противоречащих друг другу версий верна.

Если ошибок нет, "errors" — пустой список."""


class AuditError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    location: str
    description: str
    suggested_fix: str | None


class AuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    errors: list[AuditError]
    summary: str


class AuditModelError(Exception):
    """Модель не вернула структурированный отчёт (нет блока tool_use)."""


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


def _report_from_content(content) -> AuditReport:
    """Достаёт AuditReport из блока tool_use ответа модели.

    При forced tool use блок tool_use обычно есть, но при отказе модели или
    обрыве по max_tokens его может не быть — тогда явная AuditModelError
    вместо StopIteration (которая всплыла бы как голый 500)."""
    block = next((b for b in content if b.type == "tool_use"), None)
    if block is None:
        raise AuditModelError("Модель не вернула tool_use с отчётом")
    return AuditReport.model_validate(block.input)


def audit(text: str) -> AuditReport:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        tools=[AUDIT_REPORT_TOOL],
        tool_choice={"type": "tool", "name": "submit_audit_report"},
    )
    return _report_from_content(response.content)


if __name__ == "__main__":
    path = sys.argv[1]

    try:
        document_text = extract_text(path)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    try:
        result = audit(document_text)
    except (ValidationError, AuditModelError) as e:
        print("Ответ модели не соответствует схеме AuditReport:", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

    print(result.model_dump_json(indent=2))
