import json

import pytest

from dataops_demo_pipeline.pipeline import execute_pipeline, validate_scenario


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
