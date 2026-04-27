"""
analyze_data.py
---------------
Loads the processed movies dataset and produces:

  Analyses
  --------
  1. Rating Analysis   — TMDB vs IMDb correlation + rating distributions
  2. Genre Analysis    — Most common genres + average ratings by genre
  3. Financial Analysis — Budget/revenue correlation + most profitable movies
  4. Temporal Analysis  — Rating trends over time + most productive years

  Outputs
  -------
  data/analysis/plots/01_rating_correlation.png
  data/analysis/plots/02_rating_distributions.png
  data/analysis/plots/03_genre_counts.png
  data/analysis/plots/04_genre_ratings.png
  data/analysis/plots/05_financial_analysis.png
  data/analysis/plots/06_temporal_analysis.png
  base_dir/REPORT.md

Data source (read-only):
  data/processed/movies.csv  — produced by data_processor.py
"""

import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from datetime import datetime, timezone

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR      = Path(__file__).resolve().parent
LOG_DIR       = BASE_DIR / "logs"
DATA_DIR      = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR  = DATA_DIR / "analysis"
PLOTS_DIR     = ANALYSIS_DIR / "plots"

LOG_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename=str(LOG_DIR / "analyze_data.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plot style
# ---------------------------------------------------------------------------

PALETTE   = ["#2D6A8F", "#E8834A", "#4CAF82", "#9B59B6", "#E74C3C", "#F1C40F"]
BG_COLOR  = "#F8F9FA"
GRID_COLOR = "#DEE2E6"

plt.rcParams.update({
    "figure.facecolor":  BG_COLOR,
    "axes.facecolor":    BG_COLOR,
    "axes.edgecolor":    "#CED4DA",
    "axes.grid":         True,
    "grid.color":        GRID_COLOR,
    "grid.linewidth":    0.7,
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
})

# ---------------------------------------------------------------------------
# 1. Data loading
# ---------------------------------------------------------------------------

def load_processed_data() -> pd.DataFrame:
    """Load movies.csv from data/processed/."""
    csv_path = PROCESSED_DIR / "movies.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {csv_path}.\n"
            "Run data_processor.py first."
        )
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info("Loaded %d rows × %d columns from %s", *df.shape, csv_path)
    print(f"  Loaded {len(df):,} movies from {csv_path}")
    return df


# ---------------------------------------------------------------------------
# 2. Rating Analysis
# ---------------------------------------------------------------------------

def analyze_ratings(df: pd.DataFrame) -> Dict:
    """
    1a. Pearson correlation between TMDB and IMDb ratings.
    1b. Distribution of ratings on each platform.

    Returns a dict of summary stats used in the report.
    """
    results: Dict = {}

    pair = df[["tmdb_rating", "imdb_rating"]].dropna()
    if len(pair) >= 3:
        r, p = stats.pearsonr(pair["tmdb_rating"], pair["imdb_rating"])
        results["rating_correlation"]  = round(r, 4)
        results["rating_corr_pvalue"]  = round(p, 6)
        results["rating_corr_n"]       = len(pair)
    else:
        results["rating_correlation"]  = None
        results["rating_corr_pvalue"]  = None
        results["rating_corr_n"]       = len(pair)

    for col, label in [("tmdb_rating", "tmdb"), ("imdb_rating", "imdb")]:
        s = df[col].dropna()
        results[f"{label}_mean"]   = round(float(s.mean()), 3) if len(s) else None
        results[f"{label}_median"] = round(float(s.median()), 3) if len(s) else None
        results[f"{label}_std"]    = round(float(s.std()), 3) if len(s) else None
        results[f"{label}_n"]      = len(s)

    logger.info("Rating analysis: r=%.4f  n=%d", results.get("rating_correlation") or 0, results["rating_corr_n"])

    # --- Plot 1: Correlation scatter ---
    fig, ax = plt.subplots(figsize=(7, 6))
    if len(pair) >= 3:
        ax.scatter(pair["tmdb_rating"], pair["imdb_rating"],
                   alpha=0.45, s=28, color=PALETTE[0], edgecolors="white", linewidths=0.4)
        m, b = np.polyfit(pair["tmdb_rating"], pair["imdb_rating"], 1)
        x_line = np.linspace(pair["tmdb_rating"].min(), pair["tmdb_rating"].max(), 200)
        ax.plot(x_line, m * x_line + b, color=PALETTE[1], linewidth=2,
                label=f"OLS fit  (r = {results['rating_correlation']:.3f})")
        ax.legend(frameon=True)

    ax.set_xlabel("TMDB Rating (0–10)")
    ax.set_ylabel("IMDb Rating (0–10)")
    ax.set_title("TMDB vs IMDb Rating Correlation")
    fig.tight_layout()
    p1 = PLOTS_DIR / "01_rating_correlation.png"
    fig.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p1)

    # --- Plot 2: Rating distributions ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, col, label, color in [
        (axes[0], "tmdb_rating", "TMDB Rating", PALETTE[0]),
        (axes[1], "imdb_rating", "IMDb Rating", PALETTE[2]),
    ]:
        s = df[col].dropna()
        if len(s):
            ax.hist(s, bins=30, color=color, edgecolor="white",
                    linewidth=0.5, alpha=0.85)
            ax.axvline(float(s.mean()), color=PALETTE[1], linewidth=1.8,
                       linestyle="--", label=f"Mean {s.mean():.2f}")
            ax.axvline(float(s.median()), color=PALETTE[4], linewidth=1.8,
                       linestyle=":", label=f"Median {s.median():.2f}")
            ax.legend(frameon=True)
        ax.set_xlabel("Rating")
        ax.set_ylabel("Number of Movies")
        ax.set_title(f"{label} Distribution  (n={len(s):,})")

    fig.suptitle("Rating Distributions", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    p2 = PLOTS_DIR / "02_rating_distributions.png"
    fig.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p2)

    results["plots"] = [str(p1), str(p2)]
    return results


