import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ANTHROPIC_API_KEY")
if not key or key == "paste-your-key-here":
    print("ANTHROPIC_API_KEY не задан в .env")
else:
    print(f"Ключ найден, длина: {len(key)}")
