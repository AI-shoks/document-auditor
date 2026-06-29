import os
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from audit import AuditModelError, AuditReport, audit, extract_text_from_bytes

# --- Защита публичного демо-эндпоинта ---------------------------------------
# /audit на КАЖДЫЙ вызов тратит токены Anthropic, а эндпоинт публичный (это
# демо из портфолио). Модель защиты здесь СОЗНАТЕЛЬНО иная, чем у write-
# эндпоинта в file-archive (там fail-closed): демо должно оставаться
# кликабельным без ключа, но не должно давать слить бюджет.
#
#   - AUDIT_API_KEY (опц.): если задан в env — требуется заголовок X-API-Key;
#     если НЕ задан — демо открыто, но действуют лимиты ниже.
#   - Глобальный дневной потолок: жёсткий предел расходов НЕЗАВИСИМО от IP
#     (per-IP лимит обходится сменой адреса, дневной потолок — нет). Это и
#     есть настоящая защита кошелька.
#   - Per-IP rate limit: грубый тормоз против частого дёрганья с одного IP.
#   - Предел размера входа: ограничивает стоимость одного вызова.
AUDIT_API_KEY = os.environ.get("AUDIT_API_KEY", "").strip()
RATE_LIMIT = int(os.environ.get("AUDIT_RATE_LIMIT", "5"))            # запросов с одного IP за окно
RATE_WINDOW_SECONDS = 60
DAILY_CAP = int(os.environ.get("AUDIT_DAILY_CAP", "100"))           # всего аудитов в сутки
MAX_INPUT_CHARS = int(os.environ.get("AUDIT_MAX_INPUT_CHARS", "50000"))

# IP -> времена недавних запросов. Sync-зависимости FastAPI исполняются в пуле
# потоков, поэтому общее состояние — под локом.
_hits: dict[str, deque[float]] = defaultdict(deque)
_hits_lock = threading.Lock()
_daily = {"day": date.today(), "count": 0}
_daily_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    """IP клиента с учётом прокси Render: реальный клиент — первый в
    X-Forwarded-For. Заголовок подделываем, поэтому per-IP лимит — это
    defense-in-depth, а не аутентификация; бюджет защищает дневной потолок."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_limits(request: Request) -> None:
    """Зависимость: per-IP rate limit + глобальный дневной потолок. Стоит
    ПЕРЕД проверкой ключа, чтобы перебор ключа тоже упирался в лимит."""
    ip = _client_ip(request)
    now = time.monotonic()
    with _hits_lock:
        hits = _hits[ip]
        while hits and now - hits[0] > RATE_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Слишком много запросов, попробуйте позже")
        hits.append(now)

    with _daily_lock:
        today = date.today()
        if _daily["day"] != today:
            _daily["day"] = today
            _daily["count"] = 0
        if _daily["count"] >= DAILY_CAP:
            raise HTTPException(status_code=429, detail="Дневной лимит демо исчерпан, попробуйте завтра")
        _daily["count"] += 1


def require_audit_key(x_api_key: str | None = Header(default=None)) -> None:
    """Зависимость: ключ ОПЦИОНАЛЕН. Задан в env -> обязателен (сравнение
    через secrets.compare_digest, постоянное время). Не задан -> демо
    открыто (лимиты из enforce_limits всё равно действуют)."""
    if not AUDIT_API_KEY:
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, AUDIT_API_KEY):
        raise HTTPException(status_code=401, detail="Неверный или отсутствующий ключ")


app = FastAPI(title="Document Auditor")


@app.post(
    "/audit",
    response_model=AuditReport,
    dependencies=[Depends(enforce_limits), Depends(require_audit_key)],
)
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

    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Документ слишком большой (максимум {MAX_INPUT_CHARS} символов)",
        )

    try:
        # audit() — блокирующий сетевой вызов к Anthropic; уводим в пул потоков,
        # чтобы не блокировать event loop на время запроса к модели.
        return await run_in_threadpool(audit, text)
    except (ValidationError, AuditModelError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ответ модели не соответствует схеме AuditReport: {e}",
        )
