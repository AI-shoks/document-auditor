import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from schema import ErrorType


class GroundTruthError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ErrorType
    paragraph: int
    note: str = ""


class GroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    status: Literal["draft", "ready"] = "draft"
    errors: list[GroundTruthError]


def load_ground_truth(path: Path) -> GroundTruth:
    data = json.loads(path.read_text(encoding="utf-8"))
    return GroundTruth.model_validate(data)
