import torch
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "model_dir"

def inspect_pth(fpath):
    print(f"\n--- Inspecting {fpath.name} ---")
    try:
        state_dict = torch.load(fpath, map_location="cpu")
        if isinstance(state_dict, dict):
            print(f"Loaded as dict. Keys ({len(state_dict)}):")
            for k, v in state_dict.items():
                print(f"  {k}: shape {list(v.shape) if hasattr(v, 'shape') else type(v)}")
        else:
            print(f"Loaded as {type(state_dict)}")
            print(state_dict)
    except Exception as e:
        print(f"Error loading {fpath.name}: {e}")

def main():
    for name in ["flood_v2_cnn_lstm.pth", "flood_v2_lstm.pth", "landslide_v2_cnn.pth", "landslide_v2_lstm.pth"]:
        fpath = MODEL_DIR / name
        if fpath.exists():
            inspect_pth(fpath)
        else:
            print(f"File {name} does not exist.")

if __name__ == "__main__":
    main()
