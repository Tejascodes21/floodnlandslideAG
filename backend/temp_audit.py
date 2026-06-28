import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Ensure project root is in path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from backend.ml.data_ingestion import RealDataIngestionPipeline
from backend.ml.feature_engineering import feature_engineer

# V1 synthetic dataset
np.random.seed(42)
ns = 2500
lat = np.random.uniform(15.0, 30.0, ns)
lon = np.random.uniform(70.0, 95.0, ns)
elevation = np.random.uniform(5.0, 1800.0, ns)
slope = np.clip(np.random.uniform(0.5, 45.0, ns) * (1.0 + (elevation / 1800.0) * 0.5), 0.5, 45.0)
ndwi = np.random.uniform(-0.8, 0.6, ns)
ndvi = np.random.uniform(-0.1, 0.85, ns)
rain_24h = np.random.exponential(scale=25.0, size=ns)
rain_72h = rain_24h + np.random.exponential(scale=35.0, size=ns)
soil_moisture = np.clip(20.0 + (rain_72h * 0.15) + (ndvi * 30.0) + np.random.normal(0, 5, ns), 5.0, 95.0)
sar_backscatter = np.where(ndwi > 0.1, -22.0 + ndwi * 3.0, -12.0 + (slope / 45.0) * 4.0 + np.random.normal(0, 1.5, ns))
flood_score = (
    (rain_24h > 50.0).astype(float) * 0.25 +
    (ndwi > 0.05).astype(float) * 0.15 +
    (elevation < 400.0).astype(float) * 0.15 +
    (soil_moisture > 70.0).astype(float) * 0.15 +
    (rain_72h > 100.0).astype(float) * 0.10
)
landslide_score = (
    (slope > 20.0).astype(float) * 0.25 +
    (soil_moisture > 60.0).astype(float) * 0.15 +
    (rain_72h > 100.0).astype(float) * 0.15 +
    (ndvi < 0.3).astype(float) * 0.15 +
    (elevation > 500.0).astype(float) * 0.10
)
flood_occurred = (flood_score >= np.percentile(flood_score, 75)).astype(int)
landslide_occurred = (landslide_score >= np.percentile(landslide_score, 75)).astype(int)
df_v1 = pd.DataFrame({
    'lat': lat, 'lon': lon, 'elevation': elevation, 'slope': slope,
    'ndwi': ndwi, 'ndvi': ndvi, 'rain_24h': rain_24h, 'rain_72h': rain_72h,
    'soil_moisture': soil_moisture, 'sar_backscatter': sar_backscatter,
    'flood_occurred': flood_occurred, 'landslide_occurred': landslide_occurred
})
print('=== V1 dataset audit ===')
print('shape', df_v1.shape)
print('duplicates', df_v1.duplicated().sum())
print('target distribution flood', df_v1['flood_occurred'].value_counts().to_dict())
print('target distribution landslide', df_v1['landslide_occurred'].value_counts().to_dict())
print('features corr flood top')
print(df_v1.corr()['flood_occurred'].abs().sort_values(ascending=False).head(12))
print('features corr landslide top')
print(df_v1.corr()['landslide_occurred'].abs().sort_values(ascending=False).head(12))

X = df_v1[['lat', 'lon', 'elevation', 'slope', 'ndwi', 'ndvi', 'rain_24h', 'rain_72h', 'soil_moisture', 'sar_backscatter']].values
yf = df_v1['flood_occurred'].values
yl = df_v1['landslide_occurred'].values
X_train, X_test, y_f_train, y_f_test = train_test_split(X, yf, test_size=0.2, random_state=42)
_, _, y_l_train, y_l_test = train_test_split(X, yl, test_size=0.2, random_state=42)
print('train/test sizes', X_train.shape, X_test.shape)

clf = DecisionTreeClassifier(max_depth=5, random_state=42)
clf.fit(X_train, y_f_train)
print('DT flood train acc', clf.score(X_train, y_f_train), 'test acc', clf.score(X_test, y_f_test))

# Simple threshold parser for feature separability
for target in ['flood_occurred', 'landslide_occurred']:
    y = df_v1[target].values
    best = (None, None, 0.0)
    for c in ['lat', 'lon', 'elevation', 'slope', 'ndwi', 'ndvi', 'rain_24h', 'rain_72h', 'soil_moisture', 'sar_backscatter']:
        xs = df_v1[c].values
        for thr in np.linspace(xs.min(), xs.max(), 101):
            acc1 = ((xs >= thr).astype(int) == y).mean()
            acc2 = ((xs < thr).astype(int) == y).mean()
            if acc1 > best[2]:
                best = (c, thr, acc1)
            if acc2 > best[2]:
                best = (c, thr, acc2)
    print('best one-feature threshold for', target, best)

# V2 dataset audit
print('\n=== V2 dataset audit ===')
ingestion = RealDataIngestionPipeline()
df_v2 = ingestion.compile_full_dataset()
print('shape', df_v2.shape)
print('duplicates', df_v2.duplicated().sum())
print('constant cols', [c for c in df_v2.columns if df_v2[c].nunique() == 1])
print('potential leak cols', [c for c in df_v2.columns if any(tok in c for tok in ['prob', 'risk', 'score', 'frequency']) and c not in ['flood_label', 'landslide_label']])
print('corr with flood top')
print(df_v2.corr(numeric_only=True)['flood_label'].abs().sort_values(ascending=False).head(12))
print('corr with landslide top')
print(df_v2.corr(numeric_only=True)['landslide_label'].abs().sort_values(ascending=False).head(12))

eng = feature_engineer.engineer_features(df_v2)
print('engineered new cols', [c for c in eng.columns if c not in df_v2.columns])
print('engineered corr with flood top')
print(eng.corr(numeric_only=True)['flood_label'].abs().sort_values(ascending=False).head(15))
print('engineered corr with landslide top')
print(eng.corr(numeric_only=True)['landslide_label'].abs().sort_values(ascending=False).head(15))

# Cross-validation on V1 flood with XGBoost-like tree/ensemble using simple decision tree
from sklearn.ensemble import RandomForestClassifier
clf_rf = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
accs=[]
for tr, te in skf.split(X, yf):
    clf_rf.fit(X[tr], yf[tr])
    accs.append(clf_rf.score(X[te], yf[te]))
print('RF 5-fold acc mean/std', np.mean(accs), np.std(accs), accs)
PY