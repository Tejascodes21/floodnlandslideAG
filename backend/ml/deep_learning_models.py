"""
Deep Learning Models Module
=============================
Defines the PyTorch architectures for Flood and Landslide prediction,
including LSTMs, CNNs, and CNN-LSTMs, along with training utility loops.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import logging

logger = logging.getLogger("geoshield.ml.deep_learning")

# --- Flood Prediction PyTorch Architectures ---

class FloodLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

class FloodCNNLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.lstm = nn.LSTM(input_size=16, hidden_size=32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        x = torch.relu(self.conv(x))
        x = x.transpose(1, 2)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

# --- Landslide Susceptibility PyTorch Architectures ---

class LandslideCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=8, kernel_size=3)
        self.fc = nn.Linear(8, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.mean(x, dim=2)
        return torch.sigmoid(self.fc(x))

class LandslideLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=40, hidden_size=24, batch_first=True)
        self.fc = nn.Linear(24, 1)

    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))

# --- PyTorch Classifier Wrapper for Scikit-Learn Compatibility ---

class PyTorchClassifierWrapper:
    def __init__(self, pytorch_model, model_name="PyTorchModel", lr=0.005, epochs=100, batch_size=32, patience=10):
        self.model = pytorch_model
        self.name = model_name
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.n_features_in_ = 40
        self.classes_ = np.array([0, 1])

    def fit(self, X, y, X_val=None, y_val=None):
        self.model.train()
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)

        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        best_loss = float('inf')
        best_weights = None
        patience_counter = 0

        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * batch_X.size(0)
            epoch_loss /= len(X)

            # Validation validation
            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    X_v = torch.tensor(X_val, dtype=torch.float32)
                    y_v = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
                    val_outputs = self.model(X_v)
                    val_loss = criterion(val_outputs, y_v).item()
                self.model.train()
            else:
                val_loss = epoch_loss

            if val_loss < best_loss:
                best_loss = val_loss
                best_weights = self.model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= self.patience:
                logger.info(f"[{self.name}] Early stopping at epoch {epoch}. Best Val Loss: {best_loss:.4f}")
                break

        if best_weights is not None:
            self.model.load_state_dict(best_weights)
        self.model.eval()
        return self

    def predict_proba(self, X):
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32)
            outputs = self.model(X_t).numpy().flatten()
        return np.vstack([1.0 - outputs, outputs]).T

    def predict(self, X, threshold=0.5):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)
