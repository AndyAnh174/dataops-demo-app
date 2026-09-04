import json

import pytest

from dataops_demo_pipeline import pipeline as pipeline_module
from dataops_demo_pipeline.pipeline import (
    execute_pipeline,
    validate_scenario,
)


def test_healthy_dataset_passes_the_versioned_contract() -> None:
    report = validate_scenario("none")

    assert report["schema_version"] == "1.0"
    assert report["contract"] == {"name": "customer-orders", "version": "1.0.0"}
    assert report["scenario"] == "none"
    assert report["success"] is True
    assert report["summary"] == {"checks": 6, "passed": 6, "failed": 0}
    assert report["dataset"] == {
        "row_count": 200,
        "columns": ["customer_id", "age", "amount"],
    }
    assert all(check["success"] for check in report["checks"])


@pytest.mark.parametrize(
    ("scenario", "expected_failed_checks"),
    [
        ("schema_drift", {"schema.required_columns", "validity.amount_range"}),
        ("null_rate", {"completeness.customer_id"}),
        ("duplicate", {"uniqueness.customer_id"}),
        ("range", {"validity.age_range", "validity.amount_range"}),
        ("volume", {"volume.row_count"}),
    ],
)
def test_fault_scenario_is_explained_by_specific_failed_checks(
    scenario: str,
    expected_failed_checks: set[str],
) -> None:
    report = validate_scenario(scenario)

    failed_checks = {check["id"] for check in report["checks"] if not check["success"]}
    assert report["success"] is False
    assert expected_failed_checks <= failed_checks
    assert report["summary"]["failed"] == len(failed_checks)


def test_failed_validation_writes_the_report_before_returning_nonzero(tmp_path) -> None:
    output = tmp_path / "nested" / "data-quality-report.json"

    exit_code = execute_pipeline("duplicate", output)

    assert exit_code == 2
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["scenario"] == "duplicate"
    assert persisted["success"] is False


def test_unknown_fault_scenario_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported fault scenario"):
        validate_scenario("mystery")


def test_quarantine_recovery_removes_invalid_rows_and_verifies_released_data(
    tmp_path,
) -> None:
    output = tmp_path / "recovery-verification.json"

    exit_code = pipeline_module.execute_quarantine_recovery("range", output)

    assert exit_code == 0
    verification = json.loads(output.read_text(encoding="utf-8"))
    assert verification == {
        "schema_version": "1.0",
        "recovery_action": "QUARANTINE",
        "source_scenario": "range",
        "success": True,
        "rows_received": 200,
        "rows_quarantined": 2,
        "rows_released": 198,
        "quality_summary": {"checks": 6, "passed": 6, "failed": 0},
    }


@pytest.mark.parametrize("scenario", ["schema_drift", "volume", "none"])
def test_quarantine_recovery_rejects_non_row_level_scenarios(
    scenario: str,
    tmp_path,
) -> None:
    with pytest.raises(ValueError, match="does not support"):
        pipeline_module.execute_quarantine_recovery(scenario, tmp_path / "verification.json")
