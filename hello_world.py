import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Скажи привет в одном предложении."}],
)

print("TEXT:", response.content[0].text)
print("USAGE:", response.usage)
print("STOP_REASON:", response.stop_reason)
