# PIPO Data Buffer Simulator & Interactive Web Application

[![EC2201 Digital Electronics](https://img.shields.io/badge/Course-EC2201%20Digital%20Systems-cyan.svg)](file:///)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](file:///)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-emerald.svg)](file:///)
[![Test Suite](https://img.shields.io/badge/Tests-15%20Passed-brightgreen.svg)](file:///)

A software simulation engine and interactive web application for a **Parallel-In Parallel-Out (PIPO) Data Buffer**, developed for the **EC2201 Digital Systems** syllabus. The project models hardware D-flip-flops, clocking, timing constraints ($t_{su}, t_h, t_{pd}$), tri-state buffers, multi-stage FIFO queues, AI fault detection, automated testing, and interactive waveform visualization.

---

## 1. Assumptions & Input Format

### Assumptions
1. **Clock Triggering:** D Flip-Flops sample input data on the rising edge of the system clock signal ($CLK: 0 \rightarrow 1$).
2. **Setup & Hold Constraints:** Default setup time $t_{su} = 1.0\text{ ns}$, hold time $t_h = 0.5\text{ ns}$, propagation delay $t_{pd} = 2.0\text{ ns}$.
3. **Reset Priority:** Asynchronous Active-Low Reset ($RST\_N = 0$) immediately overrides clock pulses and clears all flip-flop outputs $Q[N-1:0] \rightarrow 0$.
4. **Tri-state Buffer:** Output Enable ($OE = 0$) disconnects output lines, placing the output bus into High Impedance ($Hi\text{-}Z$).
5. **Configurable Width:** Supports $N \in \{4, 8, 16, 32\}$ parallel bit width registers.

### Input Data Formats
- **Parallel Data Bus $D[N-1:0]$:** List of boolean/integer bits `[D_0, D_1, ..., D_{N-1}]` or hexadecimal integer values (e.g. `0xA5`).
- **Control Pins:** `CLK` (0 or 1), `LOAD` (0 or 1), `RST_N` (0 or 1), `OE` (0 or 1).
- **Synthetic CSV Traffic:** Columns: `cycle`, `write_word`, `write_enable`, `read_enable`, `clk_freq_mhz`, `setup_time_ps`, `hold_time_ps`, `temp_c`, `fault_type`, `is_anomaly`.

---

## 2. Core Digital Logic & AI Architecture

```
                      Parallel Input Bus D[N-1:0]
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │               PIPO REGISTER ARRAY               │
          │  ┌─────────┐   ┌─────────┐         ┌─────────┐  │
          │  │ FF_N-1  │   │  FF_1   │  . . .  │  FF_0   │  │
          │  └─────────┘   └─────────┘         └─────────┘  │
          └─────────────────────────────────────────────────┘
             ▲ CLK          ▲ LOAD              ▲ RST_N
             │ Rising Edge  │ Clock Enable      │ Active Low
             │              │                   │
  ───────────┴──────────────┴───────────────────┴───────────────
                     Parallel Output Bus Q[N-1:0]
                                   │
                                   ▼
                       [ Tri-State OE Buffer ]
                                   │
                                   ▼
                         High-Impedance (Hi-Z) / Q
```

### Digital Logic Engine (`pipo_register.py`, `buffer_simulator.py`)
- **`DFlipFlop`**: Hardware-level Positive-Edge D Flip-Flop with timing verification logic.
- **`PIPORegister`**: $N$-bit parallel register handling simultaneous bit sampling, truth table generation, and state history.
- **`PIPODataBuffer`**: Cascaded multi-stage FIFO buffer calculating throughput (words/cycle), bandwidth (Mbps), and latency.

### Data & AI Layer (`ai_analytics.py`)
- **Synthetic Generator**: Creates burst, counter, parity, and noisy data streams.
- **AI Fault Detector**: Trained `IsolationForest` and `RandomForestClassifier` detecting setup violations ($t_{su} < 1.0\text{ ns}$), hold violations, and bit flips.

---

## 3. Quick Start & Installation

### Prerequisites
- Python 3.10+
- Installed packages: `fastapi`, `uvicorn`, `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `jinja2`

### Running the Project

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Datasets:**
   ```bash
   python generate_dataset.py
   ```

3. **Run Automated Test Suite (15 Test Cases):**
   ```bash
   python test_suite.py
   ```

4. **Launch Interactive Website:**
   ```bash
   python app.py
   # Or using uvicorn:
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
   Open your browser and navigate to: **`http://localhost:8000`**

5. **Run Jupyter Notebook:**
   ```bash
   jupyter notebook PIPO_Data_Buffer_Simulator.ipynb
   ```

---

## 4. Test Suite Summary (15 Test Cases)

| Test ID | Test Name | Category | Truth Table Operation | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC01** | Single Word Parallel Load & Read | Normal | Parallel Data Load | **PASS** |
| **TC02** | Multi-Word Sequential Burst | Normal | Parallel FIFO Transfer | **PASS** |
| **TC03** | Clock Enable (LOAD=0) Inhibit Test | Normal | Clock Disabled (Hold) | **PASS** |
| **TC04** | Asynchronous Reset (RST_N=0) | Normal | Asynchronous Reset | **PASS** |
| **TC05** | Tri-State Output Enable (OE=0) | Normal | Output Disabled (Hi-Z) | **PASS** |
| **TC06** | 4-Bit PIPO Register Load | Normal | Parallel Data Load | **PASS** |
| **TC07** | 16-Bit PIPO Register Load | Normal | Parallel Data Load | **PASS** |
| **TC08** | 32-Bit PIPO Register Load | Normal | Parallel Data Load | **PASS** |
| **TC09** | Full Buffer Pipeline Fill | Normal | Pipeline Occupancy | **PASS** |
| **TC10** | Simultaneous Read/Write | Normal | Concurrent Access | **PASS** |
| **TC11** | Setup Time Violation Fault | Edge/Fault | Timing Fault | **PASS** |
| **TC12** | Hold Time Violation Fault | Edge/Fault | Timing Fault | **PASS** |
| **TC13** | Reset During Active Write | Edge/Fault | Asynchronous Override | **PASS** |
| **TC14** | Buffer Overflow Fault | Edge/Fault | Capacity Overflow Fault | **PASS** |
| **TC15** | Buffer Underflow Fault | Edge/Fault | Capacity Underflow Fault | **PASS** |

---

## 5. File & Directory Structure

```
pipo_buffer_simulator/
├── pipo_register.py          # Core D Flip-Flop & PIPO Register digital model
├── buffer_simulator.py        # Multi-stage PIPO FIFO Buffer & Throughput engine
├── ai_analytics.py            # AI Anomaly Detector & Synthetic workload generator
├── test_suite.py              # 10 Normal + 5 Edge/Fault automated test suite
├── generate_dataset.py        # CSV dataset generation script
├── app.py                     # FastAPI web server backend
├── templates/
│   └── index.html             # Single-page interactive web application UI
├── static/
│   ├── style.css              # Dark-mode styling
│   └── app.js                 # Interactive SVG schematic & waveform visualizer
├── data/
│   ├── pipo_normal_traffic.csv# Synthetic normal traffic dataset
│   └── pipo_fault_traffic.csv # Synthetic fault traffic dataset
├── PIPO_Data_Buffer_Simulator.ipynb # Interactive Jupyter Notebook
├── REPORT.md                  # Comprehensive student project report
├── DEMO_SCRIPT.md             # 3-5 minute video demo presentation script
└── requirements.txt           # Dependency manifest
```

---

## 6. References
1. **EC2201 Digital Systems Syllabus**: Sequential Logic Design, Registers, Flip-Flops, Bus Interfaces.
2. M. Morris Mano, *Digital Design: With an Introduction to the Verilog HDL*, 5th Ed., Pearson.
3. Ronald J. Tocci, *Digital Systems: Principles and Applications*, 12th Ed., Pearson.
