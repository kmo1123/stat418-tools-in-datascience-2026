# Movie Data Pipeline
### UCLA STAT 418 — Data Collection & Analysis Assignment

An end-to-end data pipeline that collects movie data from two public APIs, merges and cleans the dataset, and produces statistical analyses with visualizations and a written report.

---

## Table of Contents

1. [Assignment Overview & Goals](#1-assignment-overview--goals)
2. [Project Structure](#2-project-structure)
3. [Dependencies & Requirements](#3-dependencies--requirements)
4. [Setup Instructions](#4-setup-instructions)
5. [How to Run the Pipeline](#5-how-to-run-the-pipeline)
6. [Data Sources & Collection Methods](#6-data-sources--collection-methods)
7. [Ethical Considerations](#7-ethical-considerations)
8. [Known Limitations](#8-known-limitations)

---

## 1. Assignment Overview & Goals

This project demonstrates a full data science pipeline applied to the movie industry:

- **Collect** structured movie data from two independent public APIs
- **Merge** the datasets on a shared key (`imdb_id`) and clean the result
- **Analyse** ratings, genres, financials, and release trends
- **Report** findings in a self-contained Markdown document with embedded visualizations

The pipeline answers four core analytical questions:

| # | Analysis | Questions |
|---|----------|-----------|
| 1 | **Rating Analysis** | How correlated are TMDB and IMDb ratings? How are ratings distributed on each platform? |
| 2 | **Genre Analysis** | Which genres are most common? Which genres rate highest on each platform? |
| 3 | **Financial Analysis** | How strongly does budget predict revenue? Which movies were most profitable? |
| 4 | **Temporal Analysis** | How have ratings shifted over time? Which years were most productive? |

---

## 2. Project Structure

```
.
├── api_collector.py       # Step 1 — TMDB API collection
├── omdb_collector.py      # Step 2 — OMDb API collection
├── data_processor.py      # Step 3 — merge, clean, validate
├── analyze_data.py        # Step 4 — analysis, plots, REPORT.md
├── run_pipeline.py        # Orchestrator — runs all four steps in order
├── requirements.txt       # Python dependencies
├── .env                   # API keys (never committed — see setup)
│
├── data/
│   ├── raw/
│   │   ├── tmdb/          # Per-movie TMDB JSON + all_movies.json
│   │   └── omdb/          # Per-movie OMDb JSON + all_omdb.json
│   ├── processed/
│   │   ├── movies.csv     # Final merged & cleaned dataset
│   │   └── movies.json    # Same dataset in JSON format
│   └── analysis/
│       └── plots/         # PNG visualizations (6 files)
│       └── REPORT.md      # Full analysis report with embedded plots
│
└── logs/
    ├── api_collector.log
    ├── omdb_collector.log
    ├── data_processor.log
    ├── analyze_data.log
    └── run_pipeline.log
```

---

## 3. Dependencies & Requirements

**Python 3.9 or higher** is required.

| Package | Version | Used by |
|---------|---------|---------|
| `requests` | ≥ 2.31.0 | `api_collector.py`, `omdb_collector.py` |
| `python-dotenv` | ≥ 1.0.0 | `api_collector.py`, `omdb_collector.py` |
| `pandas` | ≥ 2.0.0 | `data_processor.py`, `analyze_data.py` |
| `numpy` | ≥ 1.24.0 | `data_processor.py`, `analyze_data.py` |
| `matplotlib` | ≥ 3.7.0 | `analyze_data.py` |
| `seaborn` | ≥ 0.12.0 | `analyze_data.py` |
| `scipy` | ≥ 1.10.0 | `analyze_data.py` |
| `beautifulsoup4` | ≥ 4.12.0 | (retained as dependency) |
| `lxml` | ≥ 4.9.0 | (retained as dependency) |

All standard library modules (`json`, `logging`, `os`, `pathlib`, `subprocess`, `sys`, etc.) require no installation.

---

## 4. Setup Instructions

### 4.1 Clone or download the project

```bash
git clone <your-repo-url>
cd <project-folder>
```

### 4.2 Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4.3 Install dependencies

```bash
pip install -r requirements.txt
```

### 4.4 Obtain API keys

This project requires two free API keys:

**TMDB API key**
1. Create a free account at [https://www.themoviedb.org/signup](https://www.themoviedb.org/signup)
2. Go to **Settings → API → Create → Developer**
3. Copy your **API Read Access Token** (the long Bearer token) or the shorter **API Key (v3)**

**OMDb API key**
1. Register for a free key at [https://www.omdbapi.com/apikey.aspx](https://www.omdbapi.com/apikey.aspx)
2. Confirm your email — the key arrives by email
3. The free tier allows **1,000 requests per day**

### 4.5 Create a `.env` file

Create a file named `.env` in the project root (same folder as `run_pipeline.py`) and add your keys:

```env
TMDB_API_KEY=your_tmdb_api_key_here
OMDB_API_KEY=your_omdb_api_key_here
```

> ⚠️ **Never commit `.env` to version control.** Add it to `.gitignore`:
> ```bash
> echo ".env" >> .gitignore
> ```

---

## 5. How to Run the Pipeline

### Run the full pipeline (recommended)

```bash
python run_pipeline.py
```

This runs all four scripts in order and prints a timing summary at the end:

```
══════════════════════════════════════════════════════════
  Movie Data Pipeline  ·  2025-04-27 10:00 UTC
══════════════════════════════════════════════════════════

  Steps queued:
    1. api_collector       — Fetch movie metadata from the TMDB API
    2. omdb_collector      — Fetch IMDb ratings & Metascores from the OMDb API
    3. data_processor      — Merge, clean, and validate both datasets
    4. analyze_data        — Run analyses, generate plots, and write REPORT.md
```

### Resume from a specific step

```bash
# Re-run from data_processor onward (skip re-fetching data)
python run_pipeline.py --start 3

# Re-run only the analysis step
python run_pipeline.py --only 4
```

### Preview without executing

```bash
python run_pipeline.py --dry-run
```

### Run individual scripts directly

Each script can also be run on its own:

```bash
python api_collector.py               # collect TMDB data
python omdb_collector.py              # collect OMDb data
python data_processor.py              # merge and clean
python analyze_data.py                # analyze and report
```

`api_collector.py` and `omdb_collector.py` both accept optional CLI arguments:

```bash
# Scrape a specific number of movies (default: 50)
python api_collector.py --limit 100

# Pass specific IMDb IDs to omdb_collector
python omdb_collector.py --ids tt0111161 tt0068646
```

### Outputs

After a successful run you will find:

| Path | Contents |
|------|----------|
| `data/raw/tmdb/` | One JSON file per movie + `all_movies.json` |
| `data/raw/omdb/` | One JSON file per movie + `all_omdb.json` |
| `data/processed/movies.csv` | Final cleaned dataset (CSV) |
| `data/processed/movies.json` | Final cleaned dataset (JSON) |
| `data/analysis/plots/` | 6 PNG visualization files |
| `data/analysis/REPORT.md` | Full analysis report with embedded plots |
| `logs/` | One log file per script + `run_pipeline.log` |

---

## 6. Data Sources & Collection Methods

### TMDB (The Movie Database)

- **API docs:** [https://developer.themoviedb.org/docs](https://developer.themoviedb.org/docs)
- **Endpoint used:** `/movie/popular` (paginated) + `/movie/{id}` for detail + `/movie/{id}/credits` for cast/director
- **Fields collected:** title, original title, language, release date, runtime, status, overview, genres, TMDB rating, vote count, popularity score, budget, revenue, director, top 5 cast, production companies, and — critically — `imdb_id`
- **Collection method:** Authenticated REST API calls using a Bearer token stored in `.env`. Results are saved as individual JSON files per movie and combined into `all_movies.json`.

### OMDb (Open Movie Database)

- **API docs:** [https://www.omdbapi.com/](https://www.omdbapi.com/)
- **Endpoint used:** `/?i={imdb_id}&r=json` — lookup by IMDb ID
- **Fields collected:** IMDb rating (`imdbRating`), number of user votes (`imdbVotes`), and Metascore (`Metascore`)
- **Collection method:** The `imdb_id` values stored by `api_collector.py` are used as lookup keys, ensuring both datasets cover exactly the same set of movies. Results are saved per-movie and combined into `all_omdb.json`.
- **Join key:** Both datasets are merged in `data_processor.py` on the `imdb_id` field using a LEFT join, so every TMDB movie is retained even if its OMDb fetch failed.

### Data processing

`data_processor.py` performs the following cleaning steps before analysis:

- Drops rows missing `tmdb_id` or `title`
- Removes duplicate `tmdb_id` entries (keeps first)
- Parses `release_date` to datetime and extracts `release_year`
- Coerces all numeric columns and replaces out-of-range values with `NaN`
- Replaces TMDB's `0`-encoded unknown budget/revenue with `NaN`
- Derives `profit` and `roi` where both budget and revenue are known
- Standardizes string columns (strips whitespace, normalizes empty strings to `NaN`)

---

## 7. Ethical Considerations

### API terms of service
Both APIs are used strictly within their published terms:
- **TMDB** requires attribution and prohibits commercial use of the data without a separate agreement. This project is for academic use only.
- **OMDb** free tier is used within its 1,000 requests/day rate limit. No attempt is made to circumvent this limit.

### No web scraping
An earlier version of this project attempted to scrape IMDb HTML pages directly. This approach was abandoned because IMDb's `robots.txt` restricts automated access and their frontend actively blocks scrapers. The pipeline now uses the OMDb API exclusively for IMDb-sourced data, which is a sanctioned access method.

### Data minimization
Only aggregate, publicly available data is collected — ratings, vote counts, genre tags, and financial figures. No personal user data, review text, or individual voting records are accessed or stored.

### Academic use only
All collected data is used solely for this UCLA STAT 418 assignment. The dataset is not redistributed or used for commercial purposes.

---

## 8. Known Limitations

| Limitation | Detail |
|------------|--------|
| **OMDb free-tier cap** | 1,000 requests/day limits the dataset to ~1,000 movies per run. A paid OMDb key removes this cap. |
| **TMDB popularity bias** | Movies are fetched via TMDB's popularity-ranked endpoint, which over-represents English-language studio releases and under-represents foreign, indie, and documentary titles. |
| **Metascore sparsity** | Metacritic only reviews a subset of wide releases. Metascore is missing for the majority of movies in the dataset, limiting critic-vs-audience comparisons. |
| **OMDb missing titles** | Very new or unreleased films may not yet be indexed by OMDb and return `Error getting data`. These movies are retained in the dataset with `NaN` for all OMDb fields. |
| **Static snapshot** | Ratings on both platforms change as new votes are cast. This dataset reflects a single point-in-time collection and does not capture rating drift over time. |
| **Zero-encoded financials** | TMDB stores unknown budget and revenue as `0` rather than `null`. These are replaced with `NaN` during processing but may still cause undercounting of movies with genuine financial data. |
| **`imdb_id` gaps** | TMDB does not always populate `imdb_id` for non-English or direct-to-streaming titles. These movies are kept in the dataset but cannot be joined to OMDb data. |

---

*UCLA STAT 418 · Data sources: [TMDB](https://www.themoviedb.org/) and [OMDb](https://www.omdbapi.com/) · For academic use only*