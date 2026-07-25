import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "model_dir"

def main():
    print("=== Model Directory Check ===")
    if not MODEL_DIR.exists():
        print(f"Directory {MODEL_DIR} does not exist.")
        return
        
    for p in sorted(MODEL_DIR.iterdir()):
        if p.is_file():
            print(f"File: {p.name}, Size: {p.stat().st_size} bytes")
            if p.suffix == ".pkl":
                try:
                    obj = joblib.load(p)
                    print(f"  Type: {type(obj)}")
                except Exception as e:
                    print(f"  Error loading: {e}")

    print("\n=== Dataset Check ===")
    dataset_path = Path(__file__).resolve().parent / "ml" / "training_dataset.csv"
    if not dataset_path.exists():
         print(f"Dataset {dataset_path} does not exist.")
         return
         
    df = pd.read_csv(dataset_path)
    print(f"Shape: {df.shape}")
    print("Columns:", list(df.columns))
    print("\nState distributions:")
    print(df["state"].value_counts())
    print("\nDistrict distributions:")
    print(df["district"].value_counts())
    print("\nFlood label counts:")
    print(df["flood_label"].value_counts())
    print("\nLandslide label counts:")
    print(df["landslide_label"].value_counts())

if __name__ == "__main__":
    main()
