# GeoShield AI — Model Evaluation Report

_Generated automatically by `ml/generate_report.py` on 2026-06-26 04:47 UTC._

## 1. Dataset

- **Samples:** 10000
- **Engineered features:** 40

- **Feature columns:**

`lat`, `lon`, `elevation`, `slope`, `aspect`, `terrain_roughness`, `curvature`, `twi`, `ndwi`, `ndvi`, `mndwi`, `evi`, `rain_24h`, `rain_48h`, `rain_72h`, `rain_7d`, `spi`, `soil_moisture`, `sar_backscatter`, `sar_vh`, `drainage_density`, `river_proximity`, `water_occurrence`, `flow_accumulation`, `soil_type_encoded`, `historical_flood_freq`, `rain_intensity_24_72`, `rain_intensity_48_7d`, `flood_compound`, `landslide_compound`, `slope_moisture_interaction`, `rain_elevation_interaction`, `vegetation_vulnerability`, `water_saturation_index`, `log_rain_24h`, `log_rain_72h`, `log_elevation`, `log_flow_acc`, `slope_squared`, `rain_24h_squared`

## 2. Methodology

Models are trained on a physics-based synthetic geospatial dataset (see `ml/dataset_generator.py`) that jointly samples terrain, spectral indices, precipitation, soil and hydrology features within the Indian subcontinent. Labels are derived from physically-motivated rule scoring (floods favour low elevation, high NDWI, heavy rain, high soil moisture; landslides favour steep slopes, high moisture, sparse vegetation). A 70/15/15 stratified train/validation/test split is used.

Each hazard is modelled by an independent suite of architectures trained on the same features, then combined into a weighted ensemble. Deep models (LSTM, CNN, CNN-LSTM) are trained with PyTorch; tree-based models (Random Forest, XGBoost) use scikit-learn / XGBoost with class-weight balancing.

## 3. Flood Prediction Models

### 3.1 Metrics

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Score | Specificity | NPV |
|---|---|---|---|---|---|---|---|---|---|
| Random Forest | 94.27% | 85.33% | 93.07% | 89.03% | 98.38% | 95.73% | 0.0463 | 94.67% | 97.62% |
| XGBoost | 95.40% | 88.25% | 94.13% | 91.10% | 98.63% | 96.35% | 0.0375 | 95.82% | 98.00% |
| LSTM | 89.40% | 76.21% | 83.73% | 79.80% | 95.50% | 88.64% | 0.0908 | 91.29% | 94.39% |
| CNN-LSTM | 85.47% | 69.97% | 73.33% | 71.61% | 90.82% | 77.62% | 0.1048 | 89.51% | 90.97% |
| Ensemble | 94.60% | 86.93% | 92.27% | 89.52% | 98.10% | 95.06% | 0.0468 | 95.38% | 97.37% |

### 3.2 Confusion Matrices

**Random Forest**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1065 | 60 |
| **Actual Positive** | 26 | 349 |

**XGBoost**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1078 | 47 |
| **Actual Positive** | 22 | 353 |

**LSTM**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1027 | 98 |
| **Actual Positive** | 61 | 314 |

**CNN-LSTM**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1007 | 118 |
| **Actual Positive** | 100 | 275 |

**Ensemble**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1073 | 52 |
| **Actual Positive** | 29 | 346 |

## 4. Landslide Prediction Models

### 4.1 Metrics

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Score | Specificity | NPV |
|---|---|---|---|---|---|---|---|---|---|
| Random Forest | 92.20% | 83.80% | 86.20% | 84.98% | 97.40% | 92.81% | 0.0593 | 94.27% | 95.20% |
| XGBoost | 92.80% | 83.82% | 89.06% | 86.36% | 97.91% | 94.34% | 0.0520 | 94.09% | 96.15% |
| LSTM | 86.93% | 76.11% | 71.35% | 73.66% | 92.47% | 81.68% | 0.1102 | 92.29% | 90.35% |
| CNN | 82.07% | 63.10% | 72.14% | 67.31% | 86.52% | 71.04% | 0.1320 | 85.48% | 89.92% |
| Ensemble | 92.13% | 84.46% | 84.90% | 84.68% | 97.09% | 92.03% | 0.0604 | 94.62% | 94.79% |

### 4.2 Confusion Matrices

**CNN**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 954 | 162 |
| **Actual Positive** | 107 | 277 |

**Random Forest**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1052 | 64 |
| **Actual Positive** | 53 | 331 |

**XGBoost**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1050 | 66 |
| **Actual Positive** | 42 | 342 |

**LSTM**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1030 | 86 |
| **Actual Positive** | 110 | 274 |

**Ensemble**

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 1056 | 60 |
| **Actual Positive** | 58 | 326 |

## 5. Feature Importance

### 5.1 Flood drivers (top 15)

| Rank | Feature | Mean Importance |
|---|---|---|
| 1 | `flood_compound` | 0.2149 █████████████████████ |
| 2 | `water_saturation_index` | 0.1018 ██████████ |
| 3 | `rain_24h_squared` | 0.0577 █████ |
| 4 | `rain_24h` | 0.0521 █████ |
| 5 | `rain_elevation_interaction` | 0.0474 ████ |
| 6 | `ndwi` | 0.0471 ████ |
| 7 | `log_rain_24h` | 0.0462 ████ |
| 8 | `historical_flood_freq` | 0.0440 ████ |
| 9 | `river_proximity` | 0.0413 ████ |
| 10 | `rain_72h` | 0.0336 ███ |
| 11 | `elevation` | 0.0320 ███ |
| 12 | `drainage_density` | 0.0318 ███ |

### 5.2 Landslide drivers (top 15)

| Rank | Feature | Mean Importance |
|---|---|---|
| 1 | `landslide_compound` | 0.1610 ████████████████ |
| 2 | `rain_72h` | 0.1127 ███████████ |
| 3 | `log_rain_72h` | 0.0708 ███████ |
| 4 | `soil_moisture` | 0.0612 ██████ |
| 5 | `vegetation_vulnerability` | 0.0596 █████ |
| 6 | `rain_48h` | 0.0552 █████ |
| 7 | `twi` | 0.0526 █████ |
| 8 | `ndvi` | 0.0514 █████ |
| 9 | `curvature` | 0.0393 ███ |
| 10 | `elevation` | 0.0350 ███ |
| 11 | `slope` | 0.0335 ███ |
| 12 | `log_elevation` | 0.0296 ██ |

## 8. Reproducibility

All randomness is seeded (dataset generation seed = 42, NumPy / PyTorch / scikit-learn seeds pinned in `ml/train_advanced.py`). Re-running `python -m ml.train_advanced` reproduces the metrics above within floating-point tolerance. Hyperparameters are centralised in `ml/config.py`.
