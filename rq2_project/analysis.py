"""Load raw YouTube trending CSVs, clean, engineer features, save processed.csv.

Enriches the dataset with title NLP features (word count, ALL-CAPS ratio,
has_number, has_question, has_exclamation) that feed into the ML model.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd


YOUTUBE_CATEGORY_MAP = {
    1: "Film & Animation", 2: "Autos & Vehicles", 10: "Music",
    15: "Pets & Animals", 17: "Sports", 18: "Short Movies",
    19: "Travel & Events", 20: "Gaming", 21: "Videoblogging",
    22: "People & Blogs", 23: "Comedy", 24: "Entertainment",
    25: "News & Politics", 26: "Howto & Style", 27: "Education",
    28: "Science & Technology", 29: "Nonprofits & Activism",
    30: "Movies", 31: "Anime/Animation", 32: "Action/Adventure",
    33: "Classics", 34: "Comedy", 35: "Documentary", 36: "Drama",
    37: "Family", 38: "Foreign", 39: "Horror", 40: "Sci-Fi/Fantasy",
    41: "Thriller", 42: "Shorts", 43: "Shows", 44: "Trailers",
}

_WORD_RE = re.compile(r"[A-Za-z]+")
_NUM_RE = re.compile(r"\d")


def find_raw_data_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    cand = root / "raw_data"
    if not cand.exists():
        raise FileNotFoundError(f"raw_data directory not found at {cand}")
    return cand


def load_all_country_csvs(raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = Path(raw_dir) if raw_dir else find_raw_data_dir()
    files = sorted(raw_dir.glob("*_Trending.csv"))
    if not files:
        raise FileNotFoundError(f"No *_Trending.csv files in {raw_dir}")

    usecols = [
        "video_id", "title", "channel_title", "views", "likes",
        "publish_time", "category_id", "tags", "comments",
    ]
    dfs = []
    for f in files:
        df = pd.read_csv(f, usecols=lambda c: c in usecols)
        df["country"] = f.stem.split("_")[0]
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def _parse_tags(t) -> list[str]:
    if pd.isna(t):
        return []
    s = str(t).strip()
    if not s or s.lower() == "[none]":
        return []
    sep = "|" if "|" in s else ","
    return [p.strip().lower() for p in re.split(re.escape(sep) + r"|;", s) if p.strip()]


def _title_features(title: str) -> dict:
    """Compute NLP features for a title in a single pass."""
    if not isinstance(title, str):
        title = "" if pd.isna(title) else str(title)
    title = title.strip()
    words = _WORD_RE.findall(title)
    caps_words = sum(1 for w in words if len(w) >= 2 and w.isupper())
    return {
        "title_length": len(title),
        "title_word_count": len(words),
        "title_caps_ratio": (caps_words / len(words)) if words else 0.0,
        "title_has_number": int(bool(_NUM_RE.search(title))),
        "title_has_question": int("?" in title),
        "title_has_exclamation": int("!" in title),
    }


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["category_id"] = pd.to_numeric(df.get("category_id"), errors="coerce")
    df["category"] = df["category_id"].map(YOUTUBE_CATEGORY_MAP).fillna("Unknown")

    df["publish_time"] = pd.to_datetime(df.get("publish_time"), errors="coerce", utc=True)
    df["publish_hour"] = df["publish_time"].dt.hour.fillna(0).astype(int)
    df["publish_dow"] = df["publish_time"].dt.dayofweek.fillna(0).astype(int)

    for col in ["views", "likes", "comments"]:
        df[col] = pd.to_numeric(df.get(col), errors="coerce").fillna(0).astype("int64")

    df["number_of_tags"] = df["tags"].apply(_parse_tags).str.len().astype(int)

    df["title"] = df["title"].fillna("").astype(str)
    tf = df["title"].apply(_title_features).apply(pd.Series)
    df = pd.concat([df, tf], axis=1)

    df["like_ratio"] = np.where(df["views"] > 0, df["likes"] / df["views"], 0.0)
    df["comment_ratio"] = np.where(df["views"] > 0, df["comments"] / df["views"], 0.0)
    df["like_ratio"] = df["like_ratio"].clip(0, 1)
    df["comment_ratio"] = df["comment_ratio"].clip(0, 1)

    df = df[df["views"] > 0].reset_index(drop=True)

    keep = [
        "video_id", "title", "channel_title", "country",
        "category", "category_id",
        "publish_hour", "publish_dow",
        "number_of_tags",
        "title_length", "title_word_count", "title_caps_ratio",
        "title_has_number", "title_has_question", "title_has_exclamation",
        "views", "likes", "comments", "like_ratio", "comment_ratio", "tags",
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep]


def save_processed(df: pd.DataFrame, out_path: Path | None = None) -> Path:
    if out_path is None:
        out = Path(__file__).resolve().parents[1] / "data"
        out.mkdir(exist_ok=True)
        out_path = out / "processed.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    raw_df = load_all_country_csvs()
    print(f"Loaded {len(raw_df):,} raw rows")
    clean = clean_and_engineer(raw_df)
    print(f"After cleaning: {len(clean):,} rows, categories: {clean['category'].nunique()}")
    path = save_processed(clean)
    print(f"Saved processed data -> {path}")


if __name__ == "__main__":
    main()
