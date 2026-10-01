import torch
import torch.nn as nn
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "model_dir"

class FloodLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        # x: [batch, 40] -> [batch, 1, 40]
        x = x.unsqueeze(1)
        out, (hn, cn) = self.lstm(x)
        # out: [batch, 1, 32]
        return torch.sigmoid(self.fc(out[:, -1, :]))

class FloodCNNLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.lstm = nn.LSTM(input_size=16, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        # x: [batch, 40] -> [batch, 1, 40]
        x = x.unsqueeze(1)
        x = torch.relu(self.conv(x)) # [batch, 16, 38]
        x = x.transpose(1, 2) # [batch, 38, 16]
        out, (hn, cn) = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

class LandslideCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=8, kernel_size=3)
        self.fc = nn.Linear(8, 1)

    def forward(self, x):
        # x: [batch, 40] -> [batch, 1, 40]
        x = x.unsqueeze(1)
        x = torch.relu(self.conv1(x)) # [batch, 16, 38]
        x = torch.relu(self.conv2(x)) # [batch, 8, 36]
        x = torch.mean(x, dim=2) # global average pool -> [batch, 8]
        return torch.sigmoid(self.fc(x))

class LandslideLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=24, batch_first=True)
        self.fc = nn.Linear(24, 1)

    def forward(self, x):
        # x: [batch, 40] -> [batch, 1, 40]
        x = x.unsqueeze(1)
        out, (hn, cn) = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

def main():
    models = {
        "flood_v2_cnn_lstm.pth": FloodCNNLSTM(),
        "flood_v2_lstm.pth": FloodLSTM(),
        "landslide_v2_cnn.pth": LandslideCNN(),
        "landslide_v2_lstm.pth": LandslideLSTM()
    }
    
    for name, model in models.items():
        fpath = MODEL_DIR / name
        try:
            state_dict = torch.load(fpath, map_location="cpu")
            model.load_state_dict(state_dict)
            print(f"Successfully loaded model from {name}!")
        except Exception as e:
            print(f"Error loading {name}: {e}")

if __name__ == "__main__":
    main()
