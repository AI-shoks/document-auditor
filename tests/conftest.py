import os

# audit.py при импорте создаёт Anthropic(api_key=...) — без ключа SDK падает.
# Тесты в сеть не ходят (audit() мокается), поэтому ставим заглушку ДО того,
# как тест-модули импортируют main/audit. setdefault — не затираем реальный
# ключ, если он вдруг задан в окружении.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy")
