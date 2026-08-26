import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd
from great_expectations import expectations as gxe

CONTRACT = {"name": "customer-orders", "version": "1.0.0"}
EXPECTED_COLUMNS = ["customer_id", "age", "amount"]
SUPPORTED_SCENARIOS = {"none", "schema_drift", "null_rate", "duplicate", "range", "volume"}


@dataclass(frozen=True, slots=True)
class CheckSpec:
    check_id: str
    dimension: str
    expectation_name: str
    expectation: Any
    expected: object


def build_dataframe(scenario: str) -> pd.DataFrame:
    if scenario not in SUPPORTED_SCENARIOS:
        raise ValueError(f"Unsupported fault scenario: {scenario}")

    row_count = 20 if scenario == "volume" else 200
    dataframe = pd.DataFrame(
        {
            "customer_id": [f"CUS-{index:04d}" for index in range(row_count)],
            "age": [18 + (index % 63) for index in range(row_count)],
            "amount": [float(25 + (index * 17) % 5_000) for index in range(row_count)],
        }
    )
    if scenario == "schema_drift":
        dataframe = dataframe.rename(columns={"amount": "total_amount"})
    elif scenario == "null_rate":
        dataframe.loc[:9, "customer_id"] = None
    elif scenario == "duplicate":
        dataframe.loc[row_count - 1, "customer_id"] = dataframe.loc[0, "customer_id"]
    elif scenario == "range":
        dataframe.loc[0, "age"] = 15
        dataframe.loc[1, "age"] = 120
        dataframe.loc[0, "amount"] = -10.0
        dataframe.loc[1, "amount"] = 20_000.0
    return dataframe


def validate_scenario(scenario: str) -> dict[str, object]:
    dataframe = build_dataframe(scenario)
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="dataops-demo-pandas")
    asset = data_source.add_dataframe_asset(name="customer-orders")
    batch_definition = asset.add_batch_definition_whole_dataframe("whole-dataframe")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": dataframe})

    checks = [_run_check(batch, spec) for spec in _check_specs()]
    passed = sum(bool(check["success"]) for check in checks)
    failed = len(checks) - passed
    return {
        "schema_version": "1.0",
        "contract": CONTRACT,
        "scenario": scenario,
        "success": failed == 0,
        "summary": {"checks": len(checks), "passed": passed, "failed": failed},
        "checks": checks,
        "dataset": {
            "row_count": len(dataframe.index),
            "columns": list(dataframe.columns),
        },
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def execute_pipeline(scenario: str, output: Path) -> int:
    report = validate_scenario(scenario)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = report["summary"]
    print(
        f"Data quality scenario={scenario} success={str(report['success']).lower()} "
        f"passed={summary['passed']} failed={summary['failed']} report={output}"
    )
    return 0 if report["success"] else 2


def _check_specs() -> list[CheckSpec]:
    summary_result = {"result_format": "SUMMARY"}
    return [
        CheckSpec(
            check_id="schema.required_columns",
            dimension="schema",
            expectation_name="expect_table_columns_to_match_set",
            expectation=gxe.ExpectTableColumnsToMatchSet(
                column_set=EXPECTED_COLUMNS,
                exact_match=True,
                catch_exceptions=True,
                result_format=summary_result,
            ),
            expected=EXPECTED_COLUMNS,
        ),
        CheckSpec(
            check_id="completeness.customer_id",
            dimension="completeness",
            expectation_name="expect_column_values_to_not_be_null",
            expectation=gxe.ExpectColumnValuesToNotBeNull(
                column="customer_id",
                mostly=0.99,
                result_format=summary_result,
            ),
            expected={"mostly": 0.99},
        ),
        CheckSpec(
            check_id="uniqueness.customer_id",
            dimension="uniqueness",
            expectation_name="expect_column_values_to_be_unique",
            expectation=gxe.ExpectColumnValuesToBeUnique(
                column="customer_id",
                result_format=summary_result,
            ),
            expected={"mostly": 1.0},
        ),
        CheckSpec(
            check_id="validity.age_range",
            dimension="validity",
            expectation_name="expect_column_values_to_be_between",
            expectation=gxe.ExpectColumnValuesToBeBetween(
                column="age",
                min_value=18,
                max_value=100,
                result_format=summary_result,
            ),
            expected={"min_value": 18, "max_value": 100},
        ),
        CheckSpec(
            check_id="validity.amount_range",
            dimension="validity",
            expectation_name="expect_column_values_to_be_between",
            expectation=gxe.ExpectColumnValuesToBeBetween(
                column="amount",
                min_value=0,
                max_value=10_000,
                result_format=summary_result,
            ),
            expected={"min_value": 0, "max_value": 10_000},
        ),
        CheckSpec(
            check_id="volume.row_count",
            dimension="volume",
            expectation_name="expect_table_row_count_to_be_between",
            expectation=gxe.ExpectTableRowCountToBeBetween(
                min_value=100,
                max_value=1_000,
                catch_exceptions=True,
                result_format=summary_result,
            ),
            expected={"min_value": 100, "max_value": 1_000},
        ),
    ]


def _run_check(batch: Any, spec: CheckSpec) -> dict[str, object]:
    try:
        validation = batch.validate(spec.expectation)
        serialized = validation.to_json_dict()
        observed = serialized.get("result", {})
        exception = serialized.get("exception_info", {})
        if exception.get("raised_exception"):
            observed = {
                **observed,
                "exception_message": str(exception.get("exception_message", ""))[:1_000],
            }
        success = bool(validation.success)
    except Exception as exc:  # GX can raise when schema drift removes a referenced column.
        success = False
        observed = {"exception_type": type(exc).__name__, "exception_message": str(exc)[:1_000]}
    return {
        "id": spec.check_id,
        "dimension": spec.dimension,
        "success": success,
        "expectation": spec.expectation_name,
        "expected": spec.expected,
        "observed": observed,
    }
