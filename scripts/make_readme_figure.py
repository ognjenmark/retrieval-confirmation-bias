"""Draw the README figure from saved pilot results (development questions)."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = ROOT / "docs" / "figures" / "pilot_results.png"

TRUE_COLOR = "#2a7ab0"
WRONG_COLOR = "#c0392b"
PART_COLOR = "#e08e7f"

plt.rcParams.update({"figure.dpi": 100, "axes.grid": True, "grid.alpha": 0.25})


def parse_ci(text: str) -> tuple[float, float]:
    low, high = text.split(" to ")
    return float(low), float(high)


def plot_retrieval(ax: plt.Axes) -> None:
    df = pd.read_csv(RESULTS / "asymmetry_true_wrong_dev.csv")
    df = df[df["space"] == "corpus"].reset_index(drop=True)
    x = range(len(df))
    offset = 0.18
    for column, ci_column, color, label, shift in [
        ("true_gain", "true_ci", TRUE_COLOR, "+ correct answer (q_true)", -offset),
        ("wrong_change", "wrong_ci", WRONG_COLOR, "+ wrong candidate (q_wrong)", offset),
    ]:
        cis = [parse_ci(c) for c in df[ci_column]]
        lower = [v - lo for v, (lo, _) in zip(df[column], cis)]
        upper = [hi - v for v, (_, hi) in zip(df[column], cis)]
        ax.errorbar([i + shift for i in x], df[column], yerr=[lower, upper], fmt="o", color=color,
                    capsize=4, label=label)
    ax.axhline(0, color="#555555", linewidth=1)
    ax.set_xticks(list(x), df["metric"])
    ax.set_ylabel("Change in gold recall vs q_keywords")
    ax.set_title("Retrieval (BM25, full corpus): wrong candidate barely moves recall")
    ax.legend(loc="upper left")


def plot_reader(ax: plt.Axes) -> None:
    df = pd.read_csv(RESULTS / "reader_summary_dev.csv")
    df = df[df["verdict"] == "SUPPORTED"].reset_index(drop=True)
    labels = {
        "H4 wrong candidate: wrong_wrong - wrong_keywords": ("Wrong candidate:\nq_wrong vs q_keywords results",
                                                              WRONG_COLOR),
        "snippet control, documents: wrong_wrong_kwsnip - wrong_keywords": ("  part from documents", PART_COLOR),
        "snippet control, snippets: wrong_wrong - wrong_wrong_kwsnip": ("  part from snippets", PART_COLOR),
        "correct answer: true_true - true_keywords": ("Correct answer:\nq_true vs q_keywords results", TRUE_COLOR),
    }
    order = list(labels)
    df = df.set_index("comparison").loc[order].reset_index()
    y = list(range(len(df)))[::-1]
    for yi, (_, row) in zip(y, df.iterrows()):
        color = labels[row["comparison"]][1]
        xerr = [[row["difference"] - row["ci_low"]], [row["ci_high"] - row["difference"]]]
        ax.errorbar(row["difference"], yi, xerr=xerr, fmt="o", color=color, capsize=4)
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(y, [labels[c][0] for c in df["comparison"]])
    ax.set_xlabel("Change in share judged SUPPORTED (paired, 95% CI)")
    ax.set_title(f"Reader (Qwen3-4B, top 5): accepts the wrong candidate more often (n = {df['n'].iloc[0]})")


def main() -> None:
    fig, (left, right) = plt.subplots(1, 2, figsize=(15, 5))
    plot_retrieval(left)
    plot_reader(right)
    fig.suptitle("Pilot on development questions; bootstrap 95% intervals over questions", fontsize=11)
    plt.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
