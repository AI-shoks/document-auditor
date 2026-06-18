import os

from dotenv import load_dotenv
from anthropic import Anthropic

from paragraphs import number_paragraphs
from prompts import load_prompt
from schema import EVAL_AUDIT_REPORT_TOOL, EvalAuditReport

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def audit_eval(text: str, prompt_version: str = "v1") -> EvalAuditReport:
    system_prompt = load_prompt(prompt_version)
    numbered_text = number_paragraphs(text)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": numbered_text}],
        tools=[EVAL_AUDIT_REPORT_TOOL],
        tool_choice={"type": "tool", "name": "submit_audit_report"},
    )
    tool_use_block = next(
        block for block in response.content if block.type == "tool_use"
    )
    return EvalAuditReport.model_validate(tool_use_block.input)
