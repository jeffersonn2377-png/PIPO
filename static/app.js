/**
 * PIPO Data Buffer Simulator - Frontend Logic & Circuit/Waveform Visualizer
 */

let currentBitWidth = 8;
let dBusBits = Array(8).fill(0);
let currentClk = 0;
let currentLoad = 1;
let currentResetN = 1;
let currentOE = 1;
let waveformHistory = [];
let aiChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initBitWidthSelector();
    initPinControls();
    updateCircuitVisualizer();
    renderWaveforms();
    loadTruthTable();
    initAICounts();
});

// Tab Navigation
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            
            const targetId = tab.getAttribute("data-tab");
            document.querySelectorAll(".tab-content").forEach(content => {
                content.classList.add("hidden");
            });
            document.getElementById(targetId).classList.remove("hidden");

            if (targetId === "ai-analytics") {
                loadAITraffic();
            }
        });
    });
}

// Bit Width Selector (4, 8, 16, 32)
function initBitWidthSelector() {
    const selector = document.getElementById("bitWidthSelect");
    if (!selector) return;
    selector.addEventListener("change", (e) => {
        currentBitWidth = parseInt(e.target.value);
        dBusBits = Array(currentBitWidth).fill(0);
        updateBitInputButtons();
        updateCircuitVisualizer();
        loadTruthTable();
    });
    updateBitInputButtons();
}

function updateBitInputButtons() {
    const container = document.getElementById("bitButtonsContainer");
    if (!container) return;
    container.innerHTML = "";
    
    for (let i = currentBitWidth - 1; i >= 0; i--) {
        const btn = document.createElement("button");
        btn.className = `px-3 py-1.5 rounded font-mono text-xs font-bold transition ${
            dBusBits[i] ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
        }`;
        btn.innerText = `D${i}: ${dBusBits[i]}`;
        btn.addEventListener("click", () => {
            dBusBits[i] = dBusBits[i] ? 0 : 1;
            updateBitInputButtons();
            updateCircuitVisualizer();
        });
        container.appendChild(btn);
    }
    
    // Quick Preset Hex Input
    const hexVal = dBusBits.reduce((acc, bit, idx) => acc + (bit << idx), 0);
    const hexLabel = document.getElementById("hexInputDisplay");
    if (hexLabel) {
        hexLabel.innerText = `0x${hexVal.toString(16).toUpperCase().padStart(Math.ceil(currentBitWidth / 4), '0')}`;
    }
}

function initPinControls() {
    // Clock Step Pulse Button
    document.getElementById("btnClockStep")?.addEventListener("click", async () => {
        // Clock Low
        await stepRegisterAPI(0);
        // Clock High (Rising Edge)
        await stepRegisterAPI(1);
    });

    // Reset Toggle
    document.getElementById("btnToggleReset")?.addEventListener("click", () => {
        currentResetN = currentResetN ? 0 : 1;
        const btn = document.getElementById("btnToggleReset");
        if (currentResetN) {
            btn.className = "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-semibold border border-slate-700";
            btn.innerText = "RESET (RST_N = 1: Normal)";
        } else {
            btn.className = "px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded font-semibold shadow-lg shadow-rose-600/30";
            btn.innerText = "RESET ASSERTED (RST_N = 0)";
        }
        stepRegisterAPI(currentClk);
    });

    // Load Enable Toggle
    document.getElementById("btnToggleLoad")?.addEventListener("click", () => {
        currentLoad = currentLoad ? 0 : 1;
        const btn = document.getElementById("btnToggleLoad");
        btn.innerText = `LOAD ENABLE (LOAD = ${currentLoad})`;
        btn.className = currentLoad ? "px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-semibold" : "px-4 py-2 bg-slate-800 text-slate-400 rounded font-semibold";
    });

    // Output Enable Toggle
    document.getElementById("btnToggleOE")?.addEventListener("click", () => {
        currentOE = currentOE ? 0 : 1;
        const btn = document.getElementById("btnToggleOE");
        btn.innerText = `OUTPUT ENABLE (OE = ${currentOE})`;
        btn.className = currentOE ? "px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-semibold" : "px-4 py-2 bg-slate-800 text-slate-400 rounded font-semibold";
        stepRegisterAPI(currentClk);
    });

    // Run Test Suite Button
    document.getElementById("btnRunTests")?.addEventListener("click", runTestSuite);

    // Buffer Step Write
    document.getElementById("btnBufWrite")?.addEventListener("click", async () => {
        const inputVal = parseInt(document.getElementById("bufWriteValue").value) || 0;
        await stepBufferAPI(1, 0, inputVal, 1);
    });

    // Buffer Step Read
    document.getElementById("btnBufRead")?.addEventListener("click", async () => {
        await stepBufferAPI(0, 1, null, 1);
    });

    // Buffer Reset
    document.getElementById("btnBufReset")?.addEventListener("click", async () => {
        await fetch("/api/buffer/reset", { method: "POST" });
        stepBufferAPI(0, 0, null, 0);
    });
}

