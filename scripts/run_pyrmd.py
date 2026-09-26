"""Run PyRMD in benchmark or screening mode.

PyRMD writes its output files into the folder it is started from, so this script
starts it from results/<mode>/ to keep each run's outputs separate.

Usage (inside the `pyrmd` conda environment):
    python scripts/run_pyrmd.py benchmark
    python scripts/run_pyrmd.py screening
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYRMD = ROOT / "pyrmd" / "PyRMD_v1.03.py"


def run_pyrmd(config: Path, workdir: Path) -> None:
    if not PYRMD.is_file():
        sys.exit(f"PyRMD not found at {PYRMD}.\nDownload PyRMD_v1.03.py from "
                 "https://github.com/cosconatilab/PyRMD into the pyrmd/ folder (see README).")
    workdir.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(PYRMD), str(config)], cwd=workdir, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["benchmark", "screening"])
    args = parser.parse_args()

    workdir = ROOT / "results" / args.mode
    if args.mode == "benchmark":
        # PyRMD appends to an existing benchmark file, so start clean
        (workdir / "benchmark_results.csv").unlink(missing_ok=True)
    run_pyrmd(ROOT / "config" / f"{args.mode}.ini", workdir)
    print(f"\nDone. Outputs are in {workdir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
