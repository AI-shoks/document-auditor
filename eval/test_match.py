from match import Key, match


def test_exact_match_is_tp():
    gt = [Key("typo", 1), Key("factual", 3)]
    pred = [Key("typo", 1), Key("factual", 3)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (2, 0, 0)


def test_missed_error_is_fn():
    gt = [Key("typo", 1), Key("factual", 3)]
    pred = [Key("typo", 1)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (1, 0, 1)


def test_hallucinated_error_is_fp():
    gt = [Key("typo", 1)]
    pred = [Key("typo", 1), Key("contradiction", 5)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (1, 1, 0)


def test_wrong_type_same_paragraph_does_not_match():
    gt = [Key("factual", 2)]
    pred = [Key("grammar", 2)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (0, 1, 1)


def test_wrong_paragraph_same_type_does_not_match():
    gt = [Key("factual", 2)]
    pred = [Key("factual", 5)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (0, 1, 1)


def test_duplicate_keys_match_one_to_one():
    gt = [Key("typo", 1), Key("typo", 1)]
    pred = [Key("typo", 1)]
    result = match(pred, gt)
    assert (result.tp, result.fp, result.fn) == (1, 0, 1)


def test_empty_prediction_all_fn():
    gt = [Key("typo", 1), Key("factual", 2)]
    result = match([], gt)
    assert (result.tp, result.fp, result.fn) == (0, 0, 2)


def test_empty_ground_truth_all_fp():
    pred = [Key("typo", 1)]
    result = match(pred, [])
    assert (result.tp, result.fp, result.fn) == (0, 1, 0)
