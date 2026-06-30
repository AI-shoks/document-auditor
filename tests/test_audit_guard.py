import pytest

from audit import AuditModelError, AuditReport, _report_from_content


class _Block:
    """Минимальный двойник блока ответа Anthropic: нужны только .type/.input."""

    def __init__(self, type_: str, input_: dict | None = None):
        self.type = type_
        self.input = input_


def test_guard_raises_when_no_tool_use():
    # Ответ без блока tool_use (например, отказ модели) -> явная ошибка,
    # а не StopIteration, которая всплыла бы голым 500.
    with pytest.raises(AuditModelError):
        _report_from_content([_Block("text")])


def test_report_parsed_from_tool_use():
    block = _Block("tool_use", {"errors": [], "summary": "ок"})
    report = _report_from_content([block])
    assert isinstance(report, AuditReport)
    assert report.summary == "ок"
    assert report.errors == []
