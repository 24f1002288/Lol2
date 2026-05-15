from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from math import ceil

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def percentile(values, q):
    values = sorted(values)
    if not values:
        return None
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] + frac * (values[hi] - values[lo])

@app.get("/")
async def health():
    return {"ok": True, "email": "24f1002288@ds.study.iitm.ac.in"}

@app.post("/")
@app.post("/api/latency")
async def latency_stats(request: Request):
    body = await request.json()
    wanted_regions = body.get("regions", [])
    threshold_ms = float(body.get("threshold_ms", 0))

    data_path = Path("q-vercel-latency.json")
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

    with data_path.open(encoding="utf-8") as f:
        rows = json.load(f)

    output = []
    for region in wanted_regions:
        region_rows = [row for row in rows if row.get("region") == region]
        latencies = [float(row["latency_ms"]) for row in region_rows]
        uptimes = [float(row["uptime_pct"]) for row in region_rows]
        breaches = sum(1 for value in latencies if value > threshold_ms)
        output.append({
            "region": region,
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(percentile(latencies, 0.95), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": breaches,
        })

    return {"regions": output}
