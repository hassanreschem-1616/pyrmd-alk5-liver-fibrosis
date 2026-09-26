"""Tune PyRMD's epsilon cutoffs by benchmarking every combination.

The PyRMD authors recommend testing epsilon_cutoff_actives in {0.84, 0.95, 0.98} and
epsilon_cutoff_inactives in {0.70, 0.84, 0.95, 0.98}, then choosing the combination with
the best trade-off between true-positive rate (TPR) and false-positive rate (FPR).
Here that trade-off is measured with Youden's J = TPR - FPR.

Usage (inside the `pyrmd` conda environment):
    python scripts/epsilon_scan.py            # run the scan and print the ranking
    python scripts/epsilon_scan.py --apply    # also write the best values into config/screening.ini
"""
import argparse
import itertools
import re
from pathlib import Path

import pandas as pd

from run_pyrmd import ROOT, run_pyrmd

EPS_ACTIVES = [0.84, 0.95, 0.98]
EPS_INACTIVES = [0.70, 0.84, 0.95, 0.98]
WORKDIR = ROOT / "results" / "epsilon_scan"
RESULTS = WORKDIR / "epsilon_scan.csv"


def set_values(text: str, values: dict) -> str:
    for key, value in values.items():
        text = re.sub(rf"(?m)^{key}\s*=.*$", f"{key}={value}", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the best cutoffs into config/screening.ini")
    args = parser.parse_args()

    WORKDIR.mkdir(parents=True, exist_ok=True)
    RESULTS.unlink(missing_ok=True)
    template = (ROOT / "config" / "benchmark.ini").read_text()

    combos = list(itertools.product(EPS_ACTIVES, EPS_INACTIVES))
    for i, (eps_a, eps_i) in enumerate(combos, 1):
        print(f"\n=== [{i}/{len(combos)}] epsilon actives = {eps_a}, epsilon inactives = {eps_i} ===")
        config = WORKDIR / f"benchmark_ea{eps_a}_ei{eps_i}.ini"
        config.write_text(set_values(template, {
            "epsilon_cutoff_actives": eps_a,
            "epsilon_cutoff_inactives": eps_i,
            "benchmark_file": RESULTS.name,   # every run appends one row to the same file
        }))
        run_pyrmd(config, WORKDIR)

    df = pd.read_csv(RESULTS)
    df["Youden J"] = df["TPR"] - df["FPR"]
    cols = ["epsilon_cutoff_actives", "epsilon_cutoff_inactives", "TPR", "FPR", "Precision",
            "F Score", "ROC AUC", "PRC AUC", "BEDROC", "Youden J"]
    ranking = df[cols].sort_values("Youden J", ascending=False)
    ranking.to_csv(WORKDIR / "epsilon_scan_ranked.csv", index=False)
    print("\n" + ranking.round(3).to_string(index=False))

    best = ranking.iloc[0]
    print(f"\nBest combination: epsilon actives = {best['epsilon_cutoff_actives']}, "
          f"epsilon inactives = {best['epsilon_cutoff_inactives']} (Youden J = {best['Youden J']:.3f})")

    if args.apply:
        screening = ROOT / "config" / "screening.ini"
        screening.write_text(set_values(screening.read_text(), {
            "epsilon_cutoff_actives": best["epsilon_cutoff_actives"],
            "epsilon_cutoff_inactives": best["epsilon_cutoff_inactives"],
        }))
        benchmark = ROOT / "config" / "benchmark.ini"
        benchmark.write_text(set_values(benchmark.read_text(), {
            "epsilon_cutoff_actives": best["epsilon_cutoff_actives"],
            "epsilon_cutoff_inactives": best["epsilon_cutoff_inactives"],
        }))
        print("Updated config/benchmark.ini and config/screening.ini with the best cutoffs.")


if __name__ == "__main__":
    main()
