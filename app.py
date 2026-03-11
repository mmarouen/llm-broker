import requests
import google.auth
import google.auth.transport.requests
import time
import os
import uvicorn
import yaml
import json
import sys
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from src import upload_results, get_gcp_endpoint_paths, run_stress_test, LISO_PROMPTS

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

with open(os.path.join('config', 'config.yaml'), 'r') as file:
    config = yaml.safe_load(file)
with open(os.path.join('config', '.env.yaml'), 'r') as file:
    project = yaml.safe_load(file)['project']

PROJECT_ID = project['id']
PROJECT_NR=project['number']
REGION = project['region']
GCP_MODEL = 'llama-3.2-vllm'
CLAUDE_MODEL = 'claude-sonnet-4-6'
endpoint = config['models'][GCP_MODEL]['endpoint']
storage = config['models'][GCP_MODEL]['storage']
STREAM = False
TRACE = True
GCP_INSTANCE = True

STAGES = [
    (1, 30),   # Baseline
    (2, 30),   # Low Load
    (5, 60),  # Medium Load
    (10, 60),  # Heavy Stress
    (20, 120),
    (40, 240),
]

#STAGES = [
#    (1, 8)   # Baseline
#]

app = FastAPI()

class StressRequest(BaseModel):
    node: str = "gcp_endpoint"
    stream: bool = False
    trace: bool = True

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/run_test")
def run_test(req: StressRequest):
    session = requests.Session()
    url = None
    if req.node == "gcp_endpoint":
        MODEL = GCP_MODEL
        url = get_gcp_endpoint_paths(endpoint, PROJECT_NR, REGION, PROJECT_ID)
        credentials, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        
        session.headers.update({
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        })
    elif req.node == "claude":
        MODEL = CLAUDE_MODEL
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        session.headers.update({
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        })
        url = "https://api.anthropic.com/v1/messages"
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        session.headers.update({
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        })


    results = []
    for concurrency, duration in STAGES:
        logging.info(f"\n--- Stage: {concurrency} users for {duration}s ---")
        stop_time = time.time() + duration
        stage_result = None
        stage_result = run_stress_test(
                stop_time=stop_time,
                concurrency=concurrency,
                duration=duration,
                prompt_bank=LISO_PROMPTS,
                stream=STREAM,
                session=session,
                url=url,
                model=MODEL,
                backend=req.node)
        record = {
            "model_name": MODEL,
            "node": req.node,
            "concurrency": concurrency,
            "duration": duration,
            "metrics": stage_result.model_dump()
        }

        logging.info(f"Stress test log {json.dumps(record)}")
        results.append(record)
    upload_results(results=results, gs_bucket=storage['bucket'])
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)