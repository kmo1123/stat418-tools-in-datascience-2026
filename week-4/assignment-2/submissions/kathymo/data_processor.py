"""
data_processor.py
-----------------
Loads raw TMDB and OMDb data, merges on IMDb ID, cleans and validates,
then saves processed output as CSV and JSON.

Data sources (read-only):
  - data/raw/tmdb/all_movies.json  — produced by api_collector.py
  - data/raw/omdb/all_omdb.json    — produced by omdb_collector.py
"""

import json
import logging
import math
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Paths — same BASE_DIR pattern as api_collector.py and omdb_collector.py
# ---------------------------------------------------------------------------

BASE_DIR      = Path(__file__).resolve().parent

LOG_DIR       = BASE_DIR / "logs"
DATA_DIR      = BASE_DIR / "data"
TMDB_DIR      = DATA_DIR / "raw" / "tmdb"
OMDB_DIR      = DATA_DIR / "raw" / "omdb"   # was: imdb
PROCESSED_DIR = DATA_DIR / "processed"

LOG_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename=str(LOG_DIR / "data_processor.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_COLS = ["tmdb_id", "title"]

NUMERIC_RANGES: Dict[str, Tuple[float, float]] = {
    "tmdb_rating":    (0.0, 10.0),
    "imdb_rating":    (0.0, 10.0),
    "metascore":      (0.0, 100.0),
    "runtime":        (1.0, 600.0),
    "tmdb_vote_count": (0.0, float("inf")),
    "num_reviews":    (0.0, float("inf")),
    "budget":         (0.0, float("inf")),
    "revenue":        (0.0, float("inf")),
}


# ---------------------------------------------------------------------------
# 1. load_raw_data
# ---------------------------------------------------------------------------

def load_raw_data() -> Tuple[List[Dict], List[Dict]]:
    """
    Load raw JSON data from both sources into lists of dicts.

    Reads:
      - data/raw/tmdb/all_movies.json  (from api_collector.py)
      - data/raw/omdb/all_omdb.json    (from omdb_collector.py)

    Falls back to reading individual per-movie JSON files if the combined
    file is missing for either source.

    Returns:
        Tuple of (tmdb_records, omdb_records). Either list may be empty
        if the source files are not found, but an error is logged.

    Raises:
        FileNotFoundError: If the TMDB data directory does not exist at all.
    """
    tmdb_records = _load_tmdb()
    omdb_records = _load_omdb()
    logger.info(
        "Loaded %d TMDB records and %d OMDb records.",
        len(tmdb_records), len(omdb_records),
    )
    return tmdb_records, omdb_records


def _load_tmdb() -> List[Dict]:
    """Load TMDB records from all_movies.json or individual files."""
    combined = TMDB_DIR / "all_movies.json"
    if combined.exists():
        try:
            with combined.open(encoding="utf-8") as fh:
                data = json.load(fh)
            logger.info("Loaded %d TMDB records from %s", len(data), combined)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read %s: %s — trying individual files.", combined, exc)

    records: List[Dict] = []
    for path in sorted(TMDB_DIR.glob("[0-9]*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                records.append(json.load(fh))
        except (json.JSONDecodeError, OSError):
            continue
    if records:
        logger.info("Loaded %d TMDB records from individual files.", len(records))
    else:
        logger.error("No TMDB data found in %s. Run api_collector.py first.", TMDB_DIR)
    return records


def _load_omdb() -> List[Dict]:
    """Load OMDb records from all_omdb.json or individual files."""
    combined = OMDB_DIR / "all_omdb.json"
    if combined.exists():
        try:
            with combined.open(encoding="utf-8") as fh:
                data = json.load(fh)
            logger.info("Loaded %d OMDb records from %s", len(data), combined)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read %s: %s — trying individual files.", combined, exc)

    records: List[Dict] = []
    for path in sorted(OMDB_DIR.glob("tt*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                records.append(json.load(fh))
        except (json.JSONDecodeError, OSError):
            continue
    if records:
        logger.info("Loaded %d OMDb records from individual files.", len(records))
    else:
        logger.warning(
            "No OMDb data found in %s. Run omdb_collector.py first. "
            "Proceeding with TMDB data only.",
            OMDB_DIR,
        )
    return records


# ---------------------------------------------------------------------------
# 2. merge_data
# ---------------------------------------------------------------------------

def merge_data(tmdb_data: List[Dict], omdb_data: List[Dict]) -> pd.DataFrame:
    """
    Merge TMDB and OMDb records into a single DataFrame on imdb_id.

    TMDB records are flattened first (nested lists like genres and top_5_cast
    are converted to pipe-separated strings). The merge is a LEFT join so
    every TMDB movie is kept even if the OMDb fetch failed or returned no data.

    Args:
        tmdb_data: List of movie dicts from api_collector.py.
        omdb_data: List of fetch-result dicts from omdb_collector.py.

    Returns:
        Merged DataFrame. OMDb columns (imdb_rating, num_reviews, metascore)
        will be NaN for any movie whose OMDb fetch failed.
    """
    if not tmdb_data:
        logger.error("tmdb_data is empty — cannot build DataFrame.")
        return pd.DataFrame()

    # --- Flatten TMDB records ---
    tmdb_rows: List[Dict] = []
    for movie in tmdb_data:
        genres = movie.get("genres", [])
        genres_str = "|".join(genres) if isinstance(genres, list) else str(genres or "")

        companies = movie.get("production_companies", [])
        companies_str = "|".join(companies) if isinstance(companies, list) else str(companies or "")

        cast = movie.get("top_5_cast", [])
        if isinstance(cast, list):
            cast_str = "|".join(
                c.get("name", "") if isinstance(c, dict) else str(c)
                for c in cast
            )
        else:
            cast_str = str(cast or "")

        tmdb_rows.append({
            "tmdb_id":              movie.get("tmdb_id"),
            "imdb_id":              movie.get("imdb_id"),
            "title":                movie.get("title"),
            "original_title":       movie.get("original_title"),
            "original_language":    movie.get("original_language"),
            "release_date":         movie.get("release_date"),
            "runtime":              movie.get("runtime"),
            "status":               movie.get("status"),
            "overview":             movie.get("overview"),
            "genres":               genres_str,
            "tmdb_rating":          movie.get("tmdb_rating"),
            "tmdb_vote_count":      movie.get("tmdb_vote_count"),
            "tmdb_popularity":      movie.get("tmdb_popularity"),
            "budget":               movie.get("budget"),
            "revenue":              movie.get("revenue"),
            "director":             movie.get("director"),
            "top_5_cast":           cast_str,
            "production_companies": companies_str,
        })

    tmdb_df = pd.DataFrame(tmdb_rows)
    logger.info("TMDB DataFrame: %d rows × %d columns", *tmdb_df.shape)

    # --- Flatten OMDb records (keep only successful fetches) ---
    if omdb_data:
        omdb_rows: List[Dict] = []
        for rec in omdb_data:
            if rec.get("error"):
                logger.debug("Skipping errored OMDb record: %s", rec.get("imdb_id"))
                continue
            omdb_rows.append({
                "imdb_id":     rec.get("imdb_id"),
                "imdb_rating": rec.get("rating"),
                "num_reviews": rec.get("num_reviews"),
                "metascore":   rec.get("metascore"),
            })
        omdb_df = pd.DataFrame(omdb_rows) if omdb_rows else pd.DataFrame(
            columns=["imdb_id", "imdb_rating", "num_reviews", "metascore"]
        )
        logger.info("OMDb DataFrame: %d rows × %d columns", *omdb_df.shape)
    else:
        omdb_df = pd.DataFrame(
            columns=["imdb_id", "imdb_rating", "num_reviews", "metascore"]
        )
        logger.warning("No OMDb data — merging TMDB only.")

    # --- Left join on imdb_id ---
    if not omdb_df.empty and "imdb_id" in omdb_df.columns:
        merged = tmdb_df.merge(omdb_df, on="imdb_id", how="left")
    else:
        merged = tmdb_df.copy()
        for col in ["imdb_rating", "num_reviews", "metascore"]:
            merged[col] = pd.NA

    matched = merged["imdb_rating"].notna().sum()
    logger.info(
        "Merged DataFrame: %d rows × %d columns (%d/%d matched on imdb_id).",
        merged.shape[0], merged.shape[1], matched, len(merged),
    )
    return merged


# ---------------------------------------------------------------------------
# 3. clean_data
# ---------------------------------------------------------------------------

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the merged DataFrame.

    Steps performed:
      1. Drop rows missing all required identifiers (tmdb_id, title)
      2. Remove exact duplicates on tmdb_id
      3. Standardise release_date to datetime; extract release_year
      4. Coerce all numeric columns to float/int
      5. Replace out-of-range values with NaN
      6. Replace 0 budget/revenue with NaN (TMDB stores 0 for "unknown")
      7. Derive profit and ROI where budget and revenue are both known
      8. Standardise string columns (strip whitespace, empty string → NaN)
      9. Log a missing-value summary

    Args:
        df: Merged DataFrame from merge_data().

    Returns:
        Cleaned DataFrame ready for analysis.
    """
    if df.empty:
        logger.warning("clean_data received an empty DataFrame — returning as-is.")
        return df

    original_len = len(df)

    # 1. Drop rows missing required identifiers
    df = df.dropna(subset=REQUIRED_COLS)
    if len(df) < original_len:
        logger.info(
            "Dropped %d rows missing required columns (%s).",
            original_len - len(df), REQUIRED_COLS,
        )

    # 2. Remove duplicates on tmdb_id (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["tmdb_id"], keep="first")
    dupes_removed = before_dedup - len(df)
    if dupes_removed:
        logger.info("Removed %d duplicate tmdb_id rows.", dupes_removed)

    # 3. Standardise dates
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year.astype("Int64")

    # 4. Coerce numeric columns
    for col in NUMERIC_RANGES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. Replace out-of-range values with NaN
    for col, (lo, hi) in NUMERIC_RANGES.items():
        if col in df.columns and hi != float("inf"):
            bad_mask = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
            if bad_mask.any():
                logger.warning(
                    "Setting %d out-of-range values to NaN in '%s'.",
                    bad_mask.sum(), col,
                )
                df.loc[bad_mask, col] = pd.NA

    # 6. Replace 0 budget/revenue with NaN (TMDB uses 0 for "unknown")
    for col in ["budget", "revenue"]:
        if col in df.columns:
            zeros = (df[col] == 0).sum()
            if zeros:
                df[col] = df[col].replace(0, pd.NA)
                logger.info(
                    "Replaced %d zero values with NaN in '%s'.", zeros, col
                )

    # 7. Derive profit and ROI
    if "budget" in df.columns and "revenue" in df.columns:
        both_known = df["budget"].notna() & df["revenue"].notna()
        df["profit"] = pd.NA
        df["roi"]    = pd.NA
        df.loc[both_known, "profit"] = (
            df.loc[both_known, "revenue"] - df.loc[both_known, "budget"]
        )
        nonzero_budget = both_known & (df["budget"] != 0)
        df.loc[nonzero_budget, "roi"] = (
            df.loc[nonzero_budget, "profit"] / df.loc[nonzero_budget, "budget"]
        ).round(4)
        logger.info("Derived profit/ROI for %d movies.", both_known.sum())

    # 8. Standardise string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        try:
            df[col] = df[col].astype(str).where(df[col].notna(), other=pd.NA)
            df[col] = df[col].str.strip()
            df[col] = df[col].replace("", pd.NA).replace("None", pd.NA).replace("nan", pd.NA)
        except Exception:
            pass

    # 9. Log missing-value summary
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if not missing.empty:
        pct = (missing / len(df) * 100).round(1)
        summary = "\n".join(
            f"    {col}: {cnt} missing ({pct[col]}%)"
            for col, cnt in missing.items()
        )
        logger.info("Missing value summary after cleaning:\n%s", summary)

    logger.info("Cleaning complete: %d rows × %d columns.", *df.shape)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. save_processed_data
# ---------------------------------------------------------------------------

def save_processed_data(df: pd.DataFrame, output_dir: str) -> None:
    """
    Save the processed DataFrame as both CSV and JSON.

    Files written:
      <output_dir>/movies.csv   — standard CSV, index excluded
      <output_dir>/movies.json  — records-oriented JSON

    Args:
        df:         Cleaned DataFrame from clean_data().
        output_dir: Directory path to write output files (created if absent).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    csv_path  = out / "movies.csv"
    json_path = out / "movies.json"

    # --- CSV ---
    df.to_csv(csv_path, index=False)
    logger.info("Saved CSV  → %s  (%d rows, %d columns)", csv_path, *df.shape)

    # --- JSON ---
    df_for_json = df.copy()

    for col in df_for_json.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df_for_json[col] = df_for_json[col].dt.strftime("%Y-%m-%d")

    raw_records = df_for_json.to_dict(orient="records")
    clean_records = []
    for row in raw_records:
        clean_row = {}
        for k, v in row.items():
            if v is pd.NA:
                clean_row[k] = None
            elif isinstance(v, float) and math.isnan(v):
                clean_row[k] = None
            elif hasattr(v, "__class__") and type(v).__name__ in ("NAType", "NaTType"):
                clean_row[k] = None
            else:
                clean_row[k] = v
        clean_records.append(clean_row)

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(clean_records, fh, indent=2, ensure_ascii=False, default=str)
    logger.info("Saved JSON → %s  (%d records)", json_path, len(clean_records))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full processing pipeline from the command line."""
    print("Loading raw data...")
    tmdb_data, omdb_data = load_raw_data()

    if not tmdb_data:
        print(
            "\n  No TMDB data found.\n"
            f"    Expected: {TMDB_DIR}/all_movies.json\n"
            "    Run api_collector.py first."
        )
        return

    print(f"  TMDB records : {len(tmdb_data)}")
    print(f"  OMDb records : {len(omdb_data)}")

    print("\nMerging data on imdb_id...")
    merged = merge_data(tmdb_data, omdb_data)
    print(f"  Merged shape : {merged.shape[0]} rows × {merged.shape[1]} columns")

    print("\nCleaning data...")
    cleaned = clean_data(merged)
    print(f"  Cleaned shape: {cleaned.shape[0]} rows × {cleaned.shape[1]} columns")

    print(f"\nSaving processed data to {PROCESSED_DIR}/")
    save_processed_data(cleaned, str(PROCESSED_DIR))

    print(f"\n  movies.csv  → {PROCESSED_DIR}/movies.csv")
    print(f"  movies.json → {PROCESSED_DIR}/movies.json")
    print(f"  Log         → {LOG_DIR}/data_processor.log")

    # Quick preview
    preview_cols = [c for c in
        ["title", "release_year", "tmdb_rating", "imdb_rating", "metascore", "genres"]
        if c in cleaned.columns
    ]
    print("\nSample (first 5 rows):")
    print(cleaned[preview_cols].head().to_string(index=False))


if __name__ == "__main__":
    main()