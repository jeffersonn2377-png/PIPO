"""
FastAPI Backend Application for PIPO Data Buffer Simulator Website
Provides REST API endpoints and serves the interactive single-page web app.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from pipo_register import PIPORegister
from buffer_simulator import PIPODataBuffer
from ai_analytics import SyntheticTrafficGenerator, AIFaultDetector
from test_suite import PIPOTestSuite

app = FastAPI(title="PIPO Data Buffer Simulator", version="1.0.0")

# Mount static and template directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global Simulator State Instances
register_instance = PIPORegister(bit_width=8)
buffer_instance = PIPODataBuffer(depth=8, bit_width=8, clk_freq_mhz=100.0)
ai_detector = AIFaultDetector()


@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/register/state")
async def get_register_state():
    return register_instance.get_state()


@app.post("/api/register/step")
async def step_register(payload: dict):
    global register_instance
    clk = int(payload.get("clk", 0))
    d_bus = payload.get("d_bus", [0]*register_instance.bit_width)
    load = int(payload.get("load", 1))
    reset_n = int(payload.get("reset_n", 1))
    oe = int(payload.get("oe", 1))
    bit_width = int(payload.get("bit_width", register_instance.bit_width))
    time_ns = float(payload.get("time_ns", 0.0))

    if register_instance.bit_width != bit_width:
        register_instance = PIPORegister(bit_width=bit_width)

    step_rec = register_instance.clock_step(
        clk=clk, d_bus=d_bus, load=load, reset_n=reset_n, oe=oe, current_time=time_ns
    )
    return {
        "step": step_rec,
        "register_state": register_instance.get_state(),
        "history": register_instance.history[-20:]
    }


@app.get("/api/register/truth_table")
async def get_truth_table(bit_width: int = 4):
    df_tt = PIPORegister.generate_truth_table(bit_width=bit_width)
    return df_tt.to_dict(orient="records")


@app.post("/api/buffer/step")
async def step_buffer(payload: dict):
    write_enable = int(payload.get("write_enable", 0))
    read_enable = int(payload.get("read_enable", 0))
    write_word = payload.get("write_word", None)
    if write_word is not None:
        write_word = int(write_word)
    reset_n = int(payload.get("reset_n", 1))

    step_rec = buffer_instance.step_clock(
        write_enable=write_enable, read_enable=read_enable, write_word=write_word, reset_n=reset_n
    )
    summary = buffer_instance.get_performance_summary()
    return {
        "step": step_rec,
        "summary": summary,
        "history": buffer_instance.history[-20:]
    }


@app.post("/api/buffer/reset")
async def reset_buffer():
    buffer_instance.step_clock(reset_n=0)
    buffer_instance.total_clock_cycles = 0
    buffer_instance.total_words_written = 0
    buffer_instance.total_words_read = 0
    buffer_instance.overflow_events = 0
    buffer_instance.underflow_events = 0
    buffer_instance.latencies.clear()
    buffer_instance.history.clear()
    return {"status": "Buffer reset successfully"}


@app.get("/api/tests/run")
async def run_test_suite():
    runner = PIPOTestSuite()
    df_res = runner.run_all_tests()
    records = df_res.to_dict(orient="records")
    passed = int((df_res["Status"] == "PASS").sum())
    total = len(df_res)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "results": records
    }


@app.get("/api/ai/traffic")
async def get_ai_traffic(pattern: str = "burst", noise: float = 0.1):
    df_traffic = SyntheticTrafficGenerator.generate_workload(
        num_samples=100, pattern_type=pattern, noise_prob=noise
    )
    train_res = ai_detector.train(df_traffic)
    return {
        "traffic_data": df_traffic.to_dict(orient="records"),
        "model_metrics": train_res
    }


@app.post("/api/ai/predict")
async def predict_fault(payload: dict):
    res = ai_detector.predict_sample(payload)
    return res


@app.get("/api/download/dataset/{name}")
async def download_dataset(name: str):
    file_map = {
        "normal": os.path.join("data", "pipo_normal_traffic.csv"),
        "fault": os.path.join("data", "pipo_fault_traffic.csv")
    }
    target = file_map.get(name)
    if target and os.path.exists(target):
        return FileResponse(target, filename=f"pipo_{name}_traffic.csv", media_type="text/csv")
    return JSONResponse(status_code=404, content={"error": "File not found"})


if __name__ == "__main__":
    import uvicorn
    print("Starting PIPO Data Buffer Simulator Web Application on http://localhost:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
