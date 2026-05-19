from alin_core.redline_guard import evaluate_action, load_redlines, validate_redlines_structure


def test_redlines_structure_is_valid():
    redlines = load_redlines()
    validate_redlines_structure(redlines)
    assert len(redlines["rules"]) >= 10


def test_network_action_is_blocked():
    decision = evaluate_action({"operation": "network_request", "note": "https://example.invalid"})
    assert decision.allowed is False
    assert "RL003_INTERNET" in {finding.rule_id for finding in decision.findings}


def test_local_report_action_is_allowed():
    decision = evaluate_action({"operation": "write_report", "paths": ["Reports/local.txt"]})
    assert decision.allowed is True
