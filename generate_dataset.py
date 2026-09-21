"""
Synthetic Dataset Generator Script for PIPO Data Buffer Simulator
Creates CSV datasets:
  - data/pipo_normal_traffic.csv
  - data/pipo_fault_traffic.csv
"""

import os
import pandas as pd
from ai_analytics import SyntheticTrafficGenerator


def generate_and_save():
    os.makedirs("data", exist_ok=True)
    
    # 1. Normal traffic workload (500 cycles)
    df_normal = SyntheticTrafficGenerator.generate_workload(
        num_samples=500, pattern_type="burst", noise_prob=0.0, seed=101
    )
    normal_path = os.path.join("data", "pipo_normal_traffic.csv")
    df_normal.to_csv(normal_path, index=False)
    print(f"Saved normal traffic dataset to {normal_path} ({len(df_normal)} records)")

    # 2. Fault traffic workload with 15% error rate (500 cycles)
    df_fault = SyntheticTrafficGenerator.generate_workload(
        num_samples=500, pattern_type="burst", noise_prob=0.15, seed=202
    )
    fault_path = os.path.join("data", "pipo_fault_traffic.csv")
    df_fault.to_csv(fault_path, index=False)
    print(f"Saved fault traffic dataset to {fault_path} ({len(df_fault)} records)")


if __name__ == "__main__":
    generate_and_save()
