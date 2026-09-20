from scripts.evaluate_accuracy import evaluate


def test_supported_fixture_dates_are_not_missed():
    result = evaluate()
    assert result["false_negatives"] == 0


def test_benchmark_documents_known_historical_false_positive():
    result = evaluate()
    historical = next(case for case in result["cases"] if case["name"] == "historical date false positive")
    assert historical["extra"] == 1


def test_relative_dates_are_safely_ignored():
    result = evaluate()
    relative = next(case for case in result["cases"] if case["name"] == "unsupported relative dates")
    assert relative["found"] == 0
    assert relative["passed"] is True
