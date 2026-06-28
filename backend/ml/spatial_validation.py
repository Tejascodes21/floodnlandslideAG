"""
Spatial Cross-Validation Module
=================================
Provides region-grouped splitting to prevent spatial data leakage.
Ensures models are tested on geographical areas completely unseen during training.
"""

import numpy as np
import pandas as pd
import logging
from typing import Generator, Tuple, List
from sklearn.model_selection import GroupKFold

logger = logging.getLogger("geoshield.ml.spatial_split")


class SpatialCV:
    """
    Implements GroupKFold cross-validation based on district or state
    to prevent spatial data leakage.
    """
    
    def __init__(self, n_splits: int = 5, group_col: str = "state"):
        self.n_splits = n_splits
        self.group_col = group_col
        self.gkf = GroupKFold(n_splits=n_splits)
        
    def split(self, df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Generator[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], None, None]:
        """
        Generates train/validation splits of feature matrices and labels.
        
        Yields:
            X_train, y_train, X_val, y_val
        """
        # Ensure group column exists
        group_col = self.group_col
        if group_col not in df.columns:
            # Fallback to district if state is absent
            group_col = "district" if "district" in df.columns else None
            
        if group_col is None:
            logger.warning("No grouping column (state/district) found. Falling back to default random K-Fold.")
            # Mock groups randomly if missing
            groups = np.random.randint(0, self.n_splits, size=len(df))
        else:
            groups = df[group_col].values
            
        X = df[feature_cols].values
        y = df[target_col].values
        
        logger.info(f"Running Spatial Cross Validation ({self.n_splits} splits) grouped by '{group_col}'...")
        
        for fold, (train_idx, val_idx) in enumerate(self.gkf.split(X, y, groups)):
            # Verify no group overlap
            train_groups = set(df.iloc[train_idx][group_col].unique())
            val_groups = set(df.iloc[val_idx][group_col].unique())
            overlap = train_groups.intersection(val_groups)
            
            if overlap:
                logger.warning(f"Fold {fold}: Spatial leak detected! Overlapping groups: {overlap}")
            else:
                logger.info(f"Fold {fold}: Split successful. Unseen groups in validation: {len(val_groups)}")
                
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            yield X_train, y_train, X_val, y_val
            
    def get_train_test_split(self, df: pd.DataFrame, feature_cols: List[str], target_col: str, test_size: float = 0.25) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[int], List[int]]:
        """
        Produces a single spatial holdout train/test split.
        Ensures that test districts are entirely distinct from train districts.
        """
        group_col = self.group_col if self.group_col in df.columns else ("district" if "district" in df.columns else None)
        
        if group_col is None:
            # Fallback to standard stratified split
            from sklearn.model_selection import train_test_split
            X = df[feature_cols].values
            y = df[target_col].values
            indices = np.arange(len(df))
            X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
                X, y, indices, test_size=test_size, random_state=42, stratify=y
            )
            return X_train, X_test, y_train, y_test, list(idx_train), list(idx_test)
            
        # Group-based split
        unique_groups = df[group_col].unique()
        np.random.seed(42)
        np.random.shuffle(unique_groups)
        
        # Select test groups up to target size fraction
        n_test_groups = max(1, int(len(unique_groups) * test_size))
        test_groups = unique_groups[:n_test_groups]
        
        is_test = df[group_col].isin(test_groups)
        is_train = ~is_test
        
        idx_train = df[is_train].index.tolist()
        idx_test = df[is_test].index.tolist()
        
        X = df[feature_cols].values
        y = df[target_col].values
        
        X_train, X_test = X[idx_train], X[idx_test]
        y_train, y_test = y[idx_train], y[idx_test]
        
        logger.info(f"Spatial Holdout Split complete: {len(X_train)} train, {len(X_test)} test. "
                    f"Test groups (unseen in training): {list(test_groups)}")
                    
        return X_train, X_test, y_train, y_test, idx_train, idx_test
