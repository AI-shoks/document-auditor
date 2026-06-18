from dataclasses import dataclass


@dataclass(frozen=True)
class Key:
    type: str
    paragraph: int


@dataclass
class MatchResult:
    tp: int
    fp: int
    fn: int


def match(predicted_keys: list[Key], ground_truth_keys: list[Key]) -> MatchResult:
    """Deterministic greedy matching by (type, paragraph) key.

    Does NOT compare description text — wording from the model never has to
    match the human's wording. Duplicate keys (e.g. two distinct planted
    typos in the same paragraph) are matched one-to-one, not collapsed into
    a set, so each ground-truth error can only satisfy one predicted error.
    """
    remaining_gt = list(ground_truth_keys)
    tp = 0
    fp = 0

    for key in predicted_keys:
        if key in remaining_gt:
            remaining_gt.remove(key)
            tp += 1
        else:
            fp += 1

    fn = len(remaining_gt)
    return MatchResult(tp=tp, fp=fp, fn=fn)
