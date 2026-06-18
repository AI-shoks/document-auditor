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
- Текущий этап: ЭТАП 6 — ЗАВЕРШЁН.

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
Этап 5a закрыт полностью.

## Текущее состояние (Этап 5b)
- audit.py: AuditError получил поле `suggested_fix: str | None`. Для ошибок
  с однозначной текстовой правкой (опечатка, пунктуация, явная фактическая
  ошибка типа "Берлин"→"Париж") модель заполняет конкретный исправленный
  фрагмент. Для случаев, требующих решения человека (противоречивые цифры/
  факты внутри документа, неоднозначность) — `suggested_fix` строго `null`;
  промпт явно запрещает модели выдумывать правку.
- Это только предложение исправления, без автоматического применения к
  документу (.txt/.docx не модифицируются).
- main.py не менялся — `response_model=AuditReport` подхватил новое поле
  автоматически.
- Проверено: sample.txt и sample.docx — однозначные ошибки получают
  конкретный suggested_fix, противоречия (выручка 20%/35%, сотрудники 50/80)
  получают null; uvicorn + curl на /audit → 200, поле suggested_fix есть
  у каждого error. Commit и push сделаны.

## Что нужно доделать в Этапе 5b
Этап 5b закрыт полностью.

## Текущее состояние (Этап 6)
- Новая директория eval/ — отдельная инфраструктура для измерения content-движка,
  audit.py/main.py НЕ изменялись (продуктовая схема с free-text location осталась как была).
- eval/schema.py: отдельная eval-схема EvalAuditError с закрытым enum type
  (typo/grammar/factual/contradiction/logic) и paragraph: int вместо free-text location —
  иначе детерминированный матчинг по ключу невозможен.
- eval/paragraphs.py: split_paragraphs()/number_paragraphs() — единая функция нумерации
  абзацев, используется и в промпте ([P1].. [P2]..), и в show_paragraphs.py (чтобы
  человек размечал ground truth по тем же номерам, что увидит модель).
- eval/match.py: детерминированный greedy-матчинг по ключу (type, paragraph), без
  сравнения текста описания. Покрыт юнит-тестами (eval/test_match.py, 8 тестов).
- eval/eval_audit.py: temperature=0, форсированный tool use, версия промпта — параметр
  (eval/prompts/v1.py, грузится через eval/prompts/__init__.py:load_prompt()).
- eval/run_eval.py: прогоняет все docNN со status:"ready" в eval/docs/, считает
  precision/recall/F1 per-doc и agregate (micro), пишет eval/results.json, печатает таблицу.
  Документы со status:"draft" пропускаются с предупреждением (не считаются как "ошибок нет").
- Датасет: 10 документов размечены ВРУЧНУЮ пользователем (НЕ моделью) —
  eval/docs/doc01..10.txt + doc01..10.ground_truth.json, формат описан в eval/docs/FORMAT.md.
  В процессе разметки найдена и исправлена пользователем реальная ошибка в doc10
  (paragraph-номера были сдвинуты на 1, т.к. абзац не был учтён при ручном подсчёте —
  показывает, почему show_paragraphs.py обязателен, а не подсчёт глазами).
- Финальный прогон (prompt v1): aggregate TP=20, FP=6, FN=4, precision=0.769,
  recall=0.833, F1=0.8. Таблица по всем 10 докам + анализ паттернов ошибок (граница
  типов logic/contradiction/factual размыта; doc10 — модель слила два разных заложенных
  дефекта в одну находку) — в eval/README.md (на английском).
- requirements.txt дополнен pytest==8.4.2 (для eval/test_match.py).

## Что нужно доделать в Этапе 6
Этап 6 закрыт полностью. Следующий шаг — Этап 7 (deploy + видео), но НЕ начинать
без явного запроса пользователя.

## Подводные камни Этапа 1
- Claude иногда оборачивает JSON в ```json ... ```. Воркэранд:
  text.strip().removeprefix("```json").removesuffix("```").strip()
  (уйдёт на Этапе 5 при переходе на structured outputs / tool use).
- Файлы открывать с encoding="utf-8", иначе падает на русском.
- В Windows-консоли (cp1251) print с эмодзи/юникодом падает — нужен
  sys.stdout.reconfigure(encoding="utf-8") в начале скрипта.
- max_tokens=4096 хватает; если срезается — поднять.
- .env НИКОГДА не коммитить (он уже в .gitignore — проверено).

## Инженерные соглашения (durable)
- Аудитор = два движка: ГОСТ-движок детерминированный (python-docx, без LLM),
  контент-движок на LLM. Вход = документ + критерии/ТЗ.
- LLM только для содержания (качество, полнота). Измеримое оформление (ГОСТ:
  шрифт, поля, интервалы) проверяется детерминированно, НИКОГДА не через LLM.
- suggested_fix в схеме nullable; модель не выдумывает правку, если безопасной нет.
- Eval: ground truth размечает человек, НЕ модель; матчинг ошибок по ключу
  тип+локация, не по тексту описания; temperature=0; версия промпта — параметр.
- ГОСТ-движок покрывается юнит-тестами, не precision/recall.
- Конвертация входа в Markdown — эксперимент ПОСЛЕ Этапа 6 (измерить дельту), не в MVP.

## Полный маршрут (СПРАВОЧНО — не реализовывать вперёд)
1. Один файл end-to-end: текст → Claude API → JSON.  → СДЕЛАНО (Этап 1)
2. Pydantic-схема (AuditError, AuditReport).  → СДЕЛАНО (Этап 2)
3. Поддержка форматов: extract_text() для .txt/.docx/.pdf.  → СДЕЛАНО (Этап 3, .txt/.docx; .pdf не реализован — опционально)
4. FastAPI: POST /audit.  → СДЕЛАНО (Этап 4)
5. Режим patch + structured outputs через tool use.  → СДЕЛАНО (5a tool use, 5b suggested_fix)
6. Eval harness: 10 размеченных документов, precision/recall.
7. Deploy (Railway/Render) + 60-сек видео.
