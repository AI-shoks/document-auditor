import importlib


def load_prompt(version: str) -> str:
    module = importlib.import_module(f"prompts.{version}")
    return module.PROMPT
