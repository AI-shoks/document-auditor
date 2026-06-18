import sys
from pathlib import Path

from paragraphs import split_paragraphs

sys.stdout.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    for i, p in enumerate(split_paragraphs(text), start=1):
        print(f"[P{i}] {p}\n")
