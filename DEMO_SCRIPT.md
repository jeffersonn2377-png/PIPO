# PIPO Data Buffer Simulator: 3–5 Minute Video Demo Script

**Project Title:** PIPO Data Buffer Simulator  
**Syllabus Mapping:** EC2201 Digital Systems & Microprocessors  
**Target Duration:** 4 Minutes  

---

## Video Timeline & Script Breakdown

### [0:00 - 0:45] Section 1: Introduction & Real-World Context
- **Visual:** Presenter on screen or opening web app header (`http://localhost:8000`).
- **Narrator Script:**
  > "Hello everyone! Today we present our software simulator and interactive web application for the **Parallel-In Parallel-Out (PIPO) Data Buffer**, designed for the EC2201 Digital Systems course syllabus.
  > In real-world computing—such as CPU register files, GPU frame buffers, or memory buses—data words must be loaded simultaneously on a clock pulse. A PIPO register uses parallel D-flip-flops to store all bits at once, achieving maximum throughput with a single clock cycle latency."

---

### [0:45 - 2:00] Section 2: Interactive Web Simulator & Circuit Visualizer
- **Visual:** Navigate to **Simulator** tab. Click D-bit buttons to set `D = 0xA5 (10100101)`. Click **CLK Pulse**.
- **Narrator Script:**
  > "Let's demonstrate our interactive hardware model! Here in the web interface, we select an 8-bit PIPO register. We present the input word `0xA5` on the parallel bus $D[7:0]$.
  > Notice that when the clock is low, the flip-flops hold their previous state. Now, when we click **CLK Pulse (Rising Edge)**, all 8 D flip-flops sample their inputs simultaneously, and the output bus updates instantly to `0xA5`.
  > We can also demonstrate **Clock Enable (LOAD=0)** where clock pulses are inhibited, and **Asynchronous Reset (RST_N=0)** which clears all outputs to `0x00` immediately."

---

### [2:00 - 2:45] Section 3: Live Signal Waveforms & Multi-Stage Buffer
- **Visual:** Switch to **Waveforms** tab showing live square waves for CLK, LOAD, RST_N, D_BUS, Q_BUS.
- **Narrator Script:**
  > "Next, let's look at the **Real-Time Signal Timing Diagram**. Our canvas logic analyzer renders digital square waves for CLK, LOAD, Reset, and hexadecimal bus values in real time.
  > Moving down to our **Multi-Stage PIPO Buffer Pipeline**, we can simulate an 8-stage FIFO queue operating at 100 MHz, achieving a maximum bandwidth of 800 Mbps with 100% bus efficiency."

---

### [2:45 - 3:30] Section 4: Automated Test Suite & AI Anomaly Detection
- **Visual:** Switch to **Test Suite** tab, click **Run All 15 Test Cases**. Then switch to **AI Analytics** tab.
- **Narrator Script:**
  > "To guarantee reproducibility and accuracy, we built an automated test suite containing 10 normal test cases and 5 edge fault cases—such as setup time violations, hold time violations, and buffer overflow. Clicking 'Run All' executes all 15 tests, showing a 100% PASS rate.
  > Furthermore, our **AI & Data Layer** uses an IsolationForest model to detect hardware timing anomalies in real-time when data changes within the 1.0 ns setup window."

---

### [3:30 - 4:00] Section 5: Conclusion & Student Deliverables
- **Visual:** Switch to **Deliverables** tab showing download links for CSV datasets, Jupyter Notebook, and report.
- **Narrator Script:**
  > "In conclusion, our solution provides a complete, reproducible software simulation of a PIPO Data Buffer, featuring interactive visualization, AI fault detection, 15 verification test cases, a Jupyter Notebook, and downloadable synthetic datasets. Thank you for watching!"

---

## Instructions for Video Recording
1. Start the FastAPI web application using `python app.py`.
2. Open Chrome or Edge and navigate to `http://localhost:8000`.
3. Use OBS Studio or Windows Game Bar (`Win + G`) to record the screen and audio.
4. Follow the script timestamps above for a smooth 3–5 minute presentation.
