# Movie Dataset — Analysis Report

> **Course:** UCLA STAT 418  | **Sources:** TMDB API · OMDb API  | **Generated:** 2026-04-27 23:17 UTC

---

## Table of Contents

1. [Data Collection Summary](#1-data-collection-summary)
2. [Rating Analysis](#2-rating-analysis)
3. [Genre Analysis](#3-genre-analysis)
4. [Financial Analysis](#4-financial-analysis)
5. [Temporal Analysis](#5-temporal-analysis)
6. [Interesting Insights & Patterns](#6-interesting-insights--patterns)
7. [Challenges Encountered & Solutions](#7-challenges-encountered--solutions)
8. [Limitations & Future Improvements](#8-limitations--future-improvements)

---

## 1. Data Collection Summary

### Sources

| Source | Script | What it provides |
|--------|--------|-----------------|
| **TMDB API** | `api_collector.py` | Title, genres, runtime, release date, cast, director, budget, revenue, TMDB rating & vote count |
| **OMDb API** | `omdb_collector.py` | IMDb rating, number of user votes, Metascore (Metacritic) |
| **Processed** | `data_processor.py` | Merged & cleaned dataset: deduplication, range validation, derived profit/ROI |

### Dataset at a Glance

| Metric | Count |
|--------|-------|
| Total movies in processed dataset | **50** |
| Movies with TMDB rating | 50 |
| Movies with IMDb rating (via OMDb) | 37 |
| Movies with Metascore | 32 |
| Movies with budget & revenue data | 30 |
| Movies with valid release year | 22 |
| Unique genres | 17 |

The two APIs were joined on the `imdb_id` field, which TMDB includes in its movie detail endpoint. This ensured a deterministic, lossless key with no fuzzy title-matching required.

---

## 2. Rating Analysis

### 2.1 TMDB vs IMDb Correlation

Pearson *r* = **0.918** &nbsp;|&nbsp; *p* = 0.0000 &nbsp;|&nbsp; *n* = 37

This **strong positive correlation** indicates both platforms largely agree on movie quality — high-rated films on TMDB tend to be high-rated on IMDb as well.

![TMDB vs IMDb Rating Correlation](plots/01_rating_correlation.png)

### 2.2 Rating Distribution Summary

| Metric | TMDB | IMDb |
|--------|------|------|
| Mean   | 6.42 | 6.46 |
| Median | 6.79 | 6.50 |
| Std Dev | 1.75 | 1.42 |
| n      | 50 | 37 |

![Rating Distributions](plots/02_rating_distributions.png)

---

## 3. Genre Analysis

The dataset spans **17 unique genres** across 136 total genre tags. Because TMDB assigns multiple genres per movie, these counts reflect per-genre-tag occurrences rather than per-movie counts.

### 3.1 Top 12 Most Common Genres

| Rank | Genre | # Movies |
|------|-------|----------|
| 1 | Adventure | 17 |
| 2 | Thriller | 15 |
| 3 | Action | 15 |
| 4 | Comedy | 13 |
| 5 | Horror | 13 |
| 6 | Science Fiction | 10 |
| 7 | Drama | 9 |
| 8 | Crime | 8 |
| 9 | Mystery | 8 |
| 10 | Fantasy | 7 |
| 11 | Animation | 7 |
| 12 | Family | 6 |

![Most Common Genres](plots/03_genre_counts.png)

### 3.2 Average Ratings by Genre

| Genre | Avg TMDB Rating | Avg IMDb Rating |
|-------|----------------|----------------|
| Action | 6.61 | 7.44 |
| Adventure | 6.85 | 7.32 |
| Animation | 6.46 | 7.22 |
| Comedy | 6.81 | 6.52 |
| Crime | 6.37 | 5.86 |
| Drama | 6.97 | 6.74 |
| Family | 7.27 | 6.90 |
| Fantasy | 6.63 | 7.83 |
| Horror | 5.69 | 5.43 |
| Mystery | 6.41 | 6.03 |
| Science Fiction | 7.18 | 6.73 |
| Thriller | 6.39 | 5.62 |

![Average Ratings by Genre](plots/04_genre_ratings.png)

---

## 4. Financial Analysis

Financial data was available for **30 movies**.

### 4.1 Budget vs Revenue

Pearson *r* = **0.942** (log scale) &nbsp;|&nbsp; *p* = 0.0000 &nbsp;|&nbsp; *n* = 30

The **strong log-scale correlation** confirms that higher production budgets are a reliable — though far from guaranteed — predictor of box-office returns.

![Financial Analysis](plots/05_financial_analysis.png)

### 4.2 Top 10 Most Profitable Movies

| # | Title | Budget | Revenue | Profit | ROI |
|---|-------|--------|---------|--------|-----|
| 1 | Spider-Man: No Way Home | $200M | $1,922M | $1,722M | 8.61× |
| 2 | Zootopia 2 | $150M | $1,868M | $1,718M | 11.45× |
| 3 | The Super Mario Bros. Movie | $100M | $1,361M | $1,261M | 12.61× |
| 4 | Avatar: Fire and Ash | $350M | $1,490M | $1,140M | 3.26× |
| 5 | The Lord of the Rings: The Return o | $94M | $1,119M | $1,025M | 10.90× |
| 6 | The Lord of the Rings: The Fellowsh | $93M | $871M | $778M | 8.37× |
| 7 | The Super Mario Galaxy Movie | $110M | $831M | $721M | 6.56× |
| 8 | Demon Slayer: Kimetsu no Yaiba Infi | $20M | $733M | $713M | 35.65× |
| 9 | Interstellar | $165M | $747M | $582M | 3.52× |
| 10 | Project Hail Mary | $200M | $613M | $413M | 2.07× |

---

## 5. Temporal Analysis

**22 movies** had a valid release year and fell within the 1950–2025 analysis window.

### 5.1 Most Productive Years

| Rank | Year | Movies Released |
|------|------|----------------|
| 1 | 2025 | 10 |
| 2 | 2023 | 2 |
| 3 | 2000 | 1 |
| 4 | 2001 | 1 |
| 5 | 2002 | 1 |

![Temporal Analysis](plots/06_temporal_analysis.png)

The upper panel shows annual output volume; the lower panel shows 5-point smoothed average ratings per platform, revealing whether perceived quality has shifted over decades.

---

## 6. Interesting Insights & Patterns

- **Platform rating gap:** IMDb averages 0.04 points higher than the other platform (TMDB mean = 6.42, IMDb mean = 6.46). TMDB's community skews toward enthusiast audiences who tend to rate movies they actively seek out, while IMDb's larger general audience tempers extremes.

- **Genre dominance:** Adventure is the single most common genre tag (17 movies). The top three genres account for 47 of 136 total genre tags, reflecting TMDB's genre taxonomy heavily weighting broad commercial categories.

- **Best-rated genre (TMDB):** Family leads with an average rating of 7.27 / 10. Niche or prestige genres often outscore mass-market ones because their smaller, dedicated audiences self-select.

- **Highest profit:** *Spider-Man: No Way Home* earned $1,722M in profit (8.61× ROI). Blockbuster franchises dominate the top-profit list, underscoring the outsized returns of IP-driven cinema.

- **Rating agreement:** With r = 0.918, TMDB and IMDb ratings are strongly correlated. Movies where the two platforms diverge most are often culturally divisive releases or older titles with small IMDb vote counts.

---

## 7. Challenges Encountered & Solutions

### **IMDb HTML scraping unreliable**

IMDb's frontend is JavaScript-heavy and actively blocks automated requests. Early attempts with `requests` + `BeautifulSoup` returned empty or challenge pages regardless of User-Agent. **Solution:** Replaced the scraper entirely with the OMDb API (`omdb_collector.py`), which provides the same three fields (IMDb rating, vote count, Metascore) via a clean JSON endpoint, eliminating fragile HTML parsing and robots.txt concerns.

### **OMDb missing titles (`Error getting data`)**

A small number of IMDb IDs returned `Response: False` from OMDb (e.g. `tt26735622`). These are typically very new or unreleased films not yet indexed by OMDb. **Solution:** The collector catches the error per-record, logs it, and stores `None` for all three fields. The processor then treats these as valid rows with missing IMDb data rather than dropping them.

### **TMDB `imdb_id` field sometimes absent**

TMDB's `/movie/{id}` endpoint does not always populate `imdb_id` — this is common for non-English or direct-to-streaming titles. **Solution:** The merge in `data_processor.py` is a LEFT join, so TMDB-only rows are kept with NaN IMDb columns rather than silently dropped.

### **Budget and revenue stored as 0 for unknown values**

TMDB encodes unknown financial figures as `0` rather than `null`, which would corrupt any financial analysis if left in place. **Solution:** `clean_data()` explicitly replaces `0` in `budget` and `revenue` with `pd.NA` and logs the count of replacements.

### **NaN serialisation in JSON output**

Python's `json.dump` raises a `ValueError` on `float('nan')` by default, and pandas `NA` is not JSON-serialisable. **Solution:** `save_processed_data()` iterates every cell before serialising, converting all `pd.NA`, `float('nan')`, and pandas NA sentinel types to `None`, which serialises cleanly as JSON `null`.

---

## 8. Limitations & Future Improvements

### Current Limitations

- **OMDb free-tier cap** — The free OMDb key allows 1,000 requests/day, limiting the dataset to ~1,000 movies per daily run. A paid key (unlimited) or batched daily runs would be needed to scale to tens of thousands of titles.

- **TMDB popularity bias** — Movies are collected via TMDB's popularity-sorted endpoint, which over-represents English-language mainstream releases and under-represents foreign, documentary, and art-house cinema.

- **Metascore sparsity** — Metacritic only reviews a subset of wide releases, so Metascore is missing for the majority of the dataset, limiting any critic-vs-audience comparison analysis.

- **Static snapshot** — Ratings on both platforms change over time as new votes are cast. This dataset reflects a single point-in-time collection and does not capture rating drift for older films as they gain or lose cultural relevance.

- **No user-level data** — Only aggregate ratings are available; individual review text, demographic breakdowns, or time-series rating histories would enable richer NLP and longitudinal analyses.

### Future Improvements

- Collect **review text** from OMDb or a separate source to enable sentiment analysis alongside numeric ratings.

- Add a **Rotten Tomatoes Tomatometer** field (via RapidAPI) to enable a three-way critic/audience/aggregator comparison.

- Schedule **weekly re-collection** to build a longitudinal rating time-series and detect films whose reputation improves or declines post-release.

- Expand to **TV series** using the TMDB `/tv` endpoint for a richer cross-media comparison.

- Integrate **streaming availability** data (e.g. JustWatch API) to analyze whether platform exclusivity correlates with ratings or audience size.

- Apply **regression modelling** (budget, runtime, genre, release month) to predict box-office revenue and identify the strongest predictors.

---

*Data sources: TMDB API (`api_collector.py`) · OMDb API (`omdb_collector.py`) · Processed by `data_processor.py` · Analyzed by `analyze_data.py` · UCLA STAT 418*
