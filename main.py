from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import ValidationError

from audit import AuditReport, audit, extract_text_from_bytes

app = FastAPI(title="Document Auditor")


@app.post("/audit", response_model=AuditReport)
async def audit_endpoint(file: UploadFile) -> AuditReport:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    suffix = Path(file.filename or "").suffix
    try:
        text = extract_text_from_bytes(content, suffix)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="В документе нет текста")

    try:
        return audit(text)
    except ValidationError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ответ модели не соответствует схеме AuditReport: {e}",
        )
