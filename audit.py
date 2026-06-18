import json
import os
import sys

from dotenv import load_dotenv
from anthropic import Anthropic

sys.stdout.reconfigure(encoding="utf-8")

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


def audit(text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        document_text = f.read()

    result = audit(document_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