# ---------------------------------------------------------------------------
# 3. Genre Analysis
# ---------------------------------------------------------------------------

def analyze_genres(df: pd.DataFrame) -> Dict:
    """
    2a. Most common genres.
    2b. Average TMDB and IMDb ratings by genre (top 12).

    Returns a dict of summary stats.
    """
    results: Dict = {}

    genre_col = "genres"
    if genre_col not in df.columns:
        logger.warning("No 'genres' column found — skipping genre analysis.")
        results["genre_counts"]       = {}
        results["genre_avg_tmdb"]     = {}
        results["genre_avg_imdb"]     = {}
        results["plots"]              = []
        return results

    # Explode pipe-separated genres
    genre_series = (
        df[genre_col]
        .dropna()
        .str.split("|")
        .explode()
        .str.strip()
        .replace("", pd.NA)
        .dropna()
    )
    genre_counts = genre_series.value_counts()
    results["genre_counts"]     = genre_counts.head(12).to_dict()
    results["total_genre_tags"] = int(len(genre_series))
    results["unique_genres"]    = int(len(genre_counts))

    # Build per-movie genre rows for rating aggregation
    rows = []
    for _, row in df.iterrows():
        if pd.isna(row.get(genre_col)):
            continue
        for g in str(row[genre_col]).split("|"):
            g = g.strip()
            if g:
                rows.append({
                    "genre":       g,
                    "tmdb_rating": row.get("tmdb_rating"),
                    "imdb_rating": row.get("imdb_rating"),
                })
    genre_df = pd.DataFrame(rows)

    top_genres = genre_counts.head(12).index.tolist()
    genre_df   = genre_df[genre_df["genre"].isin(top_genres)]

    avg_tmdb = genre_df.groupby("genre")["tmdb_rating"].mean().reindex(top_genres)
    avg_imdb = genre_df.groupby("genre")["imdb_rating"].mean().reindex(top_genres)
    results["genre_avg_tmdb"] = {k: round(float(v), 3) for k, v in avg_tmdb.dropna().items()}
    results["genre_avg_imdb"] = {k: round(float(v), 3) for k, v in avg_imdb.dropna().items()}

    logger.info("Genre analysis: %d unique genres, top=%s",
                results["unique_genres"], list(genre_counts.index[:3]))

    # --- Plot 3: Most common genres ---
    top_n = genre_counts.head(15)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top_n.index[::-1], top_n.values[::-1],
                   color=PALETTE[0], edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, top_n.values[::-1]):
        ax.text(bar.get_width() + top_n.values.max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=9, color="#555")
    ax.set_xlabel("Number of Movies")
    ax.set_title("Most Common Genres (Top 15)")
    ax.set_xlim(0, top_n.values.max() * 1.12)
    fig.tight_layout()
    p3 = PLOTS_DIR / "03_genre_counts.png"
    fig.savefig(p3, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p3)

    # --- Plot 4: Average ratings by genre ---
    rating_df = pd.DataFrame({
        "TMDB": avg_tmdb,
        "IMDb": avg_imdb,
    }).dropna(how="all").sort_values("TMDB", ascending=False)

    x  = np.arange(len(rating_df))
    w  = 0.38
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - w / 2, rating_df["TMDB"].fillna(0), w,
           label="TMDB", color=PALETTE[0], edgecolor="white", linewidth=0.5)
    ax.bar(x + w / 2, rating_df["IMDb"].fillna(0), w,
           label="IMDb", color=PALETTE[2], edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(rating_df.index, rotation=35, ha="right")
    ax.set_ylabel("Average Rating")
    ax.set_title("Average Ratings by Genre (Top 12)")
    ax.legend(frameon=True)
    ax.set_ylim(0, 10)
    fig.tight_layout()
    p4 = PLOTS_DIR / "04_genre_ratings.png"
    fig.savefig(p4, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p4)

    results["plots"] = [str(p3), str(p4)]
    return results


# ---------------------------------------------------------------------------
# 4. Financial Analysis
# ---------------------------------------------------------------------------

def analyze_financials(df: pd.DataFrame) -> Dict:
    """
    3a. Budget vs revenue correlation.
    3b. Top 10 most profitable movies.

    Returns a dict of summary stats.
    """
    results: Dict = {}

    fin = df[["title", "budget", "revenue", "profit", "roi", "genres"]].copy()
    fin = fin.dropna(subset=["budget", "revenue"])

    if fin.empty:
        logger.warning("No financial data available — skipping financial analysis.")
        results["fin_n"]         = 0
        results["budget_rev_r"]  = None
        results["top_profitable"] = []
        results["plots"]         = []
        return results

    results["fin_n"] = len(fin)

    r, p = stats.pearsonr(np.log1p(fin["budget"]), np.log1p(fin["revenue"]))
    results["budget_rev_r"]       = round(r, 4)
    results["budget_rev_pvalue"]  = round(p, 6)

    top10 = (
        fin.dropna(subset=["profit"])
        .nlargest(10, "profit")[["title", "budget", "revenue", "profit", "roi"]]
        .reset_index(drop=True)
    )
    results["top_profitable"] = top10.to_dict(orient="records")

    logger.info("Financial analysis: n=%d, r=%.4f (log scale)", len(fin), r)

    # --- Plot 5: budget/revenue scatter + top-10 bar ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Scatter: budget vs revenue (log scale)
    ax = axes[0]
    ax.scatter(fin["budget"] / 1e6, fin["revenue"] / 1e6,
               alpha=0.4, s=22, color=PALETTE[0], edgecolors="white", linewidths=0.3)
    if len(fin) >= 3:
        lx = np.log1p(fin["budget"])
        ly = np.log1p(fin["revenue"])
        m, b2 = np.polyfit(lx, ly, 1)
        xs  = np.linspace(fin["budget"].min(), fin["budget"].max(), 300)
        ys  = np.expm1(m * np.log1p(xs) + b2)
        ax.plot(xs / 1e6, ys / 1e6, color=PALETTE[1], linewidth=2,
                label=f"Fit  r={r:.3f} (log)")
        ax.legend(frameon=True)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Budget ($ millions, log scale)")
    ax.set_ylabel("Revenue ($ millions, log scale)")
    ax.set_title("Budget vs Revenue")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}M"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}M"))

    # Bar: top-10 profit
    ax2 = axes[1]
    if not top10.empty:
        labels = top10["title"].str[:22]
        vals   = top10["profit"] / 1e6
        bar_colors = [PALETTE[i % len(PALETTE)] for i in range(len(top10))]
        bars = ax2.barh(labels[::-1], vals[::-1], color=bar_colors[::-1],
                        edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, vals[::-1]):
            ax2.text(bar.get_width() + vals.max() * 0.01,
                     bar.get_y() + bar.get_height() / 2,
                     f"${val:,.0f}M", va="center", fontsize=8)
        ax2.set_xlabel("Profit ($ millions)")
        ax2.set_title("Top 10 Most Profitable Movies")
        ax2.set_xlim(0, vals.max() * 1.18)

    fig.tight_layout()
    p5 = PLOTS_DIR / "05_financial_analysis.png"
    fig.savefig(p5, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p5)

    results["plots"] = [str(p5)]
    return results


