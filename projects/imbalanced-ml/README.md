# Imbalanced ML — pedagogical study

Companion notebook for a blog post on training ML models on imbalanced datasets. Uses the Kaggle Credit Card Fraud dataset (~0.17% positive rate).

## Setup

```bash
cd projects/imbalanced-ml
uv sync
```

## Kaggle credentials

The dataset is downloaded via `kagglehub`, which reads `KAGGLE_KEY` from the environment. The notebook loads the repo-root `.env` and maps `KAGGLE_API_TOKEN` (the newer `KGAT_...` token format) into `KAGGLE_KEY` automatically. No `kaggle.json` needed.

## Run

```bash
uv run jupyter lab notebook.ipynb
```

## Path to blog post

When the notebook is ready, it gets promoted into `posts/<slug>/` for Quarto to render as a blog post.