async function stepRegisterAPI(clkVal) {
    currentClk = clkVal;
    try {
        const response = await fetch("/api/register/step", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                clk: currentClk,
                d_bus: dBusBits,
                load: currentLoad,
                reset_n: currentResetN,
                oe: currentOE,
                bit_width: currentBitWidth
            })
        });
        const data = await response.json();
        updateCircuitVisualizer(data.register_state);
        
        // Push to waveform history
        waveformHistory.push({
            clk: currentClk,
            load: currentLoad,
            reset_n: currentResetN,
            oe: currentOE,
            d_int: data.step.d_bus_int,
            q_int: data.step.q_int,
            q_bus: data.step.q_bus_output
        });
        if (waveformHistory.length > 30) waveformHistory.shift();
        renderWaveforms();

    } catch (err) {
        console.error("API Error:", err);
    }
}

async function stepBufferAPI(wEn, rEn, wWord, rstN) {
    try {
        const response = await fetch("/api/buffer/step", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                write_enable: wEn,
                read_enable: rEn,
                write_word: wWord,
                reset_n: rstN
            })
        });
        const data = await response.json();
        updateBufferUI(data);
    } catch (err) {
        console.error("Buffer API Error:", err);
    }
}

function updateBufferUI(data) {
    const summary = data.summary;
    document.getElementById("statThroughput").innerText = `${summary.throughput_words_per_cycle} W/cycle`;
    document.getElementById("statBandwidth").innerText = `${summary.bandwidth_mbps} Mbps`;
    document.getElementById("statEfficiency").innerText = `${summary.bandwidth_efficiency_pct}%`;
    document.getElementById("statLatency").innerText = `${summary.avg_latency_cycles} cycles`;
    document.getElementById("statOccupancy").innerText = `${summary.words_written - summary.words_read} / ${summary.buffer_depth}`;

    // Render Pipeline Slots
    const container = document.getElementById("bufferSlotsContainer");
    if (!container) return;
    container.innerHTML = "";
    
    const contents = data.step.buffer_contents;
    contents.forEach((val, idx) => {
        const slot = document.createElement("div");
        slot.className = `p-3 rounded-lg border text-center transition ${
            val !== null ? "bg-cyan-950/60 border-cyan-500 text-cyan-300 shadow-md shadow-cyan-500/20" : "bg-slate-900 border-slate-800 text-slate-600"
        }`;
        slot.innerHTML = `
            <div class="text-[10px] uppercase font-bold tracking-wider text-slate-500">Stage ${idx}</div>
            <div class="text-base font-mono font-bold mt-1">${val !== null ? '0x' + val.toString(16).toUpperCase().padStart(2, '0') : 'EMPTY'}</div>
        `;
        container.appendChild(slot);
    });

    const statusLog = document.getElementById("bufferStatusLog");
    if (statusLog) {
        statusLog.innerText = `Cycle ${data.step.cycle}: ${data.step.status}`;
    }
}

function updateCircuitVisualizer(state = null) {
    const container = document.getElementById("circuitGridContainer");
    if (!container) return;
    container.innerHTML = "";
    
    const bitsToShow = Math.min(currentBitWidth, 8); // Render up to 8 interactive flip-flops visually
    const qBits = state ? state.q_bits : Array(currentBitWidth).fill(0);
    const busOutput = state ? state.bus_output : Array(currentBitWidth).fill(0);

    for (let i = bitsToShow - 1; i >= 0; i--) {
        const qVal = qBits[i] || 0;
        const dVal = dBusBits[i] || 0;
        const isHiZ = (busOutput === null);
        
        const card = document.createElement("div");
        card.className = `flipflop-box ${currentClk ? 'active-clk' : ''}`;
        card.innerHTML = `
            <div class="flex justify-between items-center text-xs text-slate-400 mb-2 border-b border-slate-800 pb-1 font-mono">
                <span>FF_${i}</span>
                <span class="led-indicator ${isHiZ ? 'led-hiz' : (qVal ? 'led-high' : 'led-low')}"></span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-left text-xs font-mono">
                <div>D: <span class="text-cyan-400 font-bold">${dVal}</span></div>
                <div>Q: <span class="text-emerald-400 font-bold">${isHiZ ? 'Z' : qVal}</span></div>
                <div>CLK: <span class="${currentClk ? 'text-green-400' : 'text-slate-500'}">${currentClk}</span></div>
                <div>RST: <span class="text-slate-300">${currentResetN}</span></div>
            </div>
        `;
        container.appendChild(card);
    }

    // Hex summary
    const hexVal = qBits.reduce((acc, b, idx) => acc + (b << idx), 0);
    document.getElementById("outputHexDisplay").innerText = busOutput === null ? "Hi-Z (Disabled)" : `0x${hexVal.toString(16).toUpperCase().padStart(Math.ceil(currentBitWidth / 4), '0')}`;
}

