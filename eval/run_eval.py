import argparse
import json
import sys
from pathlib import Path

from eval_audit import audit_eval
from ground_truth import load_ground_truth
from match import Key, match
from metrics import precision_recall_f1

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DOCS_DIR = Path(__file__).parent / "docs"


def doc_ids() -> list[str]:
    return sorted(p.stem for p in DOCS_DIR.glob("doc*.txt"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-version", default="v1")
    args = parser.parse_args()

    rows = []
    total_tp = total_fp = total_fn = 0
    skipped = []

    for doc_id in doc_ids():
        gt_path = DOCS_DIR / f"{doc_id}.ground_truth.json"
        gt = load_ground_truth(gt_path)

        if gt.status != "ready":
            skipped.append(doc_id)
            continue

        text = (DOCS_DIR / f"{doc_id}.txt").read_text(encoding="utf-8")
        report = audit_eval(text, prompt_version=args.prompt_version)

        predicted_keys = [Key(e.type, e.paragraph) for e in report.errors]
        gt_keys = [Key(e.type, e.paragraph) for e in gt.errors]

        result = match(predicted_keys, gt_keys)
        m = precision_recall_f1(result.tp, result.fp, result.fn)

        rows.append(
            {
                "doc_id": doc_id,
                "tp": result.tp,
                "fp": result.fp,
                "fn": result.fn,
                "precision": round(m.precision, 3),
                "recall": round(m.recall, 3),
                "f1": round(m.f1, 3),
            }
        )
        total_tp += result.tp
        total_fp += result.fp
        total_fn += result.fn

    if skipped:
        print(
            f"Пропущены (status != 'ready'): {', '.join(skipped)}",
            file=sys.stderr,
        )

    overall = precision_recall_f1(total_tp, total_fp, total_fn)
    summary = {
        "prompt_version": args.prompt_version,
        "docs": rows,
        "aggregate": {
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": round(overall.precision, 3),
            "recall": round(overall.recall, 3),
            "f1": round(overall.f1, 3),
        },
    }

    print(f"{'doc_id':<10}{'TP':>4}{'FP':>4}{'FN':>4}{'P':>8}{'R':>8}{'F1':>8}")
    for row in rows:
        print(
            f"{row['doc_id']:<10}{row['tp']:>4}{row['fp']:>4}{row['fn']:>4}"
            f"{row['precision']:>8}{row['recall']:>8}{row['f1']:>8}"
        )
    print("-" * 46)
    a = summary["aggregate"]
    print(
        f"{'AGGREGATE':<10}{a['tp']:>4}{a['fp']:>4}{a['fn']:>4}"
        f"{a['precision']:>8}{a['recall']:>8}{a['f1']:>8}"
    )

    results_path = Path(__file__).parent / "results.json"
    results_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nЗаписано в {results_path}")


if __name__ == "__main__":
    main()
