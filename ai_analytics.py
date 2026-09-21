"""
AI & Data Analytics Layer for PIPO Data Buffer Simulator (EC2201 Syllabus)
Provides synthetic workload generation, machine learning anomaly/fault detection,
and predictive throughput optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix


class SyntheticTrafficGenerator:
    """
    Generates synthetic input data streams and digital signal noise patterns for testing.
    """
    @staticmethod
    def generate_workload(num_samples: int = 100, 
                          pattern_type: str = "burst", 
                          bit_width: int = 8, 
                          noise_prob: float = 0.05,
                          seed: int = 42) -> pd.DataFrame:
        """
        Generates reproducible synthetic traffic samples.
        Pattern types: 'uniform', 'burst', 'counter', 'parity', 'noisy'
        """
        np.random.seed(seed)
        max_val = (1 << bit_width) - 1
        records = []
        
        for i in range(num_samples):
            cycle = i + 1
            clk_freq_mhz = float(np.random.choice([50.0, 100.0, 133.0, 200.0]))
            temp_c = float(np.random.uniform(25.0, 85.0))
            setup_time_ps = float(np.random.normal(1000.0, 100.0))  # 1.0 ns avg
            hold_time_ps = float(np.random.normal(500.0, 50.0))     # 0.5 ns avg
            
            # Default normal signals
            write_enable = 1
            read_enable = 1
            
            if pattern_type == "counter":
                word_val = i % (max_val + 1)
            elif pattern_type == "burst":
                # Alternate 5 cycles write, 5 cycles read
                write_enable = 1 if (i // 5) % 2 == 0 else 0
                read_enable = 1 if (i // 5) % 2 == 1 else 0
                word_val = np.random.randint(0, max_val + 1)
            elif pattern_type == "parity":
                # Alternating parity words 0x55 and 0xAA
                word_val = 0x55 if i % 2 == 0 else 0xAA
            else:  # uniform or noisy
                word_val = np.random.randint(0, max_val + 1)
                
            # Noise injection
            is_anomaly = 0
            fault_type = "NORMAL"
            
            if np.random.rand() < noise_prob:
                is_anomaly = 1
                fault_choice = np.random.choice(["SETUP_VIOLATION", "HOLD_VIOLATION", "BIT_FLIP", "OVERFLOW"])
                fault_type = str(fault_choice)
                
                if fault_type == "SETUP_VIOLATION":
                    setup_time_ps = float(np.random.uniform(100.0, 400.0))  # violates 1.0 ns setup
                elif fault_type == "HOLD_VIOLATION":
                    hold_time_ps = float(np.random.uniform(50.0, 150.0))   # violates 0.5 ns hold
                elif fault_type == "BIT_FLIP":
                    bit_to_flip = np.random.randint(0, bit_width)
                    word_val ^= (1 << bit_to_flip)
                elif fault_type == "OVERFLOW":
                    write_enable = 1
                    read_enable = 0
            
            records.append({
                "cycle": cycle,
                "write_word": word_val,
                "write_enable": write_enable,
                "read_enable": read_enable,
                "clk_freq_mhz": clk_freq_mhz,
                "setup_time_ps": setup_time_ps,
                "hold_time_ps": hold_time_ps,
                "temp_c": temp_c,
                "fault_type": fault_type,
                "is_anomaly": is_anomaly
            })
            
        return pd.DataFrame(records)


class AIFaultDetector:
    """
    Machine Learning Anomaly and Fault Detection for PIPO Data Buffers.
    """
    def __init__(self):
        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self.rf_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        self.is_fitted = False
        self.feature_names = ["setup_time_ps", "hold_time_ps", "clk_freq_mhz", "temp_c", "write_enable", "read_enable"]

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains IsolationForest for unsupervised anomaly detection and RandomForest for fault classification.
        """
        X = df[self.feature_names]
        y = df["is_anomaly"]
        
        # Fit Isolation Forest
        self.iso_forest.fit(X)
        
        # Fit Classifier
        self.rf_classifier.fit(X, df["fault_type"])
        self.is_fitted = True
        
        # Predictions
        iso_preds = self.iso_forest.predict(X)  # -1 for anomaly, 1 for normal
        iso_binary = np.where(iso_preds == -1, 1, 0)
        
        rf_preds = self.rf_classifier.predict(X)
        
        report = classification_report(df["fault_type"], rf_preds, output_dict=True)
        feature_importance = dict(zip(self.feature_names, self.rf_classifier.feature_importances_.round(4)))

        return {
            "training_samples": len(df),
            "detected_anomalies": int(np.sum(iso_binary)),
            "actual_anomalies": int(y.sum()),
            "feature_importance": feature_importance,
            "classification_report": report
        }

    def predict_sample(self, sample_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Predicts whether a live hardware clock cycle input contains a timing/data fault.
        """
        if not self.is_fitted:
            # Self-fit on default synthetic baseline if not trained yet
            df_base = SyntheticTrafficGenerator.generate_workload(200, noise_prob=0.1)
            self.train(df_base)
            
        X_sample = pd.DataFrame([[
            sample_dict.get("setup_time_ps", 1000.0),
            sample_dict.get("hold_time_ps", 500.0),
            sample_dict.get("clk_freq_mhz", 100.0),
            sample_dict.get("temp_c", 25.0),
            sample_dict.get("write_enable", 1),
            sample_dict.get("read_enable", 1)
        ]], columns=self.feature_names)
        
        iso_score = float(self.iso_forest.score_samples(X_sample)[0])
        is_anomaly = bool(self.iso_forest.predict(X_sample)[0] == -1)
        predicted_fault = str(self.rf_classifier.predict(X_sample)[0])

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(iso_score, 4),
            "predicted_fault_type": predicted_fault,
            "status": "FAULT DETECTED" if is_anomaly else "NORMAL OPERATION"
        }


if __name__ == "__main__":
    print("Testing AI & Data Analytics Layer...")
    generator = SyntheticTrafficGenerator()
    df_data = generator.generate_workload(num_samples=150, pattern_type="burst", noise_prob=0.12)
    print(f"Generated {len(df_data)} synthetic data samples.")
    print(df_data[["cycle", "write_word", "fault_type", "is_anomaly"]].head(10))
    
    detector = AIFaultDetector()
    metrics = detector.train(df_data)
    print("\nModel Training Metrics:")
    print("Feature Importance:", metrics["feature_importance"])
    
    test_sample = {
        "setup_time_ps": 250.0,  # setup violation!
        "hold_time_ps": 500.0,
        "clk_freq_mhz": 100.0,
        "temp_c": 45.0,
        "write_enable": 1,
        "read_enable": 1
    }
    pred = detector.predict_sample(test_sample)
    print("\nLive Sample Fault Prediction:")
    print(pred)