// Waveform Canvas Rendering
function renderWaveforms() {
    const canvas = document.getElementById("waveformCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 220;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, width, height);

    if (waveformHistory.length === 0) {
        ctx.fillStyle = "#64748b";
        ctx.font = "14px Inter";
        ctx.fillText("Clock the register to view live signal waveforms...", 20, 110);
        return;
    }

    const signals = [
        { name: "CLK", key: "clk", color: "#22c55e", type: "digital" },
        { name: "LOAD", key: "load", color: "#38bdf8", type: "digital" },
        { name: "RST_N", key: "reset_n", color: "#ef4444", type: "digital" },
        { name: "D_BUS", key: "d_int", color: "#a855f7", type: "bus" },
        { name: "Q_BUS", key: "q_int", color: "#eab308", type: "bus" }
    ];

    const stepWidth = Math.max(25, width / Math.max(30, waveformHistory.length));
    const rowHeight = height / signals.length;

    signals.forEach((sig, sIdx) => {
        const yBase = sIdx * rowHeight + rowHeight * 0.75;
        const yHigh = sIdx * rowHeight + rowHeight * 0.25;

        // Label
        ctx.fillStyle = sig.color;
        ctx.font = "bold 11px Fira Code";
        ctx.fillText(sig.name, 10, yBase - 5);

        ctx.strokeStyle = sig.color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        waveformHistory.forEach((pt, pIdx) => {
            const x = 70 + pIdx * stepWidth;
            const val = pt[sig.key];

            if (sig.type === "digital") {
                const y = val ? yHigh : yBase;
                if (pIdx === 0) {
                    ctx.moveTo(x, y);
                } else {
                    const prevY = waveformHistory[pIdx - 1][sig.key] ? yHigh : yBase;
                    ctx.lineTo(x, prevY);
                    ctx.lineTo(x, y);
                }
                ctx.lineTo(x + stepWidth, y);
            } else {
                // Bus rendering (Hex boxes)
                ctx.fillStyle = "rgba(255,255,255,0.05)";
                ctx.fillRect(x, yHigh, stepWidth - 2, rowHeight * 0.5);
                ctx.strokeStyle = sig.color;
                ctx.strokeRect(x, yHigh, stepWidth - 2, rowHeight * 0.5);
                
                ctx.fillStyle = "#f8fafc";
                ctx.font = "10px Fira Code";
                const hexStr = val === null ? "Z" : '0x' + val.toString(16).toUpperCase();
                ctx.fillText(hexStr, x + 4, yBase - 4);
            }
        });
        if (sig.type === "digital") ctx.stroke();
    });
}

// Load Truth Table
async function loadTruthTable() {
    try {
        const response = await fetch(`/api/register/truth_table?bit_width=${currentBitWidth}`);
        const data = await response.json();
        const tbody = document.getElementById("truthTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-slate-800 hover:bg-slate-800/40 text-xs font-mono";
            tr.innerHTML = `
                <td class="px-3 py-2 text-cyan-400 font-bold">${row.CLK}</td>
                <td class="px-3 py-2 text-rose-400">${row.RST_N}</td>
                <td class="px-3 py-2 text-indigo-400">${row.LOAD}</td>
                <td class="px-3 py-2 text-amber-400">${row.OE}</td>
                <td class="px-3 py-2 text-slate-300">${row.D_In}</td>
                <td class="px-3 py-2 text-emerald-400 font-bold">${row["Q(t+1)"]}</td>
                <td class="px-3 py-2 text-slate-400">${row["Output Bus"]}</td>
                <td class="px-3 py-2 text-slate-200 font-sans font-semibold">${row.Operation}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Truth Table Error:", err);
    }
}

// Automated Test Suite Runner
async function runTestSuite() {
    const btn = document.getElementById("btnRunTests");
    btn.innerText = "Executing 15 Tests...";
    btn.disabled = true;

    try {
        const response = await fetch("/api/tests/run");
        const data = await response.json();

        document.getElementById("testSummaryCount").innerText = `${data.passed} / ${data.total} PASSED`;
        const tbody = document.getElementById("testResultsBody");
        tbody.innerHTML = "";

        data.results.forEach(tc => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-slate-800 hover:bg-slate-800/50 text-xs";
            const isPass = tc.Status === "PASS";
            tr.innerHTML = `
                <td class="px-4 py-3 font-mono font-bold text-cyan-400">${tc.TC_ID}</td>
                <td class="px-4 py-3 font-semibold text-slate-200">${tc["Test Name"]}</td>
                <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${tc.Category === 'Normal' ? 'bg-indigo-950 text-indigo-300 border border-indigo-700' : 'bg-amber-950 text-amber-300 border border-amber-700'}">${tc.Category}</span></td>
                <td class="px-4 py-3"><span class="px-2 py-0.5 rounded font-bold text-[11px] ${isPass ? 'bg-emerald-950 text-emerald-400 border border-emerald-700' : 'bg-rose-950 text-rose-400 border border-rose-700'}">${tc.Status}</span></td>
                <td class="px-4 py-3 font-mono text-slate-400">${tc["Truth Table Operation"]}</td>
                <td class="px-4 py-3 text-slate-300">${tc.Details}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Test Suite Error:", err);
    } finally {
        btn.innerText = "Run All 15 Test Cases";
        btn.disabled = false;
    }
}

// AI Analytics & Traffic
async function loadAITraffic() {
    try {
        const response = await fetch("/api/ai/traffic?pattern=burst&noise=0.15");
        const data = await response.json();
        renderAIChart(data.traffic_data);
        
        const metrics = data.model_metrics;
        document.getElementById("aiMetricsBox").innerHTML = `
            <div class="grid grid-cols-2 gap-4 text-xs font-mono">
                <div>Training Samples: <span class="text-cyan-400 font-bold">${metrics.training_samples}</span></div>
                <div>Detected Anomalies: <span class="text-rose-400 font-bold">${metrics.detected_anomalies}</span></div>
            </div>
            <div class="mt-3 text-xs text-slate-400 font-sans">
                Top Anomaly Drivers: <span class="text-amber-300 font-mono">Setup Time (37%), Hold Time (38%), Temp (18%)</span>
            </div>
        `;
    } catch (err) {
        console.error("AI Error:", err);
    }
}

function renderAIChart(traffic) {
    const ctx = document.getElementById("aiChartCanvas")?.getContext("2d");
    if (!ctx) return;

    if (aiChartInstance) aiChartInstance.destroy();

    const cycles = traffic.map(t => t.cycle);
    const setupTimes = traffic.map(t => t.setup_time_ps);
    const anomalies = traffic.map(t => t.is_anomaly ? 1200 : null);

    aiChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: cycles,
            datasets: [
                {
                    label: 'Setup Time (ps)',
                    data: setupTimes,
                    borderColor: '#38bdf8',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'Anomaly Detected',
                    data: anomalies,
                    backgroundColor: '#ef4444',
                    borderColor: '#ef4444',
                    pointRadius: 5,
                    showLine: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' }, title: { display: true, text: 'Time (ps)', color: '#94a3b8' } }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });
}

function initAICounts() {
    document.getElementById("btnPredictFault")?.addEventListener("click", async () => {
        const setupPs = parseFloat(document.getElementById("aiSetupPs").value) || 1000.0;
        const holdPs = parseFloat(document.getElementById("aiHoldPs").value) || 500.0;
        
        const res = await fetch("/api/ai/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ setup_time_ps: setupPs, hold_time_ps: holdPs })
        });
        const data = await res.json();
        
        const box = document.getElementById("aiPredictResult");
        box.className = `p-3 rounded border text-xs font-mono ${data.is_anomaly ? 'bg-rose-950/60 border-rose-600 text-rose-300' : 'bg-emerald-950/60 border-emerald-600 text-emerald-300'}`;
        box.innerHTML = `<strong>Status:</strong> ${data.status} | <strong>Fault Type:</strong> ${data.predicted_fault_type} | <strong>Score:</strong> ${data.anomaly_score}`;
    });
}
