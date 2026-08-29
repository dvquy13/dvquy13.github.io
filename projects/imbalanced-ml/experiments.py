"""Shared experiment grid for the imbalanced-ML study.

Runs the same six conditions (LR/LGBM x full/downsampled/balanced) across
whichever dataset is handed to it, over a 5-fold stratified CV split so
single-split noise doesn't get mistaken for a finding.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

import lightgbm as lgb


# ---------------------------------------------------------------------------
# Dataset loaders — each returns (X, y) with y a 0/1 Series.
# ---------------------------------------------------------------------------

def load_gmsc(data_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    import kagglehub

    dataset_path = kagglehub.dataset_download("brycecf/give-me-some-credit-dataset")
    csv_path = next(Path(dataset_path).glob("cs-training.csv"))
    df = pd.read_csv(csv_path, index_col=0)
    df = df.dropna(subset=["SeriousDlqin2yrs"])
    y = df["SeriousDlqin2yrs"].astype(int)
    X = df.drop(columns=["SeriousDlqin2yrs"])
    return X, y


def load_fraud(data_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    import kagglehub

    dataset_path = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
    csv_path = Path(dataset_path) / "creditcard.csv"
    df = pd.read_csv(csv_path)
    y = df["Class"].astype(int)
    X = df.drop(columns=["Class"])
    return X, y


def load_adult(data_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    from sklearn.datasets import fetch_openml

    data = fetch_openml("adult", version=2, as_frame=True, data_home=str(data_dir))
    df = data.frame
    y = (df["class"] == ">50K").astype(int)
    X = df.drop(columns=["class"])
    return X, y


def load_sparkov(data_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Simulated card-fraud transactions with raw (non-PCA) features — the
    counterpart to Fraud's PCA components, at a similarly severe imbalance.
    """
    import kagglehub

    dataset_path = Path(kagglehub.dataset_download("kartik2112/fraud-detection"))
    df = pd.concat(
        [pd.read_csv(dataset_path / "fraudTrain.csv"), pd.read_csv(dataset_path / "fraudTest.csv")],
        ignore_index=True,
    )

    trans_time = pd.to_datetime(df["trans_date_trans_time"])
    dob = pd.to_datetime(df["dob"])
    df["hour"] = trans_time.dt.hour
    df["age"] = (trans_time - dob).dt.days // 365

    keep_cols = [
        "category", "amt", "gender", "state", "city_pop", "job",
        "lat", "long", "merch_lat", "merch_long", "hour", "age",
    ]
    y = df["is_fraud"].astype(int)
    X = df[keep_cols]

    # Subsample to keep runtime in line with the other datasets; stratified
    # so the 0.58% fraud rate carries over unchanged.
    X, _, y, _ = train_test_split(X, y, train_size=300_000, stratify=y, random_state=0)
    return X.reset_index(drop=True), y.reset_index(drop=True)


DATASETS = {
    "GMSC": load_gmsc,
    "Fraud": load_fraud,
    "Adult": load_adult,
    "Sparkov": load_sparkov,
}


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def _cols(X: pd.DataFrame) -> tuple[list[str], list[str]]:
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]
    return num_cols, cat_cols


def make_lr_pipeline(X: pd.DataFrame, random_state: int, class_weight=None) -> Pipeline:
    num_cols, cat_cols = _cols(X)
    transformers = []
    if num_cols:
        transformers.append((
            "num",
            Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", RobustScaler())]),
            num_cols,
        ))
    if cat_cols:
        transformers.append((
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore")),
            ]),
            cat_cols,
        ))
    pre = ColumnTransformer(transformers)
    return Pipeline([
        ("pre", pre),
        ("lr", LogisticRegression(max_iter=2000, random_state=random_state, class_weight=class_weight)),
    ])


def _as_lgbm_frame(X: pd.DataFrame) -> pd.DataFrame:
    _, cat_cols = _cols(X)
    if not cat_cols:
        return X
    X = X.copy()
    for c in cat_cols:
        X[c] = X[c].astype("category")
    return X


