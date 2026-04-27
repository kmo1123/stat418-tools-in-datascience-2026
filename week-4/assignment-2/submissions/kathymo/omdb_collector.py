"""
omdb_collector.py
-----------------
Fetches IMDb rating, number of user reviews, and Metascore from the
OMDb API (https://www.omdbapi.com/) for every movie collected by
api_collector.py.

IMDb IDs are read from the TMDB JSON files produced by api_collector.py,
so both datasets always cover the exact same movies.

Data source:
  - OMDb API (https://www.omdbapi.com/) — requires a free API key.
    Set OMDB_API_KEY in your .env file (or as an environment variable).

"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
import os

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# ---------------------------------------------------------------------------
# Paths — mirrors the layout used by api_collector.py
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR  = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
OMDB_DIR = DATA_DIR / "raw" / "omdb"   # where OMDb JSON files go
TMDB_DIR = DATA_DIR / "raw" / "tmdb"   # read-only: source of IMDb IDs

LOG_DIR.mkdir(parents=True, exist_ok=True)
OMDB_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename=str(LOG_DIR / "omdb_collector.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OMDB_BASE_URL = "https://www.omdbapi.com/"
REQUEST_DELAY = 0.25   # seconds between requests (OMDb free tier: 1 000 req/day)


# ---------------------------------------------------------------------------
# Module-level convenience functions (mirror the old scraper's public API)
# ---------------------------------------------------------------------------

def fetch_movie_data(imdb_id: str) -> Dict:
    """
    Fetch IMDb rating, user review count, and Metascore for one title.

    Args:
        imdb_id: IMDb title ID, e.g. 'tt0111161'.

    Returns:
        Dict with keys: imdb_id, rating, num_reviews, metascore,
        fetched_at, error (None on success).
    """
    return OMDbCollector().fetch_movie_data(imdb_id)


def fetch_multiple_movies(imdb_ids: List[str]) -> List[Dict]:
    """
    Fetch OMDb data for a list of IMDb IDs and persist results to JSON.

    Each result is saved to data/raw/omdb/<imdb_id>.json and a combined
    all_omdb.json is written at the end.

    Args:
        imdb_ids: List of IMDb title IDs, e.g. ['tt0111161', 'tt0068646'].

    Returns:
        List of result dicts (one per ID, including those that errored).
    """
    return OMDbCollector().fetch_multiple_movies(imdb_ids)


# ---------------------------------------------------------------------------
# Helper: load IMDb IDs from the TMDB JSON files made by api_collector.py
# (unchanged from the original web_scraper.py)
# ---------------------------------------------------------------------------

def load_imdb_ids_from_tmdb(limit: int = 50) -> List[str]:
    """
    Read the imdb_id field from TMDB JSON files in data/raw/tmdb/.

    Tries all_movies.json first (one read), then individual files.

    Args:
        limit: Maximum number of IDs to return (default 50).

    Returns:
        List of IMDb ID strings, e.g. ['tt0111161', 'tt0068646', ...]
    """
    ids: List[str] = []

    combined = TMDB_DIR / "all_movies.json"
    if combined.exists():
        try:
            with combined.open(encoding="utf-8") as fh:
                movies = json.load(fh)
            for movie in movies:
                iid = movie.get("imdb_id")
                if iid and str(iid).startswith("tt"):
                    ids.append(iid)
                    if len(ids) >= limit:
                        break
            if ids:
                logger.info("Loaded %d IMDb IDs from %s", len(ids), combined)
                return ids
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Could not read %s: %s -- trying individual files.", combined, exc
            )

    for path in sorted(TMDB_DIR.glob("[0-9]*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                record = json.load(fh)
            iid = record.get("imdb_id")
            if iid and str(iid).startswith("tt"):
                ids.append(iid)
                if len(ids) >= limit:
                    break
        except (json.JSONDecodeError, OSError):
            continue

    if ids:
        logger.info("Loaded %d IMDb IDs from individual TMDB files.", len(ids))
    else:
        logger.error(
            "No IMDb IDs found in %s. Run api_collector.py first.", TMDB_DIR
        )
    return ids


# ---------------------------------------------------------------------------
# OMDbCollector class
# ---------------------------------------------------------------------------

class OMDbCollector:
    """
    Retrieves IMDb rating, user review count, and Metascore via the
    OMDb API using an IMDb ID as the lookup key — so every record
    aligns directly with the TMDB dataset from api_collector.py.

    OMDb returns JSON, so no HTML parsing is needed.
    """

    def __init__(self, delay: float = REQUEST_DELAY) -> None:
        """
        Initialise the collector.

        Args:
            delay: Seconds to wait between API requests (default 0.25).
        """
        if not OMDB_API_KEY:
            raise EnvironmentError(
                "OMDB_API_KEY is not set. Add it to your .env file:\n"
                "  OMDB_API_KEY=your_key_here\n"
                "Get a free key at https://www.omdbapi.com/apikey.aspx"
            )

        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        logger.info("OMDbCollector initialised (delay=%.2fs)", self.delay)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fetch_movie_data(self, imdb_id: str) -> Dict:
        """
        Call the OMDb API for a single IMDb ID and extract the three
        fields of interest.

        Args:
            imdb_id: IMDb title ID, e.g. 'tt0111161'.

        Returns:
            Dict with keys:
              imdb_id     -- the input ID (matches TMDB imdb_id field)
              rating      -- float [0-10] or None
              num_reviews -- int or None   (imdbVotes from OMDb)
              metascore   -- int [0-100] or None
              fetched_at  -- ISO-8601 UTC timestamp
              error       -- error string, or None on success
        """
        time.sleep(self.delay)

        params = {
            "i":      imdb_id,
            "apikey": OMDB_API_KEY,
            "r":      "json",
        }

        try:
            response = self.session.get(OMDB_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()

            if payload.get("Response") == "False":
                raise ValueError(f"OMDb error: {payload.get('Error', 'unknown')}")

            data = {
                "imdb_id":     imdb_id,
                "rating":      self._parse_rating(payload.get("imdbRating")),
                "num_reviews": self._parse_votes(payload.get("imdbVotes")),
                "metascore":   self._parse_metascore(payload.get("Metascore")),
                "fetched_at":  datetime.now(timezone.utc).isoformat(),
                "error":       None,
            }

            logger.info("Fetched %s — rating=%s  votes=%s  metascore=%s",
                        imdb_id, data["rating"], data["num_reviews"], data["metascore"])
            return data

        except Exception as exc:
            logger.error("Error fetching %s: %s", imdb_id, exc)
            return {
                "imdb_id":     imdb_id,
                "rating":      None,
                "num_reviews": None,
                "metascore":   None,
                "fetched_at":  datetime.now(timezone.utc).isoformat(),
                "error":       str(exc),
            }

    def fetch_multiple_movies(self, imdb_ids: List[str]) -> List[Dict]:
        """
        Fetch OMDb data for a list of IMDb IDs and persist results.

        Each result is saved to data/raw/omdb/<imdb_id>.json.
        A combined all_omdb.json is written at the end.

        Args:
            imdb_ids: List of IMDb title IDs.

        Returns:
            List of result dicts.
        """
        total = len(imdb_ids)
        logger.info("Starting OMDb fetch for %d title(s).", total)
        results: List[Dict] = []

        for idx, imdb_id in enumerate(imdb_ids, start=1):
            print(f"Fetching {idx}/{total}: {imdb_id}")
            data = self.fetch_movie_data(imdb_id)
            results.append(data)
            self._save_result(imdb_id, data)

        combined_path = OMDB_DIR / "all_omdb.json"
        with combined_path.open("w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)

        successful = sum(1 for r in results if r.get("error") is None)
        logger.info(
            "Fetch complete — %d/%d succeeded -> %s",
            successful, total, combined_path,
        )
        return results

    # ------------------------------------------------------------------
    # Private parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_rating(value: Optional[str]) -> Optional[float]:
        """'8.3' -> 8.3, 'N/A' or None -> None."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_votes(value: Optional[str]) -> Optional[int]:
        """'1,234,567' -> 1234567, 'N/A' or None -> None."""
        try:
            return int(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_metascore(value: Optional[str]) -> Optional[int]:
        """'74' -> 74, 'N/A' or None -> None."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _save_result(imdb_id: str, data: Dict) -> None:
        """Save one result to data/raw/omdb/<imdb_id>.json."""
        path = OMDB_DIR / f"{imdb_id}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        logger.debug("Saved -> %s", path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the OMDb collector from the command line.

    By default reads IMDb IDs from the TMDB JSON files produced by
    api_collector.py so both datasets cover the exact same movies.
    Pass --ids to supply specific IDs instead.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch IMDb ratings, vote counts, and Metascores via the OMDb API."
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        metavar="IMDB_ID",
        help="Specific IMDb IDs to fetch (overrides reading from TMDB files).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max movies to read from TMDB data (default: 50).",
    )
    args = parser.parse_args()

    if args.ids:
        imdb_ids = args.ids
        logger.info("Using %d IMDb IDs from --ids argument.", len(imdb_ids))
    else:
        imdb_ids = load_imdb_ids_from_tmdb(limit=args.limit)

    if not imdb_ids:
        print(
            "\n  No IMDb IDs found.\n"
            f"    Make sure api_collector.py has been run so JSON files\n"
            f"    exist in {TMDB_DIR}\n"
            "    Or supply IDs directly:  python omdb_collector.py --ids tt0111161 tt0068646"
        )
        return

    print(f"Fetching OMDb data for {len(imdb_ids)} title(s)...")
    collector  = OMDbCollector()
    results    = collector.fetch_multiple_movies(imdb_ids)
    successful = sum(1 for r in results if r.get("error") is None)

    print(f"\n  {successful}/{len(results)} fetched successfully.")
    print(f"    Individual JSON files -> {OMDB_DIR}/<id>.json")
    print(f"    Combined dataset      -> {OMDB_DIR}/all_omdb.json")
    print(f"    Log                   -> {LOG_DIR}/omdb_collector.log")


if __name__ == "__main__":
    main()      