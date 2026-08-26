import argparse
from pathlib import Path

from dataops_demo_pipeline.pipeline import SUPPORTED_SCENARIOS, execute_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DataOps M3 data-quality demo")
    parser.add_argument(
        "--scenario",
        choices=sorted(SUPPORTED_SCENARIOS),
        default="none",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/data-quality-report.json"),
    )
    arguments = parser.parse_args()
    return execute_pipeline(arguments.scenario, arguments.output)


if __name__ == "__main__":
    raise SystemExit(main())