def fit_lgbm(X_fit, y_fit, X_es, y_es, random_state: int, **kwargs) -> lgb.LGBMClassifier:
    def ap_metric(y_true, y_pred):
        return "ap", average_precision_score(y_true, y_pred), True

    callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=-1)]
    m = lgb.LGBMClassifier(
        n_estimators=2000,
        random_state=random_state,
        verbose=-1,
        num_threads=1,
        metric="None",
        **kwargs,
    )
    m.fit(X_fit, y_fit, eval_set=[(X_es, y_es)], eval_metric=ap_metric, callbacks=callbacks)
    return m


# ---------------------------------------------------------------------------
# One fold's worth of the six conditions
# ---------------------------------------------------------------------------

def run_fold(X: pd.DataFrame, y: pd.Series, train_idx, val_idx, fold: int) -> list[dict]:
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    # LR's downsample: independent of LGBM's early-stopping split below, since
    # LR never evaluates against that held-out set.
    pos_idx = y_train[y_train == 1].index
    neg_idx = y_train[y_train == 0].index
    neg_sampled = np.random.RandomState(fold).choice(neg_idx, size=len(pos_idx), replace=False)
    ds_idx = np.concatenate([pos_idx, neg_sampled])
    X_train_ds, y_train_ds = X_train.loc[ds_idx], y_train.loc[ds_idx]

    rows = []

    def add(model_family, strategy, scores, best_iter=None):
        rows.append({
            "fold": fold,
            "model": model_family,
            "strategy": strategy,
            "AP": average_precision_score(y_val, scores),
            "ROC-AUC": roc_auc_score(y_val, scores),
            "best_iter": best_iter,
        })

    lr_full = make_lr_pipeline(X_train, fold).fit(X_train, y_train)
    add("LR", "full", lr_full.predict_proba(X_val)[:, 1])

    lr_ds = make_lr_pipeline(X_train_ds, fold).fit(X_train_ds, y_train_ds)
    add("LR", "downsampled", lr_ds.predict_proba(X_val)[:, 1])

    lr_bal = make_lr_pipeline(X_train, fold, class_weight="balanced").fit(X_train, y_train)
    add("LR", "balanced", lr_bal.predict_proba(X_val)[:, 1])

    X_train_lgb = _as_lgbm_frame(X_train)
    X_val_lgb = _as_lgbm_frame(X_val)

    # Carve the early-stopping set out first, so it's guaranteed disjoint from
    # every LGBM variant's training data. Downsampling for LGBM then draws
    # from X_tr only (not the full X_train) — otherwise the downsampled
    # training set can include rows also used to judge its own early stopping.
    X_tr, X_es, y_tr, y_es = train_test_split(
        X_train_lgb, y_train, test_size=0.2, stratify=y_train, random_state=fold
    )
    n_pos, n_neg = int(y_train.sum()), int((y_train == 0).sum())

    m_full = fit_lgbm(X_tr, y_tr, X_es, y_es, fold)
    add("LGBM", "full", m_full.predict_proba(X_val_lgb)[:, 1], m_full.best_iteration_)

    m_bal = fit_lgbm(X_tr, y_tr, X_es, y_es, fold, scale_pos_weight=n_neg / n_pos)
    add("LGBM", "balanced", m_bal.predict_proba(X_val_lgb)[:, 1], m_bal.best_iteration_)

    pos_idx_lgb = y_tr[y_tr == 1].index
    neg_idx_lgb = y_tr[y_tr == 0].index
    neg_sampled_lgb = np.random.RandomState(fold).choice(neg_idx_lgb, size=len(pos_idx_lgb), replace=False)
    ds_idx_lgb = np.concatenate([pos_idx_lgb, neg_sampled_lgb])
    X_tr_ds_lgb, y_tr_ds_lgb = X_tr.loc[ds_idx_lgb], y_tr.loc[ds_idx_lgb]

    m_ds = fit_lgbm(X_tr_ds_lgb, y_tr_ds_lgb, X_es, y_es, fold)
    add("LGBM", "downsampled", m_ds.predict_proba(X_val_lgb)[:, 1], m_ds.best_iteration_)

    return rows


def run_dataset(name: str, data_dir: Path, n_splits: int = 5, random_state: int = 0) -> pd.DataFrame:
    X, y = DATASETS[name](data_dir)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    rows = []
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        rows.extend(run_fold(X, y, train_idx, val_idx, fold))
    df = pd.DataFrame(rows)
    df.insert(0, "dataset", name)
    return df
