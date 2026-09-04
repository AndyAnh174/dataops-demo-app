import argparse
from pathlib import Path

from dataops_demo_pipeline.pipeline import QUARANTINE_SCENARIOS, execute_quarantine_recovery


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a verified DataOps recovery action")
    parser.add_argument(
        "--scenario",
        choices=sorted(QUARANTINE_SCENARIOS),
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/recovery-verification.json"),
    )
    arguments = parser.parse_args()
    return execute_quarantine_recovery(arguments.scenario, arguments.output)


if __name__ == "__main__":
    raise SystemExit(main())
