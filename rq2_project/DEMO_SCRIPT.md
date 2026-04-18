# YouTube Viral Advisor — Demo Script
**Target duration:** 4 minutes  ·  **Word count:** ~550  ·  **Pace:** 130–140 wpm

---

## [0:00 – 0:30] — Problem Overview
*(Show the app homepage on screen)*

Every YouTuber faces the same question before hitting publish: *"Is this video actually going to reach people?"*

The problem is that most creators guess — wrong title length, wrong upload time, wrong number of tags.
We built **YouTube Viral Advisor** to turn that guesswork into a data-driven prediction,
using real trending data from 11 countries and 178,000 videos collected in 2026.

---

## [0:30 – 1:15] — Data & Solution
*(Navigate to Dashboard)*

The foundation is a multi-country trending dataset — US, UK, Japan, Brazil, and 7 more.
After cleaning, we have **178,267 videos** across **15 categories**,
each enriched with features we engineered ourselves:

- **Like ratio** and **comment ratio** — proxies for engagement quality
- **Title NLP features** — character length, word count, ALL-CAPS ratio, presence of numbers, questions, and exclamation marks
- **Timing features** — publish hour and day of week
- **Tag count** — how many tags the creator applied

The Dashboard gives creators an instant read of the landscape.
We can see that **Pets & Animals** dominates with a median of 1.2 million views,
that publishing around **13:00 to 21:00 UTC** consistently outperforms other windows,
and that viral videos cluster in a specific tag count and title length range — which we'll use in the predictor.

---

## [1:15 – 2:45] — Viral Advisor Demo
*(Navigate to Viral Advisor, fill in the form)*

This is the core product. A creator fills in four things they know *before* uploading:
title, category, number of tags, and publish time.

Let's test a real scenario: title is *"Top 10 BEST Moments of 2026"*, category **Entertainment**, 15 tags, publishing Friday at 15:00 UTC.

*(Click Analyze)*

The model returns a **virality score** — a calibrated probability that this video lands in the **top 25% of trending videos**.

Below the score, we get a **Benchmark Comparison table** — a side-by-side of the creator's inputs against what viral videos actually look like in the data.
Each row has a clear status indicator: green dot for on-target, red for off.

Then **Recommendations** — specific, data-driven suggestions.
Not generic tips, but insights like: *"Your title is 34 characters — viral videos use 34 to 66."*
Or: *"Try publishing at 13:00, 15:00, or 21:00 UTC."*

The **Viral Keywords panel** is where NLP comes in.
We computed a **lift score** for every word in the dataset — lift measures how much more likely a word is to appear in viral titles versus average titles.
Words already in the title are highlighted. The rest become suggestions.

Finally, a live **Views by Publish Hour chart** marks the creator's chosen hour in red so they can see exactly where they stand versus the average.

---

## [2:45 – 3:30] — Model Insights
*(Navigate to Model Insights)*

The Model Insights page is for full transparency.

The classifier is a **Histogram Gradient Boosting** model — faster and more accurate than a standard Random Forest on tabular data.
It's wrapped in a **Calibrated Cross-Validator** using isotonic regression, which ensures the percentages we show are statistically meaningful probabilities, not raw scores.

Key results on the held-out test set of **35,000 videos**:

- **ROC AUC: 0.853** — the model correctly ranks a viral video above a non-viral one 85% of the time
- **5-fold CV AUC: 0.797 ± 0.005** — stable across folds, no overfitting
- **Brier Score: 0.124** — well-calibrated probabilities

The **permutation feature importance chart** shows that **category** and **country** are the strongest predictors, followed by **tag count**, **title length**, and **publish hour** — which aligns with intuition and validates the feature engineering.

---

## [3:30 – 4:00] — Closing
*(Return to Viral Advisor)*

YouTube Viral Advisor turns a creator's pre-upload decisions into a single, explainable score — backed by 178,000 real trending videos, a calibrated ML model, and NLP keyword analysis.

The goal isn't to predict the future perfectly.
The goal is to give creators one honest data point before they publish —
so the next video isn't a guess.

---

*Total: ~555 words · Estimated duration: 3 min 58 sec at 140 wpm*
