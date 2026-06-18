# Document Auditor

## Что это
FastAPI-сервис, который принимает документ (.txt/.docx/.pdf),
шлёт текст в Claude API с system-промптом аудитора и возвращает структурированный
отчёт об ошибках. Портфолио-проект для роли Applied AI / LLM Engineer.

## Стек
Python, anthropic SDK, python-dotenv, pydantic, python-docx, FastAPI, uvicorn.
Модель по умолчанию: claude-sonnet-4-6 (точность важнее скорости, не haiku).

## ПРАВИЛА РАБОТЫ НАД ПРОЕКТОМ
- Делаем ОДИН этап за раз. Не реализуем этапы вперёд.
- Каждый этап = работающий запускающийся артефакт + git commit. Сначала артефакт, потом следующий шаг.
- Не предлагать "сначала спроектируем всё". Архитектуру решаем итеративно.
- Текущий этап: ЭТАП 5a — ЗАВЕРШЁН.

## Текущее состояние (Этап 2)
- audit.py: добавлены pydantic-модели AuditError и AuditReport (extra="forbid").
  audit() возвращает AuditReport, а не dict. CLI-обработка оборачивает audit()
  в try/except ValidationError — печатает понятную ошибку в stderr и exit(1)
  вместо traceback или молчаливого провала.
- Проверено: на sample.txt отчёт валидируется штатно; на искусственно испорченном
  JSON (лишнее поле) ловится ValidationError с понятным сообщением.

## Текущее состояние (Этап 1)
- Проект физически лежит в C:\Users\artem\document-auditor.
- Окружение готово (venv, .env с ANTHROPIC_API_KEY, .gitignore, check.py прошёл).
- hello_world.py написан и запущен — ответ приходит, поля разобраны
  (response.content[0].text, usage с input/output_tokens, stop_reason=end_turn).
- audit.py написан и протестирован на sample.txt — находит все заложенные ошибки,
  отдаёт валидный JSON {"errors":[{"type","location","description"}],"summary"}.
- git init сделан, репозиторий создан на GitHub: https://github.com/AI-shoks/document-auditor
  (ПУБЛИЧНЫЙ — изначально был сделан приватным по просьбе пользователя, затем переключён
  на публичный, как и предполагал исходный план).
  Первый commit и push сделаны.
- git и gh CLI были не установлены на машине — поставлены через winget в рамках этого этапа.

## Что нужно доделать в Этапе 1
Этап 1 закрыт полностью.

## Что нужно доделать в Этапе 2
Этап 2 закрыт полностью.

## Текущее состояние (Этап 3)
- audit.py: добавлена extract_text(path) — ветка по расширению (.txt читает как раньше,
  .docx читает через python-docx, абзацы join по "\n"). .pdf не реализован (опционально
  по плану, не блокер).
- Неподдерживаемый формат (например .pdf) даёт понятную ошибку в stderr + exit(1),
  без traceback.
- stderr тоже переведён на utf-8 (sys.stderr.reconfigure) — иначе сообщения об ошибках
  на русском превращались в мусор в cp1251-консоли.
- Добавлен sample.docx (сделан из текста sample.txt) как тестовый артефакт реального .docx.
- requirements.txt зафиксирован (pip freeze по факту установленных версий).
- Проверено: audit.py sample.txt и audit.py sample.docx оба дают валидный осмысленный
  AuditReport (расходятся в деталях формулировок — ожидаемая недетерминированность LLM,
  не баг); audit.py на .pdf даёт чистую ошибку формата.

## Что нужно доделать в Этапе 3
Этап 3 закрыт (минимум .txt/.docx). .pdf не сделан — по плану это бонус, не блокер.

## Текущее состояние (Этап 4)
- main.py: FastAPI-приложение с эндпоинтом POST /audit (UploadFile → AuditReport).
- audit.py рефакторен: extract_text(path) теперь использует общую
  extract_text_from_bytes(content: bytes, suffix: str), которую вызывают и CLI,
  и main.py (избегает дублирования логики .txt/.docx между скриптом и сервисом).
- Обработка ошибок: пустой файл → 400, неподдерживаемый формат → 400,
  невалидный ответ модели (ValidationError) → 502. Никаких голых 500 с traceback.
- Проверено curl-ом: .txt и .docx → 200 + валидный AuditReport JSON;
  пустой .txt → 400 "Файл пустой"; .pdf → 400 "Неподдерживаемый формат файла: .pdf".
- requirements.txt дополнен (fastapi, uvicorn[standard], python-multipart).
- Запуск: ./venv/Scripts/python.exe -m uvicorn main:app --port 8000 (или без venv-префикса
  при активированном venv).

## Что нужно доделать в Этапе 4
Этап 4 закрыт полностью.

## Текущее состояние (Этап 5a)
- audit.py: ответ модели теперь приходит через forced tool use (`AUDIT_REPORT_TOOL`
  с `input_schema = AuditReport.model_json_schema()`), а не текстом с markdown-обёрткой.
  Убран воркэраунд `removeprefix("```json")...`/`json.loads` — парсинг идёт через
  `tool_use_block.input` → `AuditReport.model_validate(...)`. Импорт `json` удалён
  как неиспользуемый. SYSTEM_PROMPT очищен от инструкции про "только JSON без markdown".
- main.py не менялся — зависит только от `audit()`/`ValidationError`, контракт тот же.
- Проверено: audit.py на sample.txt и sample.docx находит те же классы заложенных
  ошибок, что и раньше; uvicorn + curl на /audit с sample.txt → 200 + валидный
  AuditReport. Commit и push сделаны.

## Что нужно доделать в Этапе 5a
Этап 5a закрыт полностью. Следующий шаг — Этап 5b (режим patch) из полного
маршрута ниже, но НЕ начинать без явного запроса пользователя.

## Подводные камни Этапа 1
- Claude иногда оборачивает JSON в ```json ... ```. Воркэранд:
  text.strip().removeprefix("```json").removesuffix("```").strip()
  (уйдёт на Этапе 5 при переходе на structured outputs / tool use).
- Файлы открывать с encoding="utf-8", иначе падает на русском.
- В Windows-консоли (cp1251) print с эмодзи/юникодом падает — нужен
  sys.stdout.reconfigure(encoding="utf-8") в начале скрипта.
- max_tokens=4096 хватает; если срезается — поднять.
- .env НИКОГДА не коммитить (он уже в .gitignore — проверено).

## Полный маршрут (СПРАВОЧНО — не реализовывать вперёд)
1. Один файл end-to-end: текст → Claude API → JSON.  → СДЕЛАНО (Этап 1)
2. Pydantic-схема (AuditError, AuditReport).  → СДЕЛАНО (Этап 2)
3. Поддержка форматов: extract_text() для .txt/.docx/.pdf.  → СДЕЛАНО (Этап 3, .txt/.docx; .pdf не реализован — опционально)
4. FastAPI: POST /audit.  → СДЕЛАНО (Этап 4)
5. Режим patch + structured outputs через tool use.  → 5a СДЕЛАНО (tool use), 5b не начат
6. Eval harness: 10 размеченных документов, precision/recall.
7. Deploy (Railway/Render) + 60-сек видео.
