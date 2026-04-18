# YouTube Virality Product (rq2_project)

This project analyzes YouTube trending data, trains a simple virality model, and provides a Streamlit app for exploration and prediction.

Structure:

- `analysis.py` — load raw CSVs from `../raw_data`, clean and engineer features, save `data/processed.csv`.
- `model.py` — trains a RandomForest classifier to predict whether a video is "viral" (top 20% by views). Saves model to `models/viral_model.joblib`.
- `app.py` — Streamlit app with Dashboard and Virality Predictor pages.
- `requirements.txt` — Python dependencies.

Quick start (from project root `d:/hackthon1`):

1. Create and activate a Python environment (recommended Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r rq2_project/requirements.txt
```

2. Prepare processed data:

```powershell
python rq2_project/analysis.py
```

3. Train model:

```powershell
python rq2_project/model.py
```

4. Run Streamlit app:

```powershell
streamlit run rq2_project/app.py
```

Notes:
- The scripts expect a `raw_data` folder at `d:/hackthon1/raw_data` containing `*_Trending.csv` files (already present in your workspace).
- If you want NLP title suggestions, we can add a simple keyword extractor and a title-suggester in a follow-up.