# ---------------------------------------------------------------------------
# 5. Temporal Analysis
# ---------------------------------------------------------------------------

def analyze_temporal(df: pd.DataFrame) -> Dict:
    """
    4a. Average ratings per release year.
    4b. Number of movies released per year (most productive years).

    Returns a dict of summary stats.
    """
    results: Dict = {}

    if "release_year" not in df.columns:
        logger.warning("No 'release_year' column — skipping temporal analysis.")
        results["plots"] = []
        return results

    temp = df.dropna(subset=["release_year"]).copy()
    temp["release_year"] = temp["release_year"].astype(int)

    # Restrict to sensible range
    temp = temp[(temp["release_year"] >= 1950) & (temp["release_year"] <= 2025)]

    yearly = (
        temp.groupby("release_year")
        .agg(
            count       =("title", "count"),
            tmdb_avg    =("tmdb_rating", "mean"),
            imdb_avg    =("imdb_rating", "mean"),
        )
        .reset_index()
    )

    top5_prod = yearly.nlargest(5, "count")[["release_year", "count"]].reset_index(drop=True)
    results["top_productive_years"] = top5_prod.to_dict(orient="records")
    results["temporal_n"]           = len(temp)

    logger.info("Temporal analysis: %d movies, years %d–%d",
                len(temp), int(temp["release_year"].min()), int(temp["release_year"].max()))

    # --- Plot 6: temporal trends ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=False)

    # Top panel: movies per year
    ax = axes[0]
    ax.bar(yearly["release_year"], yearly["count"],
           color=PALETTE[0], edgecolor="white", linewidth=0.3, alpha=0.85)
    ax.set_ylabel("Number of Movies")
    ax.set_title("Movies Released per Year")

    # Bottom panel: avg ratings over time (smoothed)
    ax2 = axes[1]
    for col, label, color in [
        ("tmdb_avg", "TMDB", PALETTE[0]),
        ("imdb_avg", "IMDb", PALETTE[2]),
    ]:
        series = yearly[col].dropna()
        years  = yearly.loc[series.index, "release_year"]
        if len(series) >= 5:
            from scipy.ndimage import uniform_filter1d
            smoothed = uniform_filter1d(series.values, size=5)
            ax2.plot(years, series.values, alpha=0.25, linewidth=1, color=color)
            ax2.plot(years, smoothed, linewidth=2.2, color=color, label=label)
        else:
            ax2.plot(years, series.values, linewidth=2, color=color, label=label)

    ax2.set_ylabel("Average Rating")
    ax2.set_xlabel("Release Year")
    ax2.set_title("Average Ratings by Release Year (5-year rolling smooth)")
    ax2.legend(frameon=True)
    ax2.set_ylim(0, 10)

    fig.tight_layout()
    p6 = PLOTS_DIR / "06_temporal_analysis.png"
    fig.savefig(p6, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", p6)

    results["plots"] = [str(p6)]
    return results


# ---------------------------------------------------------------------------
# 6. Markdown Report
# ---------------------------------------------------------------------------

def generate_report(
    df: pd.DataFrame,
    rating_res:    Dict,
    genre_res:     Dict,
    financial_res: Dict,
    temporal_res:  Dict,
) -> Path:
    """
    Build a Markdown summary report (REPORT.md) covering:
      - Data collection summary
      - All four analyses with embedded plot images
      - Interesting insights and patterns
      - Challenges and solutions
      - Limitations and future improvements

    Saves to base_dir/REPORT.md.
    Plot paths are written as relative links from the REPORT.md location
    so the file renders correctly on GitHub, VS Code, and Jupyter.
    """
    report_path = BASE_DIR / "REPORT.md"

    # Helper: make plot path relative to ANALYSIS_DIR so links work in-situ
    def rel(path: str) -> str:
        try:
            return Path(path).relative_to(ANALYSIS_DIR).as_posix()
        except ValueError:
            return path

    # Convenience formatters
    def flt(v, decimals=3):
        return f"{v:.{decimals}f}" if v is not None else "N/A"

    def fmt_m(v):
        """Format a raw dollar value as $XM."""
        try:
            return f"${float(v)/1e6:,.0f}M"
        except (TypeError, ValueError):
            return "—"

    def fmt_roi(v):
        try:
            return f"{float(v):.2f}×"
        except (TypeError, ValueError):
            return "—"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ------------------------------------------------------------------ #
    lines: List[str] = []
    L = lines.append          # shorthand

    # ── Title & TOC ──────────────────────────────────────────────────── #
    L("# Movie Dataset — Analysis Report")
    L("")
    L(f"> **Course:** UCLA STAT 418  "
      f"| **Sources:** TMDB API · OMDb API  "
      f"| **Generated:** {now}")
    L("")
    L("---")
    L("")
    L("## Table of Contents")
    L("")
    L("1. [Data Collection Summary](#1-data-collection-summary)")
    L("2. [Rating Analysis](#2-rating-analysis)")
    L("3. [Genre Analysis](#3-genre-analysis)")
    L("4. [Financial Analysis](#4-financial-analysis)")
    L("5. [Temporal Analysis](#5-temporal-analysis)")
    L("6. [Interesting Insights & Patterns](#6-interesting-insights--patterns)")
    L("7. [Challenges Encountered & Solutions](#7-challenges-encountered--solutions)")
    L("8. [Limitations & Future Improvements](#8-limitations--future-improvements)")
    L("")
    L("---")
    L("")

    # ── 1. Data Collection Summary ───────────────────────────────────── #
    L("## 1. Data Collection Summary")
    L("")
    L("### Sources")
    L("")
    L("| Source | Script | What it provides |")
    L("|--------|--------|-----------------|")
    L("| **TMDB API** | `api_collector.py` | Title, genres, runtime, release date, cast, director, budget, revenue, TMDB rating & vote count |")
    L("| **OMDb API** | `omdb_collector.py` | IMDb rating, number of user votes, Metascore (Metacritic) |")
    L("| **Processed** | `data_processor.py` | Merged & cleaned dataset: deduplication, range validation, derived profit/ROI |")
    L("")
    L("### Dataset at a Glance")
    L("")

    tmdb_n = rating_res.get("tmdb_n", 0)
    imdb_n = rating_res.get("imdb_n", 0)
    fin_n  = financial_res.get("fin_n", 0)
    temp_n = temporal_res.get("temporal_n", 0)
    meta_n = int(df["metascore"].notna().sum()) if "metascore" in df.columns else 0

    L(f"| Metric | Count |")
    L(f"|--------|-------|")
    L(f"| Total movies in processed dataset | **{len(df):,}** |")
    L(f"| Movies with TMDB rating | {tmdb_n:,} |")
    L(f"| Movies with IMDb rating (via OMDb) | {imdb_n:,} |")
    L(f"| Movies with Metascore | {meta_n:,} |")
    L(f"| Movies with budget & revenue data | {fin_n:,} |")
    L(f"| Movies with valid release year | {temp_n:,} |")
    L(f"| Unique genres | {genre_res.get('unique_genres', 0)} |")
    L("")
    L("The two APIs were joined on the `imdb_id` field, which TMDB includes in "
      "its movie detail endpoint. This ensured a deterministic, lossless key with "
      "no fuzzy title-matching required.")
    L("")
    L("---")
    L("")

    # ── 2. Rating Analysis ───────────────────────────────────────────── #
    L("## 2. Rating Analysis")
    L("")

    r_val = rating_res.get("rating_correlation")
    p_val = rating_res.get("rating_corr_pvalue")
    n_val = rating_res.get("rating_corr_n", 0)

    if r_val is not None:
        if r_val > 0.7:
            interp = ("This **strong positive correlation** indicates both platforms "
                      "largely agree on movie quality — high-rated films on TMDB tend "
                      "to be high-rated on IMDb as well.")
        elif r_val > 0.4:
            interp = ("This **moderate correlation** shows general agreement between "
                      "the platforms, but meaningful disagreements exist — audience "
                      "composition and rating scale differences likely contribute.")
        else:
            interp = ("The **weak correlation** suggests the two platforms' user bases "
                      "assess quality quite differently.")
    else:
        interp = "Insufficient overlapping data to compute a reliable correlation."

    L("### 2.1 TMDB vs IMDb Correlation")
    L("")
    L(f"Pearson *r* = **{flt(r_val)}** &nbsp;|&nbsp; "
      f"*p* = {flt(p_val, 4)} &nbsp;|&nbsp; "
      f"*n* = {n_val:,}")
    L("")
    L(interp)
    L("")

    for p in rating_res.get("plots", [])[:1]:   # correlation scatter
        if Path(p).exists():
            L(f"![TMDB vs IMDb Rating Correlation]({rel(p)})")
            L("")

    L("### 2.2 Rating Distribution Summary")
    L("")
    L("| Metric | TMDB | IMDb |")
    L("|--------|------|------|")
    L(f"| Mean   | {flt(rating_res.get('tmdb_mean'), 2)} | {flt(rating_res.get('imdb_mean'), 2)} |")
    L(f"| Median | {flt(rating_res.get('tmdb_median'), 2)} | {flt(rating_res.get('imdb_median'), 2)} |")
    L(f"| Std Dev | {flt(rating_res.get('tmdb_std'), 2)} | {flt(rating_res.get('imdb_std'), 2)} |")
    L(f"| n      | {rating_res.get('tmdb_n', 0):,} | {rating_res.get('imdb_n', 0):,} |")
    L("")

    for p in rating_res.get("plots", [])[1:2]:   # distribution histograms
        if Path(p).exists():
            L(f"![Rating Distributions]({rel(p)})")
            L("")

    L("---")
    L("")

    # ── 3. Genre Analysis ────────────────────────────────────────────── #
    L("## 3. Genre Analysis")
    L("")
    L(f"The dataset spans **{genre_res.get('unique_genres', 0)} unique genres** "
      f"across {genre_res.get('total_genre_tags', 0):,} total genre tags. "
      f"Because TMDB assigns multiple genres per movie, these counts reflect "
      f"per-genre-tag occurrences rather than per-movie counts.")
    L("")

    L("### 3.1 Top 12 Most Common Genres")
    L("")
    gc = genre_res.get("genre_counts", {})
    if gc:
        L("| Rank | Genre | # Movies |")
        L("|------|-------|----------|")
        for i, (g, c) in enumerate(list(gc.items())[:12], 1):
            L(f"| {i} | {g} | {c:,} |")
        L("")

    for p in genre_res.get("plots", [])[:1]:
        if Path(p).exists():
            L(f"![Most Common Genres]({rel(p)})")
            L("")

    L("### 3.2 Average Ratings by Genre")
    L("")
    avg_tmdb = genre_res.get("genre_avg_tmdb", {})
    avg_imdb = genre_res.get("genre_avg_imdb", {})
    all_genres = sorted(set(list(avg_tmdb.keys()) + list(avg_imdb.keys())))
    if all_genres:
        L("| Genre | Avg TMDB Rating | Avg IMDb Rating |")
        L("|-------|----------------|----------------|")
        for g in all_genres:
            t = f"{avg_tmdb[g]:.2f}" if g in avg_tmdb else "—"
            i = f"{avg_imdb[g]:.2f}" if g in avg_imdb else "—"
            L(f"| {g} | {t} | {i} |")
        L("")

    for p in genre_res.get("plots", [])[1:2]:
        if Path(p).exists():
            L(f"![Average Ratings by Genre]({rel(p)})")
            L("")

    L("---")
    L("")

    # ── 4. Financial Analysis ────────────────────────────────────────── #
    L("## 4. Financial Analysis")
    L("")

    fin_n = financial_res.get("fin_n", 0)
    if fin_n:
        br = financial_res.get("budget_rev_r")
        bp = financial_res.get("budget_rev_pvalue")

        if br and br > 0.7:
            fin_interp = ("The **strong log-scale correlation** confirms that higher "
                          "production budgets are a reliable — though far from guaranteed "
                          "— predictor of box-office returns.")
        elif br and br > 0.4:
            fin_interp = ("The **moderate correlation** (log scale) suggests budget is "
                          "one factor among many; marketing, release timing, and franchise "
                          "brand all play significant roles.")
        else:
            fin_interp = "Budget alone is a weak predictor of revenue in this dataset."

        L(f"Financial data was available for **{fin_n:,} movies**.")
        L("")
        L("### 4.1 Budget vs Revenue")
        L("")
        L(f"Pearson *r* = **{flt(br)}** (log scale) &nbsp;|&nbsp; "
          f"*p* = {flt(bp, 4)} &nbsp;|&nbsp; *n* = {fin_n:,}")
        L("")
        L(fin_interp)
        L("")

        for p in financial_res.get("plots", []):
            if Path(p).exists():
                L(f"![Financial Analysis]({rel(p)})")
                L("")

        L("### 4.2 Top 10 Most Profitable Movies")
        L("")
        top_p = financial_res.get("top_profitable", [])
        if top_p:
            L("| # | Title | Budget | Revenue | Profit | ROI |")
            L("|---|-------|--------|---------|--------|-----|")
            for i, row in enumerate(top_p, 1):
                L(f"| {i} | {str(row.get('title',''))[:35]} "
                  f"| {fmt_m(row.get('budget'))} "
                  f"| {fmt_m(row.get('revenue'))} "
                  f"| {fmt_m(row.get('profit'))} "
                  f"| {fmt_roi(row.get('roi'))} |")
            L("")
    else:
        L("> ⚠️ No budget/revenue data was available in this dataset — "
          "financial analysis was skipped.")
        L("")

    L("---")
    L("")

    # ── 5. Temporal Analysis ─────────────────────────────────────────── #
    L("## 5. Temporal Analysis")
    L("")
    L(f"**{temp_n:,} movies** had a valid release year and fell within the "
      f"1950–2025 analysis window.")
    L("")

    top_years = temporal_res.get("top_productive_years", [])
    if top_years:
        L("### 5.1 Most Productive Years")
        L("")
        L("| Rank | Year | Movies Released |")
        L("|------|------|----------------|")
        for i, row in enumerate(top_years, 1):
            L(f"| {i} | {int(row['release_year'])} | {int(row['count']):,} |")
        L("")

    for p in temporal_res.get("plots", []):
        if Path(p).exists():
            L(f"![Temporal Analysis]({rel(p)})")
            L("")

    L("The upper panel shows annual output volume; the lower panel shows "
      "5-point smoothed average ratings per platform, revealing whether "
      "perceived quality has shifted over decades.")
    L("")
    L("---")
    L("")

    # ── 6. Interesting Insights & Patterns ───────────────────────────── #
    L("## 6. Interesting Insights & Patterns")
    L("")

    insights: List[str] = []

    # Rating convergence / divergence
    tmdb_mean = rating_res.get("tmdb_mean")
    imdb_mean = rating_res.get("imdb_mean")
    if tmdb_mean and imdb_mean:
        diff = abs(tmdb_mean - imdb_mean)
        higher = "TMDB" if tmdb_mean > imdb_mean else "IMDb"
        insights.append(
            f"**Platform rating gap:** {higher} averages {diff:.2f} points higher "
            f"than the other platform (TMDB mean = {tmdb_mean:.2f}, "
            f"IMDb mean = {imdb_mean:.2f}). TMDB's community skews toward "
            f"enthusiast audiences who tend to rate movies they actively seek out, "
            f"while IMDb's larger general audience tempers extremes."
        )

    # Genre dominance
    if gc:
        top_g, top_c = next(iter(gc.items())), list(gc.values())[0]
        insights.append(
            f"**Genre dominance:** {list(gc.keys())[0]} is the single most common genre "
            f"tag ({list(gc.values())[0]:,} movies). The top three genres account for "
            f"{sum(list(gc.values())[:3]):,} of {genre_res.get('total_genre_tags',0):,} "
            f"total genre tags, reflecting TMDB's genre taxonomy heavily weighting "
            f"broad commercial categories."
        )

    # Highest-rated genre
    if avg_tmdb:
        best_g = max(avg_tmdb, key=avg_tmdb.get)
        insights.append(
            f"**Best-rated genre (TMDB):** {best_g} leads with an average rating of "
            f"{avg_tmdb[best_g]:.2f} / 10. Niche or prestige genres often outscore "
            f"mass-market ones because their smaller, dedicated audiences self-select."
        )

    # Financial outliers
    top_p = financial_res.get("top_profitable", [])
    if top_p:
        top_movie = top_p[0]
        insights.append(
            f"**Highest profit:** *{top_movie.get('title','Unknown')}* earned "
            f"{fmt_m(top_movie.get('profit'))} in profit "
            f"({fmt_roi(top_movie.get('roi'))} ROI). Blockbuster franchises dominate "
            f"the top-profit list, underscoring the outsized returns of IP-driven cinema."
        )

    # Correlation interpretation
    if r_val is not None:
        insights.append(
            f"**Rating agreement:** With r = {r_val:.3f}, TMDB and IMDb ratings are "
            f"{'strongly' if r_val > 0.7 else 'moderately' if r_val > 0.4 else 'weakly'} "
            f"correlated. Movies where the two platforms diverge most are often "
            f"culturally divisive releases or older titles with small IMDb vote counts."
        )

    # Missing Metascore
    if meta_n < len(df) * 0.5:
        pct = meta_n / len(df) * 100
        insights.append(
            f"**Metascore coverage:** Only {meta_n:,} of {len(df):,} movies "
            f"({pct:.0f}%) have a Metascore. OMDb only returns Metascores for titles "
            f"reviewed on Metacritic, which skews toward wide-release studio films and "
            f"omits most foreign, indie, and limited-release titles."
        )

    for insight in insights:
        L(f"- {insight}")
        L("")

    L("---")
    L("")

    # ── 7. Challenges Encountered & Solutions ────────────────────────── #
    L("## 7. Challenges Encountered & Solutions")
    L("")
    challenges = [
        (
            "**IMDb HTML scraping unreliable**",
            "IMDb's frontend is JavaScript-heavy and actively blocks automated "
            "requests. Early attempts with `requests` + `BeautifulSoup` returned "
            "empty or challenge pages regardless of User-Agent. "
            "**Solution:** Replaced the scraper entirely with the OMDb API "
            "(`omdb_collector.py`), which provides the same three fields "
            "(IMDb rating, vote count, Metascore) via a clean JSON endpoint, "
            "eliminating fragile HTML parsing and robots.txt concerns.",
        ),
        (
            "**OMDb missing titles (`Error getting data`)**",
            "A small number of IMDb IDs returned `Response: False` from OMDb "
            "(e.g. `tt26735622`). These are typically very new or unreleased films "
            "not yet indexed by OMDb. "
            "**Solution:** The collector catches the error per-record, logs it, "
            "and stores `None` for all three fields. The processor then treats "
            "these as valid rows with missing IMDb data rather than dropping them.",
        ),
        (
            "**TMDB `imdb_id` field sometimes absent**",
            "TMDB's `/movie/{id}` endpoint does not always populate `imdb_id` — "
            "this is common for non-English or direct-to-streaming titles. "
            "**Solution:** The merge in `data_processor.py` is a LEFT join, so "
            "TMDB-only rows are kept with NaN IMDb columns rather than silently dropped.",
        ),
        (
            "**Budget and revenue stored as 0 for unknown values**",
            "TMDB encodes unknown financial figures as `0` rather than `null`, "
            "which would corrupt any financial analysis if left in place. "
            "**Solution:** `clean_data()` explicitly replaces `0` in `budget` and "
            "`revenue` with `pd.NA` and logs the count of replacements.",
        ),
        (
            "**NaN serialisation in JSON output**",
            "Python's `json.dump` raises a `ValueError` on `float('nan')` by default, "
            "and pandas `NA` is not JSON-serialisable. "
            "**Solution:** `save_processed_data()` iterates every cell before "
            "serialising, converting all `pd.NA`, `float('nan')`, and pandas NA "
            "sentinel types to `None`, which serialises cleanly as JSON `null`.",
        ),
    ]
    for title, body in challenges:
        L(f"### {title}")
        L("")
        L(body)
        L("")

    L("---")
    L("")

    # ── 8. Limitations & Future Improvements ─────────────────────────── #
    L("## 8. Limitations & Future Improvements")
    L("")
    L("### Current Limitations")
    L("")
    limitations = [
        ("**OMDb free-tier cap**",
         "The free OMDb key allows 1,000 requests/day, limiting the dataset to "
         "~1,000 movies per daily run. A paid key (unlimited) or batched daily runs "
         "would be needed to scale to tens of thousands of titles."),
        ("**TMDB popularity bias**",
         "Movies are collected via TMDB's popularity-sorted endpoint, which "
         "over-represents English-language mainstream releases and under-represents "
         "foreign, documentary, and art-house cinema."),
        ("**Metascore sparsity**",
         "Metacritic only reviews a subset of wide releases, so Metascore is missing "
         "for the majority of the dataset, limiting any critic-vs-audience "
         "comparison analysis."),
        ("**Static snapshot**",
         "Ratings on both platforms change over time as new votes are cast. "
         "This dataset reflects a single point-in-time collection and does not "
         "capture rating drift for older films as they gain or lose cultural relevance."),
        ("**No user-level data**",
         "Only aggregate ratings are available; individual review text, demographic "
         "breakdowns, or time-series rating histories would enable richer NLP and "
         "longitudinal analyses."),
    ]
    for title, body in limitations:
        L(f"- {title} — {body}")
        L("")

    L("### Future Improvements")
    L("")
    improvements = [
        "Collect **review text** from OMDb or a separate source to enable "
        "sentiment analysis alongside numeric ratings.",
        "Add a **Rotten Tomatoes Tomatometer** field (via RapidAPI) to enable "
        "a three-way critic/audience/aggregator comparison.",
        "Schedule **weekly re-collection** to build a longitudinal rating "
        "time-series and detect films whose reputation improves or declines post-release.",
        "Expand to **TV series** using the TMDB `/tv` endpoint for a richer "
        "cross-media comparison.",
        "Integrate **streaming availability** data (e.g. JustWatch API) to "
        "analyze whether platform exclusivity correlates with ratings or audience size.",
        "Apply **regression modelling** (budget, runtime, genre, release month) "
        "to predict box-office revenue and identify the strongest predictors.",
    ]
    for imp in improvements:
        L(f"- {imp}")
        L("")

    L("---")
    L("")
    L("*Data sources: TMDB API (`api_collector.py`) · OMDb API (`omdb_collector.py`) "
      "· Processed by `data_processor.py` · Analyzed by `analyze_data.py` · UCLA STAT 418*")
    L("")

    # ------------------------------------------------------------------ #
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Markdown report saved → %s", report_path)
    return report_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  Movie Dataset Analysis")
    print("=" * 55)

    print("\nLoading processed data...")
    df = load_processed_data()

    print("\n[1/4] Rating analysis...")
    rating_res = analyze_ratings(df)
    r = rating_res.get("rating_correlation")
    print(f"      TMDB–IMDb correlation: r = {r:.3f}" if r else "      Insufficient data for correlation.")

    print("\n[2/4] Genre analysis...")
    genre_res = analyze_genres(df)
    top_genre = next(iter(genre_res.get("genre_counts", {})), "N/A")
    print(f"      {genre_res.get('unique_genres', 0)} unique genres — most common: {top_genre}")

    print("\n[3/4] Financial analysis...")
    financial_res = analyze_financials(df)
    fin_n = financial_res.get("fin_n", 0)
    if fin_n:
        print(f"      {fin_n:,} movies with budget+revenue data  "
              f"(r = {financial_res.get('budget_rev_r', 'N/A'):.3f})")
    else:
        print("      No financial data available.")

    print("\n[4/4] Temporal analysis...")
    temporal_res = analyze_temporal(df)
    print(f"      {temporal_res.get('temporal_n', 0):,} movies with release year data")

    print("\nGenerating REPORT.md...")
    pdf_path = generate_report(df, rating_res, genre_res, financial_res, temporal_res)

    print("\n" + "=" * 55)
    print("  Outputs")
    print("=" * 55)
    all_plots = (
        rating_res.get("plots", [])
        + genre_res.get("plots", [])
        + financial_res.get("plots", [])
        + temporal_res.get("plots", [])
    )
    for p in all_plots:
        print(f"  Plot   → {p}")
    print(f"  Report → {pdf_path}")
    print(f"  Log    → {LOG_DIR}/analyze_data.log")
    print()


if __name__ == "__main__":
    main()