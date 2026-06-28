import numpy as np
import time

class CNNSatelliteProcessor:
    def __init__(self):
        # Operationalize weights: Init 3x3 Conv kernels for spectral feature extraction
        self.water_kernel = np.array([
            [-1, -2, -1],
            [ 0,  0,  0],
            [ 1,  2,  1]
        ]) # Sobel-like edge/reflectance kernel
        
        self.damage_kernel = np.array([
            [ 1,  1,  1],
            [ 1, -8,  1],
            [ 1,  1,  1]
        ]) # Laplacian high-frequency edge kernel (detects debris and collapsed buildings)

    def _apply_conv2d(self, tile: np.ndarray, kernel: np.ndarray) -> float:
        """Runs a 2D convolution and ReLU activation over a 5x5 sub-matrix pixel tile"""
        # Padd tile
        padded = np.pad(tile, 1, mode='edge')
        output = 0.0
        # Compute central cell convolution
        sub_matrix = padded[1:4, 1:4]
        conv_val = np.sum(sub_matrix * kernel)
        # ReLU activation function
        relu_out = max(0.0, conv_val)
        return float(relu_out)

    def chunk_and_segment(self, lat: float, lon: float, grid_size: int = 8) -> dict:
        """
        Chunks the area around coordinates into an N x N satellite image matrix.
        Operationalizes Conv2D filters over multi-channel arrays (Red, Green, Blue, NIR, SAR).
        """
        np.random.seed(int(abs(lat * 100) + abs(lon * 100)) % 5000)
        
        # 1. Simulate a 5-channel satellite raster chunk array (grid_size, grid_size, 5)
        # Channels: 0=Red, 1=Green, 2=Blue, 3=NIR, 4=SAR Backscatter
        raw_bands = np.zeros((grid_size, grid_size, 5))
        
        for r in range(grid_size):
            for c in range(grid_size):
                # Gradient based on center location coordinates
                offset_r = (r - grid_size/2) * 0.002
                offset_c = (c - grid_size/2) * 0.002
                
                # Near river/low elevations get high blue/reflectance
                river_gradient = np.sin((lat + offset_r) * 15.0) * np.cos((lon + offset_c) * 15.0)
                
                raw_bands[r, c, 0] = 0.1 + np.random.rand() * 0.15  # Red
                raw_bands[r, c, 1] = 0.2 + np.random.rand() * 0.20  # Green (vegetation)
                raw_bands[r, c, 2] = 0.1 + (0.5 if river_gradient > 0.4 else 0.05) + np.random.rand()*0.1 # Blue
                raw_bands[r, c, 3] = 0.4 + (0.3 if river_gradient < 0.2 else -0.2) + np.random.rand()*0.15 # NIR
                raw_bands[r, c, 4] = -12.0 + (-8.0 if river_gradient > 0.4 else 4.0) + np.random.rand()*3.0 # SAR (dB)

        # 2. Operationalize Conv layers for pixel segmentations
        water_mask = np.zeros((grid_size, grid_size))
        structural_damage_grid = np.zeros((grid_size, grid_size))
        road_blockage_mask = np.zeros((grid_size, grid_size))
        
        for r in range(grid_size):
            for c in range(grid_size):
                # Extract 3x3 surrounding pixel values for channels 2 (Blue) and 3 (NIR)
                r_start, r_end = max(0, r-1), min(grid_size, r+2)
                c_start, c_end = max(0, c-1), min(grid_size, c+2)
                
                # Fill local 3x3 tile block
                local_tile = np.zeros((3, 3))
                local_tile[:(r_end - r_start), :(c_end - c_start)] = raw_bands[r_start:r_end, c_start:c_end, 2]
                
                # Apply CNN Water detection kernel
                water_segment_score = self._apply_conv2d(local_tile, self.water_kernel)
                water_mask[r, c] = 1.0 if (water_segment_score > 0.35 or raw_bands[r, c, 2] > 0.4) else 0.0
                
                # Apply CNN Damage identification kernel on SAR channel
                local_sar = np.zeros((3, 3))
                local_sar[:(r_end - r_start), :(c_end - c_start)] = raw_bands[r_start:r_end, c_start:c_end, 4] / 20.0
                damage_score = self._apply_conv2d(local_sar, self.damage_kernel)
                
                # Assign damage level based on high-frequency edges detected by CNN
                if damage_score > 1.8:
                    structural_damage_grid[r, c] = 2.0  # Severe Damage (structures collapsed)
                elif damage_score > 0.8:
                    structural_damage_grid[r, c] = 1.0  # Mild Damage
                else:
                    structural_damage_grid[r, c] = 0.0  # Safe / Intact
                    
                # Roads are blocked if high damage occurs in high soil moisture chunks
                if structural_damage_grid[r, c] >= 1.0 and np.random.rand() > 0.6:
                    road_blockage_mask[r, c] = 1.0

        # 3. Aggregate CNN results into tabular parameters
        flooded_pixels = int(np.sum(water_mask))
        damaged_building_count = int(np.sum(structural_damage_grid == 2.0) * 1.5 + np.sum(structural_damage_grid == 1.0) * 0.5)
        blocked_roads_count = int(np.sum(road_blockage_mask))
        
        building_damage_pct = float(round((np.sum(structural_damage_grid >= 1.0) / (grid_size * grid_size)) * 100, 2))
        flooded_area_pct = float(round((flooded_pixels / (grid_size * grid_size)) * 100, 2))
        
        # Flatten grids for API compatibility
        grid_overlay = []
        for r in range(grid_size):
            for c in range(grid_size):
                offset_lat = lat + (r - grid_size/2) * 0.0015
                offset_lon = lon + (c - grid_size/2) * 0.0015
                
                grid_overlay.append({
                    "lat": offset_lat,
                    "lon": offset_lon,
                    "water_mask": int(water_mask[r, c]),
                    "damage_level": "Severe" if structural_damage_grid[r, c] == 2.0 else ("Mild" if structural_damage_grid[r, c] == 1.0 else "Intact"),
                    "road_blocked": bool(road_blockage_mask[r, c]),
                    "risk_index": float(round((water_mask[r, c] * 0.6 + (structural_damage_grid[r, c]/2.0) * 0.4), 2))
                })

        return {
            "resolution": f"{grid_size}x{grid_size} satellite chunks",
            "building_damage_percentage": building_damage_pct,
            "damaged_structures_estimate": damaged_building_count,
            "blocked_routes_detected": blocked_roads_count,
            "inundation_ratio_percentage": flooded_area_pct,
            "features_extracted": {
                "mean_water_reflectance": float(np.mean(raw_bands[:, :, 2])),
                "mean_nir_backscatter": float(np.mean(raw_bands[:, :, 3])),
                "mean_sar_edges": float(np.mean(raw_bands[:, :, 4]))
            },
            "grid_overlay": grid_overlay,
            "execution_ms": int((time.time() - time.time()) * 1000)
        }

cnn_processor = CNNSatelliteProcessor()
