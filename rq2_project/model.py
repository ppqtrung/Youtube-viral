"""Train a calibrated HistGradientBoosting virality classifier.

Features used (all available pre-publish):
  - numeric: title_length, title_word_count, title_caps_ratio, number_of_tags,
             publish_hour, publish_dow, title_has_number, title_has_question,
             title_has_exclamation
  - categorical: category, country

Pipeline:
  1. OneHotEncode categoricals.
  2. Fit a HistGradientBoostingClassifier (fast, strong on tabular data).
  3. Wrap with CalibratedClassifierCV (isotonic) so predicted probabilities
     are meaningful.

Target: top-25% views within the dataset == "viral".
We save the pipeline AND a metrics bundle (AUC, CV scores, permutation
feature importance, top viral keywords) alongside the model so the app's
"Model Insights" page can display them without recomputing.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed.csv"
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "viral_model.joblib"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
KEYWORDS_PATH = MODELS_DIR / "viral_keywords.json"

NUM_FEATURES = [
    "title_length", "title_word_count", "title_caps_ratio",
    "title_has_number", "title_has_question", "title_has_exclamation",
    "number_of_tags", "publish_hour", "publish_dow",
]
CAT_FEATURES = ["category", "country"]
FEATURES = NUM_FEATURES + CAT_FEATURES

_WORD_RE = re.compile(r"[a-z]{3,}")
_STOPWORDS = frozenset("""
the a an and or but if then this that these those with without from for of to in on at by is are was were be been being has have had do does did not no i you he she it we they as so than too very more most much such any some own all each other both own
""".split())


def load_processed(path: Path | None = None) -> pd.DataFrame:
    path = path or DATA_PATH
    cols = FEATURES + ["views", "title"]
    return pd.read_csv(path, usecols=cols)


def make_label(df: pd.DataFrame, top_pct: float = 0.25) -> pd.Series:
    threshold = df["views"].quantile(1 - top_pct)
    return (df["views"] >= threshold).astype(int)


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_FEATURES),
        ],
        remainder="passthrough",
    )
    base_clf = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.08,
        max_depth=8,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
    )
    calibrated = CalibratedClassifierCV(base_clf, method="isotonic", cv=3)
    return Pipeline([("pre", preprocessor), ("clf", calibrated)])


def extract_viral_keywords(df: pd.DataFrame, y: pd.Series, top_n: int = 40) -> list[dict]:
    """Words that are disproportionately common in viral titles.

    Score: lift = P(word | viral) / P(word) computed with Laplace smoothing.
    Returned sorted by lift, filtered to words appearing ≥50 times.
    """
    total_counts: Counter[str] = Counter()
    viral_counts: Counter[str] = Counter()
    y_arr = y.to_numpy()
    for title, is_viral in zip(df["title"].fillna("").astype(str).str.lower(), y_arr):
        words = {w for w in _WORD_RE.findall(title) if w not in _STOPWORDS}
        total_counts.update(words)
        if is_viral:
            viral_counts.update(words)

    n_total = len(df)
    n_viral = int(y_arr.sum())
    rows = []
    for w, c in total_counts.items():
        if c < 50:
            continue
        p_w = (c + 1) / (n_total + 2)
        p_w_given_viral = (viral_counts[w] + 1) / (n_viral + 2)
        lift = p_w_given_viral / p_w
        rows.append({"word": w, "count": c, "viral_count": viral_counts[w],
                     "lift": round(float(lift), 3)})
    rows.sort(key=lambda r: r["lift"], reverse=True)
    return rows[:top_n]


def _feature_names_after_transform(pipe: Pipeline) -> list[str]:
    pre: ColumnTransformer = pipe.named_steps["pre"]
    cat_step: OneHotEncoder = pre.named_transformers_["cat"]
    cat_names = list(cat_step.get_feature_names_out(CAT_FEATURES))
    return cat_names + NUM_FEATURES


def build_and_train() -> Path:
    df = load_processed()
    print(f"Training rows: {len(df):,}")

    y = make_label(df, top_pct=0.25)
    X = df[FEATURES]
    print(f"Positive class share: {y.mean():.3f}")

    # Cross-validated AUC on the full dataset (5-fold).
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fresh = build_pipeline()
    cv_aucs = cross_val_score(fresh, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    print(f"CV ROC AUC: {cv_aucs.mean():.3f} ± {cv_aucs.std():.3f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    probs = pipe.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    auc = roc_auc_score(y_test, probs)
    ap = average_precision_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)
    report = classification_report(y_test, preds, digits=3, output_dict=True)

    print(classification_report(y_test, preds, digits=3))
    print(f"Test ROC AUC : {auc:.3f}")
    print(f"Test PR AUC  : {ap:.3f}")
    print(f"Brier score  : {brier:.4f} (lower is better, perfectly calibrated = 0)")

    # Permutation importance on a sample (full test set is too slow with 10 repeats).
    print("Computing permutation feature importance…")
    sample_idx = np.random.RandomState(42).choice(len(X_test), size=min(3000, len(X_test)), replace=False)
    perm = permutation_importance(
        pipe, X_test.iloc[sample_idx], y_test.iloc[sample_idx],
        n_repeats=5, random_state=42, scoring="roc_auc", n_jobs=-1,
    )
    feat_imp = sorted(
        [{"feature": f, "importance": round(float(v), 5)}
         for f, v in zip(FEATURES, perm.importances_mean)],
        key=lambda r: r["importance"], reverse=True,
    )
    for row in feat_imp:
        print(f"  {row['feature']:<25s} {row['importance']:+.4f}")

    # Calibration curve data (10 bins).
    from sklearn.calibration import calibration_curve
    frac_pos, mean_pred = calibration_curve(y_test, probs, n_bins=10, strategy="quantile")
    calibration = [{"bin_mean_pred": round(float(m), 4),
                    "bin_frac_pos": round(float(f), 4)}
                   for m, f in zip(mean_pred, frac_pos)]

    # Viral keywords from title (for NLP hints in the app).
    print("Extracting viral keywords from titles…")
    full_titles = load_processed()
    keywords = extract_viral_keywords(full_titles, make_label(full_titles), top_n=40)

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps({
        "cv_roc_auc_mean": round(float(cv_aucs.mean()), 4),
        "cv_roc_auc_std": round(float(cv_aucs.std()), 4),
        "test_roc_auc": round(float(auc), 4),
        "test_pr_auc": round(float(ap), 4),
        "brier_score": round(float(brier), 4),
        "test_report": report,
        "feature_importance": feat_imp,
        "calibration_curve": calibration,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "positive_rate": round(float(y.mean()), 4),
    }, indent=2))
    KEYWORDS_PATH.write_text(json.dumps(keywords, indent=2))

    print(f"Saved model -> {MODEL_PATH}")
    print(f"Saved metrics -> {METRICS_PATH}")
    print(f"Saved keywords -> {KEYWORDS_PATH}")
    return MODEL_PATH


if __name__ == "__main__":
    build_and_train()
